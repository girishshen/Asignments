# Low-Level Design (LLD) — Cryptocurrency Liquidity Prediction System

## Purpose
This Low-Level Design document provides a detailed, implementable specification for each module, function signatures, data formats, error handling, unit tests, and deployment steps for the Cryptocurrency Liquidity Prediction system.

It maps directly to the HLD and is intended to be used by developers implementing or extending the project.

---

## Repository Layout (recommended)
```
project-root/
├─ app/
│  ├─ app.py                # Streamlit app (inference UI)
│  ├─ streamlit_utils.py    # UI helper functions (optional)
├─ data/
│  ├─ raw/
│  ├─ processed/
│  │  └─ engineered_features.csv
├─ models/
│  └─ Linear_Regression.pkl
├─ notebooks/
│  ├─ notebook_01_eda.ipynb
│  ├─ notebook_02_fe.ipynb
│  └─ notebook_03_modeling.ipynb
├─ src/
│  ├─ data_ingest.py
│  ├─ preprocessing.py
│  ├─ features.py
│  ├─ labels.py
│  ├─ train.py
│  └─ predict.py
├─ reports/
│  └─ prediction_history.csv
├─ logs/
│  └─ app.log
├─ tests/
│  └─ test_preprocessing.py
├─ requirements.txt
└─ README.md
```

---

## Module: data_ingest.py
**Responsibility:** Load raw CSV files, validate headers, parse dates, produce a single standardized DataFrame and write `data/processed/engineered_features.csv` (after feature engineering).

### Public functions
- `def load_csv(filepath: str) -> pd.DataFrame`
  - Read CSV into pandas DataFrame with `parse_dates` for date columns.
  - Raise `FileNotFoundError` if missing.
- `def validate_schema(df: pd.DataFrame, expected_cols: List[str]) -> Tuple[bool, List[str]]`
  - Return `(True, [])` if schema OK; otherwise `(False, missing_cols)`.
- `def find_date_range(df: pd.DataFrame, date_col: str='date') -> Tuple[pd.Timestamp, pd.Timestamp]`
  - Returns `(min_date, max_date)`.

### Implementation notes
- Use `pd.read_csv(..., parse_dates=['date'], dayfirst=False, infer_datetime_format=True)` and add robust parsing fallback: `pd.to_datetime(df['date'], errors='coerce', dayfirst=True)`.
- Log ingestion metadata (file size, rows, date range) to `logs/app.log`.

### Example
```python
from pathlib import Path
import pandas as pd
def load_csv(fp: str) -> pd.DataFrame:
    p = Path(fp)
    if not p.exists():
        raise FileNotFoundError(fp)
    df = pd.read_csv(fp, parse_dates=['date'], infer_datetime_format=True)
    return df
```

---

## Module: preprocessing.py
**Responsibility:** Clean types, handle missing values, filtering, create data validation report.

### Public functions
- `def cast_types(df: pd.DataFrame) -> pd.DataFrame`
  - Ensure numeric columns are numeric. Columns: `price, 1h, 24h, 7d, 24h_volume, mkt_cap, liquidity_ratio, price_change_24h, liquidity_score`
- `def handle_missing(df: pd.DataFrame) -> pd.DataFrame`
  - Rules:
    - For time-series numeric columns: forward-fill then back-fill per `coin`.
    - For non-time features or if > 30% missing: drop row and log.
- `def validate_dates_report(df: pd.DataFrame) -> dict`
  - Output JSON with min/max per file (if multiple files) and `mismatch` flag if content date range differs from filename.

### Error handling
- If critical columns are missing, raise `ValueError("Missing required columns: ...")`
- Write `data_validation_report.json` to disk (dict with keys: `file`, `min_date`, `max_date`, `rows`, `issues`).

### Example
```python
def cast_types(df):
    num_cols = ['price','1h','24h','7d','24h_volume','mkt_cap','liquidity_ratio','price_change_24h','liquidity_score']
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df
```

---

