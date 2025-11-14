# Pipeline Architecture — Cryptocurrency Liquidity Prediction System (Full)

## Overview
This document describes the full pipeline architecture for the Cryptocurrency Liquidity Prediction system. It covers:

- End-to-end data pipeline (ingest → preprocess → feature engineering → training → evaluation → deployment)
- CI/CD for model and app
- Monitoring, alerting, and rollback strategies
- Data contracts, schema specs, and sample commands
- Infrastructure, security considerations, and scaling guidance
- Example diagrams (ASCII) and GitHub Actions snippets
- Docker & deployment examples

This is a comprehensive guide intended for engineering teams to implement, operate, and extend the pipeline.

---

## 1. High-Level Pipeline (Stages)

1. **Data Ingestion**
   - Sources: CSVs (batch), CoinGecko API (optional), internal feeds
   - Tasks: collect, validate, store raw files in `data/raw/`

2. **Data Validation & Preprocessing**
   - Parse dates, cast types, handle missing values, emit `data_validation_report.json`
   - Save cleaned data to `data/cleaned/`

3. **Feature Engineering**
   - Compute rolling stats, liquidity proxies, volatility measures
   - Save engineered dataset to `data/processed/engineered_features.csv`

4. **Label Construction**
   - Compute `liquidity_score` (regression target)
   - Save labeled dataset to `data/processed/labels.parquet` (or CSV)

5. **Model Training & Evaluation**
   - Train candidate models (Linear Regression, RandomForest, XGBoost)
   - Time-series aware evaluation (rolling origin CV)
   - Save best model to `models/` with metadata

6. **Model Packaging**
   - Save model artifact (`.pkl` via joblib) and metadata (`models/metadata.json`)
   - Build a container (Docker) for the inference app or model service

7. **Deployment**
   - Option A: Streamlit app with model artifact loaded locally
   - Option B: Model microservice (FastAPI) -> Streamlit as UI client
   - Deploy via Docker or cloud (ECS, GKE, Cloud Run)

8. **Monitoring & Reporting**
   - Logs: predictions, errors, data validation reports
   - Metrics: prediction distribution, daily averages, ML metrics on holdout
   - Alerts: missing data, model load failures, data drift detection

---

## 2. Directory & Artifact Layout

```
project-root/
├─ data/
│  ├─ raw/
│  ├─ cleaned/
│  └─ processed/
│     └─ engineered_features.csv
├─ models/
│  ├─ Linear_Regression.pkl
│  └─ metadata.json
├─ src/
│  ├─ ingest.py
│  ├─ validate.py
│  ├─ preprocess.py
│  ├─ features.py
│  ├─ labels.py
│  ├─ train.py
│  └─ predict.py
├─ app/
│  └─ app.py
├─ tests/
├─ reports/
├─ logs/
├─ Dockerfile
├─ Makefile
└─ .github/workflows/
```

---

## 3. Data Contracts & Schemas

### 3.1 Raw CSV Contract (minimum)
Columns (required):
- `coin` (string)
- `symbol` (string)
- `price` (float)
- `1h` (float) - % change over 1 hour
- `24h` (float) - % change over 24 hours
- `7d` (float) - % change over 7 days
- `24h_volume` (float)
- `mkt_cap` (float)
- `date` (string/date)
- `liquidity_ratio` (float)
- `price_change_24h` (float)

### 3.2 Processed/Engineered Schema (example)
```
coin, symbol, date, price, 1h, 24h, 7d, 24h_volume, mkt_cap,
liquidity_ratio, price_change_24h, liquidity_score, price_log, price_sqrt, mkt_cap_log, ...
```

### 3.3 Prediction API contract (if using a model service)
**Request (JSON):**
```json
{
  "price": 31245.77,
  "1h": 0.12,
  "24h": 1.89,
  "7d": 4.55,
  "24h_volume": 18522441552.0,
  "mkt_cap": 612884112554.0,
  "liquidity_ratio": 0.0302,
  "price_change_24h": 12.2578
}
```

**Response (JSON):**
```json
{
  "liquidity_score": 0.0228,
  "model": "Linear_Regression",
  "model_version": "2025-11-14_v1",
  "timestamp": "2025-11-14T15:38:10Z"
}
```

---

## 4. Detailed Stage Implementations

### 4.1 Data Ingestion
- **Batch ingestion**: place CSV files in `data/raw/` with consistent naming convention `coingecko_YYYYMMDD.csv`.
- **Automated ingestion script**:
  - `src/ingest.py` reads the folder, validates filenames, and copies new files to an archive.
  - Example usage:
    ```bash
    python src/ingest.py --input-dir data/raw --archive-dir data/archive
    ```
- **Validation**: call `src/validate.py` to produce `data_validation_report.json`.

### 4.2 Validation & Preprocessing
- `src/validate.py` checks schema; outputs:
  ```json
  {
    "file": "coingecko_20221101.csv",
    "rows": 1200,
    "min_date": "2022-10-01",
    "max_date": "2022-10-31",
    "issues": []
  }
  ```
- `src/preprocess.py`:
  - cast types
  - impute missing values (ffill/bfill grouped by coin)
  - drop rows with critical missing fields
  - write cleaned CSV to `data/cleaned/`

