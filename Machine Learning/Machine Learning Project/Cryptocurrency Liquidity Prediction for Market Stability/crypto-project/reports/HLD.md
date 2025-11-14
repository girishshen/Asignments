# High Level Design (HLD)
## Cryptocurrency Liquidity Prediction System

---

## 1. Introduction
This High-Level Design (HLD) document describes the architecture, components, data flow, and functional overview of the **Cryptocurrency Liquidity Prediction System**, whose goal is to estimate short-term **liquidity_score** for crypto assets using historical market data.

The prediction system will help identify potential **liquidity stress**, enabling early warning signals for risk monitoring or analytical insights.

---

## 2. System Objectives
The system aims to:

- Predict **liquidity_score** using market data.
- Provide a user-friendly **Streamlit UI** for predictions.
- Support **single input**, **batch input**, and **auto-fill** modes.
- Maintain **prediction history** and **PDF reports**.
- Offer **dark mode**, **help toggle**, and **real-time visualization**.
- Enable simple deployment and offline usage (no external API dependency).

---

## 3. Architecture Overview (High Level)

The system uses a modular layered architecture:

### 🔹 **Layer 1 — Data Layer**
Handles:
- Dataset ingestion (CSV)
- Data cleaning and validation
- Processed dataset storage

### 🔹 **Layer 2 — Feature Engineering Layer**
Extracts and prepares **8 numerical features** used for training:
- price  
- 1h  
- 24h  
- 7d  
- 24h_volume  
- mkt_cap  
- liquidity_ratio  
- price_change_24h  

Other engineered features may exist but are **not used** by the final model.

### 🔹 **Layer 3 — Model Training Layer**
Trains and evaluates several models:
- Linear Regression (FINAL SELECTED MODEL)
- Random Forest
- Gradient Boosting
- KNN
- SVR
- XGBoost  

Final model saved as: /models/Linear_Regression.pkl


### 🔹 **Layer 4 — Deployment Layer (Streamlit App)**
Provides:
- Single prediction
- Auto-fill using processed dataset
- Batch CSV/table prediction
- PDF generation
- Live charts
- Feature importance visualization
- Dark and light mode

### 🔹 **Layer 5 — Reporting & Logging Layer**
Outputs:
- Prediction history (CSV)
- PDF reports
- Logging for audit & debugging

---

## 4. Components & Responsibilities

### 4.1 Data Ingestion Component
**Inputs:**
- Raw market dataset (CSV)

**Responsibilities:**
- Validate schema  
- Parse date fields  
- Remove or correct invalid values  
- Save processed data  

**Outputs:**  
`data/processed/engineered_features.csv`

---

### 4.2 Preprocessing Component
Handles:
- Handling missing data
- Casting numeric datatypes
- Range checks (e.g., price > 0, volume > 0)
- Filtering noisy rows
- Normalization (optional)

---

### 4.3 Feature Engineering Component
Creates:
- Basic numerical features  
- Liquidity-related ratios  
- Percentage changes  

Defines **final model input feature vector** of 8 features.

---

### 4.4 Model Training Component
**Model Selection Process:**
- Train/test split
- Evaluate regression metrics (RMSE, R²)
- Visualize results
- Pick best performing model (Linear Regression)

**Outputs:**  
`Linear_Regression.pkl`

---

### 4.5 Model Inference Component (Streamlit)
Key capabilities:

#### **Modes**
- **Single Input Mode:** User enters 8 numeric features manually.
- **Auto-Fill Mode:** Select coin → pre-filled values → user edits → predict.
- **Batch Mode:** Upload CSV or edit table → multi-row prediction.

#### **UI Enhancements**
- Dark Mode toggle  
- Help bubble toggle  
- Real-time price–liquidity simulation chart  
- Interactive feature importance chart  

---

### 4.6 Reporting Component
Outputs include:
- **PDF report** for every prediction  
- **CSV prediction history** (append mode)  
- Daily average liquidity charts  
- Logs of all predictions  

---

## 5. High-Level Data Flow


┌──────────────────────┐
│ Raw CSV (market data)│
└───────────┬──────────┘
            ▼
┌──────────────────────┐
│ Preprocessing │
└───────────┬──────────┘
            ▼
┌────────────────────────────┐
│ Feature Engineering (8 feats) │
└───────────┬────────────────┘
            ▼
┌────────────────────────────┐
│ Model Training (LinReg) │
└───────────┬────────────────┘
            │ Saved .pkl
            ▼
┌──────────────────────────────────────────┐
│ Streamlit App (UI) │
│ Single | Auto-fill | Batch │
└───────────┬────────────────────────────┘
            ▼
┌────────────────────────────┐
│ Reports & Logs (PDF, CSV) │
└────────────────────────────┘

---

## 6. Technology Stack
| Layer | Technology |
|-------|------------|
| Processing | Python, Pandas, NumPy |
| Modeling | scikit-learn |
| Deployment | Streamlit |
| Visualization | matplotlib |
| Reports | reportlab |
| Logging | Python logging |
| Storage | CSV, PKL |

---

## 7. Non-Functional Requirements

### **Performance**
- Prediction < 40ms
- Batch predictions scale linearly

### **Usability**
- Minimal inputs (only 8 features)
- Help toggle & dark mode

### **Reliability**
- Logging for every prediction
- History stored permanently

### **Portability**
- Runs locally via Streamlit
- No external API dependency

### **Security**
- Only local file read/write
- No external data transmission

---

## 8. Constraints & Limitations
- Very small dataset (only 2 days)
- No real liquidity indicators (order book depth missing)
- Linear model may oversimplify market dynamics
- No automated retraining pipeline

---

## 9. Future Enhancements
- API-based live data ingestion (CoinGecko / Binance)
- Time-series modeling (LSTM / Prophet)
- Integrate sentiment analysis
- Deploy to cloud (GCP/AWS)
- Add monitoring dashboards

---

## 10. Conclusion
This HLD describes a modular, maintainable, and lightweight system for predicting cryptocurrency liquidity_score. The final architecture integrates data preparation, modeling, a user-friendly UI, and reporting, forming a complete end-to-end analytical tool suitable for experimentation and small-scale decision support.