## Module: features.py
**Responsibility:** Compute and persist feature engineering steps. The system intentionally uses only the final 8 numeric features for prediction, but the module provides utilities to compute extra columns for analysis.

### Public functions
- `def generate_features(df: pd.DataFrame) -> pd.DataFrame`
  - Input: cleaned DataFrame with required columns.
  - Output: DataFrame with engineered columns and `liquidity_score` (if present).
  - Saves to `data/processed/engineered_features.csv`.
- `def compute_liquidity_ratio(df) -> pd.Series`
  - `24h_volume / mkt_cap` (safe divide).

### Notes
- Keep feature computations idempotent.
- If rolling features are computed, ensure sorted by `date` and grouped by `coin`.
- Persist metadata (feature calculation timestamp, version) to `reports/features_metadata.json`.

---

## Module: labels.py
**Responsibility:** Construct regression target (`liquidity_score`) and optional binary crisis label.

### Public functions
- `def compute_liquidity_score(df: pd.DataFrame) -> pd.Series`
  - Example formula (must match training): a composite of inverse Amihud and normalized volume/mkt cap:
    - `amihud = abs(return) / volume` (approx) — but since order book is absent, use proxy:
    - `liquidity_score = scale( (24h_volume / mkt_cap) * some_factor )`
  - Ensure deterministic scaling (store scaler parameters in `/models/` or `/reports/`).
- `def binary_crisis_label(df, percentile=5, horizon=1) -> pd.Series`
  - Returns 1 if `liquidity_score` below `percentile` within `horizon` days ahead.

---

## Module: train.py
**Responsibility:** Train models, run cross-validation (time-series aware), select and persist best model.

### Public functions
- `def train_and_evaluate(X_train, y_train, X_val, y_val, models: dict) -> dict`
  - `models` param is dict of instantiated sklearn-like estimators.
  - Use time-series split (rolling origin) or `TimeSeriesSplit`.
  - Compute metrics: RMSE, MAE, R2.
  - Persist results to `reports/metrics.json` and `reports/experiment_table.csv`.
  - Save best model via `joblib.dump(..., 'models/Linear_Regression.pkl')`.

### Hyperparameter tuning
- Default: basic grid for RandomForest, XGBoost (optional).
- If using Optuna, save study to `reports/optuna_study.json`.

### Example
```python
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import TimeSeriesSplit
def train_and_evaluate(X, y):
    tscv = TimeSeriesSplit(n_splits=3)
    model = LinearRegression()
    # fit on X_train; evaluate on X_val
    model.fit(X_train, y_train)
```

---

## Module: predict.py
**Responsibility:** Serve prediction logic decoupled from UI; guarantees same feature ordering and validation for model input.

### Public functions
- `def predict_from_dict(model, input_dict: dict) -> float`
  - Prepare DataFrame with correct columns and order, call `model.predict`, return scalar float.
- `def predict_batch(model, df: pd.DataFrame) -> np.ndarray`
  - Accepts DataFrame with numeric columns and returns predictions.

### Validation
- Ensure feature names match `model.feature_names_in_` if available. Provide helpful error if mismatch.

---

## Module: app.py (Streamlit)
**Responsibility:** UI that uses `predict.py` and other helpers.

### Key functions (inside app or imported)
- `load_model() -> estimator`
- `load_feature_template() -> pd.DataFrame`
- `prepare_model_df_from_ui_dict() -> pd.DataFrame`
- `save_history_csv()`
- `generate_pdf()`

### UX Flow
1. User inputs numeric values (or auto-fill).
2. UI constructs validated model input.
3. Calls `predict.predict_from_dict()` to obtain `liquidity_score`.
4. Displays result, saves history, optionally generate PDF.

---

## Data Schemas & Formats

### Expected input CSV format (batch)
Columns:
```
coin,symbol,price,1h,24h,7d,24h_volume,mkt_cap,date,liquidity_ratio,price_change_24h
```
- `date` - ISO format `YYYY-MM-DD` or `DD-MM-YYYY` supported.
- Numeric fields must be castable to floats.

