# 🔮 Crypto Liquidity Prediction System

A machine-learning system that predicts **cryptocurrency liquidity_score** using market data such as price, volume, market cap, and volatility indicators. Includes a modern Streamlit app, documentation, and deploy-ready structure.

---

## 🚀 Features
- 🤖 **Linear Regression model** (best-performing)
- 🎛 **Modern Streamlit UI** (Light/Dark mode)
- 🔢 Single & Batch predictions
- 📄 Auto-generated PDF reports
- 📊 Feature importance & charts
- 🧠 Prediction history logging
- 🗃 Fully documented pipeline (HLD, LLD, Final Report)

---

## 🧠 Model Inputs
Model uses **8 numeric features**:

- `price`
- `1h`
- `24h`
- `7d`
- `24h_volume`
- `mkt_cap`
- `liquidity_ratio`
- `price_change_24h`

---

## 📁 Project Structure
crypto-project/
├── app/ # Streamlit app
├── data/ # Raw & processed data
├── models/ # Trained model
├── notebooks/ # EDA & Training
├── reports/ # HLD, LLD, Final Report
├── logs/ # Application logs
└── requirements.txt


---

## ▶️ How to Run

### 1️⃣ Install dependencies
python -m venv myvenv

.\myvenv\Scipts\activate

pip install -r requirements.txt

### 2️⃣ Run the Streamlit app
cd app
streamlit run app.py


### 📚 Documentation
 - Found in /reports:
    HLD.md
    LLD.md
    pipeline_architecture.md
    final_report.md