### 4.3 Feature Engineering
- `src/features.py` computes:
  - `liquidity_ratio = 24h_volume / mkt_cap`
  - basic logs and sqrt transforms for price and mkt_cap
  - rolling means (if time window exists), e.g., `price_ma_7d`
- Save engineered features to `data/processed/engineered_features.csv`

### 4.4 Label Construction
- `src/labels.py` constructs `liquidity_score`:
  - define formula (must be identical to the one used during training)
  - store scaling params to `models/scaler.json` (if scaler was used)

### 4.5 Training
- `src/train.py`:
  - reads engineered dataset
  - splits data using time-aware split
  - trains models and logs metrics to `reports/metrics.json`
  - pickles best model to `models/`

### 4.6 Packaging & Containerization
- `Dockerfile` example:
  ```dockerfile
  FROM python:3.10-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
  ```

---

## 5. CI/CD (GitHub Actions) — Example Workflow

`.github/workflows/ci-cd.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: pytest -q

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: |
          docker build -t myrepo/crypto-liquidity:latest .
      - name: Push image
        uses: docker/build-push-action@v4
        with:
          push: true
          tags: myrepo/crypto-liquidity:latest
```

---

## 6. Monitoring & Alerting

### 6.1 Logs
- Centralized logs (local file) in `logs/app.log`
- Log entries:
  - Model load events
  - Prediction events (mode, sample inputs, prediction)
  - Exceptions with tracebacks

### 6.2 Metrics & Dashboards
- Basic metrics to track:
  - Daily avg predicted liquidity score
  - Number of predictions per day
  - Distribution (histogram) of predictions
  - Mean Absolute Prediction per coin (on holdout)
- Push metrics to a lightweight store (Prometheus/Grafana) if scaling or use CSV + scheduled reporting.

### 6.3 Alerts
- Email or Slack alerts when:
  - Data validation fails (missing critical fields)
  - Model file missing or corrupted
  - Number of predictions drops to zero (indicates outage)

---

## 7. Rollback & Versioning

### 7.1 Model Versioning
- `models/metadata.json` includes:
```json
{
  "model_name": "Linear_Regression",
  "version": "2025-11-14_v1",
  "trained_on": "2025-11-14",
  "features": [...],
  "metrics": {...}
}
```

### 7.2 Rollback Strategy
- Keep last 3 model artifacts: `Linear_Regression_v1.pkl, v2.pkl, v3.pkl`
- On failure, replace symlink `models/current.pkl` to previous version and restart service.

---

## 8. Security & Compliance

- Do not store sensitive PII (none expected).
- Limit file read/write permissions to the application user.
- If deployed to cloud, store model artifacts in a protected bucket and use IAM.
- Use HTTPS for any externally exposed endpoints.

---

## 9. Scaling & Performance Guidance

- Linear Regression inference is cheap — serve within the same container for low throughput.
- For >100 RPS, separate model into microservice with Uvicorn/Gunicorn and autoscaling.
- Use batching for bulk predictions for speed-ups.

---

## 10. Example Commands & Utilities

- Run ingestion
```bash
python src/ingest.py --input data/raw --out data/cleaned
```

- Preprocess
```bash
python src/preprocess.py --input data/cleaned --out data/processed
```

- Train
```bash
python src/train.py --data data/processed/engineered_features.csv --out-model models/Linear_Regression.pkl
```

- Run app locally
```bash
streamlit run app/app.py
```

- Build Docker image
```bash
docker build -t crypto-liquidity:latest .
```

---

## 11. Diagrams

### 11.1 ASCII Sequence Diagram (Training & Deploy)
```
User/Engineer -> Ingest Script: upload raw CSV
Ingest Script -> Preprocess: validate & clean
Preprocess -> Features: compute features
Features -> Train: create datasets
Train -> Model Store: save best model
Model Store -> Deploy: containerize + publish
Deploy -> Streamlit: app loads model for inference
```

### 11.2 ASCII Component Diagram
```
[RAW DATA] --> [INGEST] --> [CLEAN] --> [FEATURES] --> [TRAIN] --> [MODEL STORE]
                                                      |
                                                      v
                                                  [DEPLOY]
                                                    |
                                                    v
                                               [STREAMLIT APP]
                                                    |
                                                    v
                                              [REPORTS / LOGS]
```

---

## 12. Appendix — GitHub Actions: Deploy to Cloud Run (optional)

Add a job to `ci-cd.yml` to push to Google Cloud Run (requires service account secrets):

```yaml
deploy-cloud-run:
  runs-on: ubuntu-latest
  needs: build-and-push
  steps:
    - uses: actions/checkout@v4
    - name: Authenticate to GCP
      uses: google-github-actions/auth@v1
      with:
        credentials_json: ${{ secrets.GCP_SA_KEY }}
    - name: Set GCP project
      run: gcloud config set project ${{ secrets.GCP_PROJECT }}
    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy crypto-liquidity \
          --image gcr.io/${{ secrets.GCP_PROJECT }}/crypto-liquidity:latest \
          --region us-central1 \
          --platform managed \
          --allow-unauthenticated
```

---

## 13. Final Notes
This pipeline architecture is robust for local and small-scale production usage. It emphasizes reproducibility, logging, and simple deployment. For enterprise production, integrate with managed services for storage (S3/GCS), orchestration (Airflow), monitoring (Prometheus/Grafana), and secrets management.