### Processed engineered_features.csv (example)
Columns include:
```
coin,symbol,price,1h,24h,7d,24h_volume,mkt_cap,date,liquidity_ratio,price_change_24h,liquidity_score,...
```

### Prediction history CSV (stored at reports/prediction_history.csv)
Columns:
```
coin,symbol,price,1h,24h,7d,24h_volume,mkt_cap,date,liquidity_ratio,price_change_24h,prediction,mode,timestamp
```

---

## Logging and Monitoring

- Use Python `logging` configured at start of app:
  - Log level: INFO
  - Log file: `logs/app.log`
  - Log entries:
    - Model load success/failure
    - Prediction events (mode, inputs, prediction value)
    - Errors/exceptions with tracebacks

- Create periodic health-checks (cron) to ensure:
  - model file exists
  - processed data updated
  - log file growth monitored

---

## Unit Tests (tests/)
Provide unit tests for critical functions:

- `tests/test_data_ingest.py`
  - Test `load_csv` with a small sample CSV.
  - Test `validate_schema` returns expected missing columns.

- `tests/test_preprocessing.py`
  - Test `cast_types` and `handle_missing`.
  - Simulate a small df with NaNs and ensure ffill/bfill logic.

- `tests/test_features.py`
  - Test `compute_liquidity_ratio` correctness.

- `tests/test_predict.py`
  - Mock a simple model (e.g., lambda) and ensure `predict_from_dict` returns expected output.

Example test (pytest):
```python
def test_compute_liquidity_ratio():
    import pandas as pd
    df = pd.DataFrame({'24h_volume':[100,50],'mkt_cap':[1000, 200]})
    from src.features import compute_liquidity_ratio
    out = compute_liquidity_ratio(df)
    assert out.iloc[0] == 0.1
    assert out.iloc[1] == 0.25
```

---

## Validation & Error Reporting

- Each public function must validate inputs and raise meaningful exceptions.
- All exceptions should be logged with `logging.exception(...)`.
- When used by Streamlit UI, catch exceptions and show user-friendly messages via `st.error()`.

---

## CI/CD & Automation

- Use GitHub Actions for:
  - Linting (flake8)
  - Running unit tests (pytest)
  - Packaging artifacts (optionally create a wheel)
- Example workflow:
  - `on: [push, pull_request]`
  - Jobs:
    - setup-python
    - pip install -r requirements.txt
    - pytest

---

## Deployment

- Local: `streamlit run app/app.py`
- Docker: Provide `Dockerfile` that installs requirements and runs the Streamlit app.
- For production, wrap model and prediction logic into a REST API (FastAPI) behind a small frontend.

---

## Performance & Optimization

- Prediction is fast (linear model). Cache model with `@st.cache_resource`.
- For batch predictions, process in vectorized pandas operations.
- If scaling to heavier loads, use a separate model microservice with Gunicorn/Uvicorn.

---

## Versioning & Reproducibility

- Keep `requirements.txt` and optionally `environment.yml`.
- Save model with metadata: training_date, feature_list, metrics in `models/metadata.json`.
- Tag releases in Git for reproducibility.

---

## Appendix: Example Code Snippets

### prepare_model_df_from_ui_dict
```python
def prepare_model_df_from_ui_dict(d: dict) -> pd.DataFrame:
    row = {}
    for f in MODEL_FEATURES:
        v = d.get(f, 0.0)
        try:
            if v == "" or v is None:
                v = 0.0
            v = float(v)
        except Exception:
            v = 0.0
        row[f] = v
    df = pd.DataFrame([row])
    if all(name in df.columns for name in model_feature_names):
        df = df[model_feature_names]
    else:
        df = df[MODEL_FEATURES]
    return df
```

### predict_from_dict
```python
def predict_from_dict(model, input_dict):
    df = prepare_model_df_from_ui_dict(input_dict)
    preds = model.predict(df)
    return float(preds[0])
```

---

## Contacts & Ownership
- Owner: Project maintainer (add email)
- Repo: GitHub repository URL (add link)
- License: MIT (recommended)

---