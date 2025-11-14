# app/app.py
import streamlit as st
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime, date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import logging
import io
import json

# -------------------------
# Config & Paths
# -------------------------
st.set_page_config(page_title="Crypto Liquidity Predictor", layout="wide", initial_sidebar_state="collapsed")
BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "Linear_Regression.pkl"
ENGINEERED_CSV = BASE_DIR / "data" / "processed" / "engineered_features.csv"  # optional autofill

LOG_DIR = BASE_DIR / "logs"
REPORT_DIR = BASE_DIR / "reports"
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"
CSV_HISTORY = REPORT_DIR / "predictions" / "prediction_history.csv"

# logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# -------------------------
# The model expects only these numeric features at predict time:
# -------------------------
MODEL_FEATURES = [
    "price",
    "1h",
    "24h",
    "7d",
    "24h_volume",
    "mkt_cap",
    "liquidity_ratio",
    "price_change_24h",
]

# Full UI fields (includes coin/symbol/date for UX) — match schema you gave
UI_FIELDS = [
    "coin", "symbol", "price", "1h", "24h", "7d",
    "24h_volume", "mkt_cap", "date", "liquidity_ratio", "price_change_24h"
]

# -------------------------
# Load model safely
# -------------------------
@st.cache_resource
def load_model(path: Path):
    if not path.exists():
        st.error(f"Model not found: {path}")
        st.stop()
    try:
        m = joblib.load(path)
        return m
    except Exception as e:
        st.error(f"Failed to load model: {e}")
        st.stop()

model = load_model(MODEL_PATH)

# If model exposes feature_names_in_, use it to reorder
try:
    model_feature_names = list(model.feature_names_in_)
except Exception:
    model_feature_names = MODEL_FEATURES.copy()

# -------------------------
# Optional engineered CSV for autofill (not used for prediction)
# -------------------------
@st.cache_data
def load_engineered_csv(path: Path):
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return None
    return None

engineered_df = load_engineered_csv(ENGINEERED_CSV)

# -------------------------
# Helpers
# -------------------------
def prepare_model_df_from_ui_dict(d: dict) -> pd.DataFrame:
    """
    Create a DataFrame containing only the numeric MODEL_FEATURES.
    Reorder to match model.feature_names_in_ if available.
    """
    row = {}
    for f in MODEL_FEATURES:
        v = d.get(f, 0.0)
        try:
            # allow empty strings -> 0.0
            if v == "" or v is None:
                v = 0.0
            v = float(v)
        except Exception:
            v = 0.0
        row[f] = v
    df = pd.DataFrame([row])
    # If model expects a specific order/columns, reorder / select intersection
    # Use model_feature_names (from loaded model) but only keep the ones we can provide
    if all(name in df.columns for name in model_feature_names):
        df = df[model_feature_names]
    else:
        # select MODEL_FEATURES order
        df = df[MODEL_FEATURES]
    return df

def generate_pdf(input_row: dict, pred: float):
    fname = f"liquidity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = REPORT_DIR / fname
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, 760, "Crypto Liquidity Prediction Report")
    c.setFont("Helvetica", 10)
    c.drawString(40, 742, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(40, 724, f"Predicted liquidity_score: {pred:.6f}")
    y = 702
    c.drawString(40, y, "Input features:")
    y -= 18
    for col, val in input_row.items():
        line = f"{col}: {val}"
        c.drawString(50, y, line[:120])
        y -= 14
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = 750
    c.save()
    return path

def save_history_csv(ui_df: pd.DataFrame, preds, mode: str):
    out = ui_df.copy().reset_index(drop=True)
    out["prediction"] = preds
    out["mode"] = mode
    out["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if CSV_HISTORY.exists():
        out.to_csv(CSV_HISTORY, mode="a", header=False, index=False)
    else:
        out.to_csv(CSV_HISTORY, index=False)

# -------------------------
# THEME / GITHUB-DARK CSS (B1) and button fixes
# We'll toggle by setting a 'data-theme' attribute on documentElement via small JS injection.
# -------------------------
BASE_CSS = """
<style>
:root{
  --bg: #ffffff;
  --card: linear-gradient(180deg,#ffffff,#f4f7fb);
  --text: #0b1b2b;
  --muted: #445;
  --accent: #2563eb;
}
[data-theme="dark"] {
  --bg: #0b1117;
  --card: linear-gradient(180deg,#071021,#091827);
  --text: #e6eef8;
  --muted: #9fb3d6;
  --accent: #2381ff;
}
/* App backgrounds and text */
body, .stApp { background: var(--bg); color: var(--text); }
/* Card style */
.card { background: var(--card); padding: 14px; border-radius:12px; box-shadow:0 8px 20px rgba(2,6,23,0.06); }
/* headers */
.kv { font-weight:700; color:var(--text); }
.small { color: var(--muted); font-size:0.95rem; margin-bottom:6px; }

/* Buttons: ensure visible in both themes */
.stButton>button, button[kind="primary"], button[kind="secondary"] {
  color: #ffffff !important;
  background-color: var(--accent) !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 8px 12px !important;
  font-weight:600;
}

/* Button hover */
.stButton>button:hover { opacity: 0.95 !important; }

/* Input boxes */
input[type="number"], input[type="text"] {
  border-radius: 6px;
  height: 40px;
  padding: 6px;
}

/* Floating help bubble (light & dark variations) */
.floating-help-btn { position: fixed; right: 28px; top: 72px; z-index: 9999; }
.floating-help-card { position: fixed; right: 28px; top: 120px; z-index: 9998; width: 340px; padding: 14px; border-radius:10px; box-shadow:0 8px 28px rgba(2,6,23,0.32); }
[data-theme="dark"] .floating-help-card { background: linear-gradient(180deg,#071021,#091827); color:#e6eef8; }
[data-theme="light"] .floating-help-card { background: rgba(255,255,255,0.98); color:var(--text); border: 1px solid rgba(10,20,40,0.04);}

/* small caption */
.stCaption { color: var(--muted) !important; }
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

# -------------------------
# Initialize session_state for toggles
# -------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "show_help" not in st.session_state:
    st.session_state.show_help = False

# -------------------------
# Top bar: toggles and title
# - Dark mode checkbox toggles session state and applies theme by setting data-theme attr
# - Help button toggles floating help bubble
# -------------------------
top1, top2, top3 = st.columns([1,6,1])
with top1:
    dm_checkbox = st.checkbox("Dark mode", value=st.session_state.dark_mode)
    if dm_checkbox != st.session_state.dark_mode:
        st.session_state.dark_mode = dm_checkbox
        # set attribute for CSS selectors
        if st.session_state.dark_mode:
            st.markdown('<script>document.documentElement.setAttribute("data-theme","dark")</script>', unsafe_allow_html=True)
        else:
            st.markdown('<script>document.documentElement.setAttribute("data-theme","light")</script>', unsafe_allow_html=True)
            
# ensure initial theme applied at first run
if st.session_state.dark_mode:
    st.markdown('<script>document.documentElement.setAttribute("data-theme","dark")</script>', unsafe_allow_html=True)
else:
    st.markdown('<script>document.documentElement.setAttribute("data-theme","light")</script>', unsafe_allow_html=True)

with top2:
    st.title("🔮 Crypto Liquidity Predictor")
    st.markdown("<div class='small'>Predict short-term liquidity_score. Use numeric inputs only (the model will ignore coin/symbol/date).</div>", unsafe_allow_html=True)
with top3:
    # Use a regular button that toggles show_help in session state
    if st.button("Help"):
        st.session_state.show_help = not st.session_state.show_help

# render a small floating help placeholder (CSS positions actual card)
st.markdown("<div class='floating-help-btn'></div>", unsafe_allow_html=True)

# -------------------------
# Render help bubble (floating) if toggled
# -------------------------
if st.session_state.show_help:
    help_html = """
    <div class="floating-help-card">
      <strong style="font-size:1.05rem">Quick Help</strong>
      <p style="margin:8px 0 6px 0; font-size:0.95rem">
       Enter the 8 numeric inputs below. The model uses these numeric features:
      </p>
      <ul style="margin:6px 0 8px 18px; font-size:0.95rem">
        <li>price</li><li>1h</li><li>24h</li><li>7d</li><li>24h_volume</li>
        <li>mkt_cap</li><li>liquidity_ratio</li><li>price_change_24h</li>
      </ul>
      <div style="font-size:0.9rem; opacity:0.9">Click <strong>Help</strong> again to close this box.</div>
    </div>
    """
    st.markdown(help_html, unsafe_allow_html=True)

st.markdown("---")

# -------------------------
# Layout: left inputs, right charts
# -------------------------
left, right = st.columns([1.1, 1])

# -------------------------
# LEFT: Inputs & Batch
# -------------------------
with left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📥 Input (numeric features)")

    # optional autofill
    coin_choice = None
    if engineered_df is not None and "coin" in engineered_df.columns:
        coin_choice = st.selectbox("Auto-fill by coin (optional)", ["-- none --"] + engineered_df["coin"].dropna().unique().tolist())
    else:
        st.info("Auto-fill unavailable (engineered CSV missing).")
        coin_choice = "-- none --"

    # prepare ui dict with defaults or autofill
    ui = {}
    if coin_choice and coin_choice != "-- none --":
        sample = engineered_df[engineered_df["coin"] == coin_choice].iloc[0]
        ui = {
            "coin": sample.get("coin", ""),
            "symbol": sample.get("symbol", ""),
            "price": sample.get("price", 0.0),
            "1h": sample.get("1h", 0.0),
            "24h": sample.get("24h", 0.0),
            "7d": sample.get("7d", 0.0),
            "24h_volume": sample.get("24h_volume", 0.0),
            "mkt_cap": sample.get("mkt_cap", 0.0),
            "date": sample.get("date", str(date.today())),
            "liquidity_ratio": sample.get("liquidity_ratio", 0.0),
            "price_change_24h": sample.get("price_change_24h", 0.0)
        }
        st.success("Auto-filled (editable).")
    else:
        ui = {
            "coin": "",
            "symbol": "",
            "price": 0.0,
            "1h": 0.0,
            "24h": 0.0,
            "7d": 0.0,
            "24h_volume": 0.0,
            "mkt_cap": 0.0,
            "date": str(date.today()),
            "liquidity_ratio": 0.0,
            "price_change_24h": 0.0
        }

    # Only numeric fields used by model are presented as inputs (but we also show coin/symbol/date for UX)
    st.markdown("**General (for history only)**")
    g1, g2, g3 = st.columns(3)
    with g1:
        ui["coin"] = st.text_input("Coin (optional)", value=ui["coin"])
    with g2:
        ui["symbol"] = st.text_input("Symbol (optional)", value=ui["symbol"])
    with g3:
        ui["date"] = st.text_input("Date (YYYY-MM-DD)", value=str(ui["date"]))

    st.markdown("**Price & Volume**")
    p1, p2, p3 = st.columns(3)
    with p1:
        ui["price"] = st.number_input("price", value=float(ui["price"]))
        ui["24h_volume"] = st.number_input("24h_volume", value=float(ui["24h_volume"]))
    with p2:
        ui["mkt_cap"] = st.number_input("mkt_cap", value=float(ui["mkt_cap"]))
        ui["liquidity_ratio"] = st.number_input("liquidity_ratio", value=float(ui["liquidity_ratio"]))
    with p3:
        ui["price_change_24h"] = st.number_input("price_change_24h", value=float(ui["price_change_24h"]))

    st.markdown("**Price Changes**")
    c1, c2, c3 = st.columns(3)
    with c1:
        ui["1h"] = st.number_input("1h (decimal)", value=float(ui["1h"]))
    with c2:
        ui["24h"] = st.number_input("24h (decimal)", value=float(ui["24h"]))
    with c3:
        ui["7d"] = st.number_input("7d (decimal)", value=float(ui["7d"]))

    st.markdown("---")

    # -----------------------------
    # Predict Button
    # -----------------------------
    if st.button("🚀 Predict Liquidity Score", use_container_width=True):
        try:
            model_df = prepare_model_df_from_ui_dict(ui)
            preds = model.predict(model_df)
            pred = float(preds[0])
            st.success(f"Predicted liquidity_score: {pred:.6f}")

            # Save history CSV with UI fields + prediction
            ui_df = pd.DataFrame([{k: ui.get(k, "") for k in UI_FIELDS}])
            save_history_csv(ui_df, [pred], mode="single")
            logging.info(json.dumps({"mode":"single","inputs":ui,"prediction":pred}))

            # PDF
            pdf_path = generate_pdf(ui, pred)
            with open(pdf_path, "rb") as f:
                st.download_button("📄 Download PDF report", f.read(), file_name=pdf_path.name, mime="application/pdf")
        except Exception as e:
            st.error(f"Prediction failed: {e}")
            logging.exception("Prediction failed")

    st.markdown("---")

    # -----------------------------
    # Batch mode (unchanged logic)
    # -----------------------------
    st.header("Batch mode (CSV upload or editable table)")
    st.write("CSV should contain at least the numeric MODEL features (price,1h,24h,7d,24h_volume,mkt_cap,liquidity_ratio,price_change_24h). Coin/symbol/date can be present but are optional.")

    uploaded = st.file_uploader("Upload CSV for batch prediction (optional)", type=["csv"])
    template = pd.DataFrame([{k: "" if k in ("coin","symbol","date") else 0.0 for k in UI_FIELDS}])
    editable = st.data_editor(template if uploaded is None else pd.read_csv(uploaded), num_rows="dynamic", width="stretch")

    if st.button("Predict (batch)"):
        if editable is None or len(editable) == 0:
            st.warning("No rows.")
        else:
            try:
                ui_batch = editable.copy()
                for col in UI_FIELDS:
                    if col not in ui_batch.columns:
                        ui_batch[col] = "" if col in ("coin","symbol","date") else 0.0

                # Prepare model input by selecting MODEL_FEATURES
                model_batch = pd.DataFrame()
                for f in MODEL_FEATURES:
                    if f in ui_batch.columns:
                        model_batch[f] = pd.to_numeric(ui_batch[f], errors="coerce").fillna(0.0)
                    else:
                        # missing numeric column -> fill zeros
                        model_batch[f] = 0.0

                # Reorder to match model if possible
                if all(name in model_batch.columns for name in model_feature_names):
                    model_batch = model_batch[model_feature_names]
                else:
                    model_batch = model_batch[MODEL_FEATURES]

                preds = model.predict(model_batch)
                out = ui_batch.copy()
                out["prediction"] = preds
                st.dataframe(out)

                # Save history CSV with UI fields + preds
                save_history_csv(out[UI_FIELDS + ["prediction"]], preds, mode="batch")

                # Provide download
                csv_buf = out.to_csv(index=False).encode("utf-8")
                st.download_button("⬇ Download batch predictions CSV", csv_buf, "batch_predictions.csv")
                logging.info(f"Batch predicted {len(out)} rows")
            except Exception as e:
                st.error(f"Batch prediction failed: {e}")
                logging.exception("Batch error")

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# RIGHT: Charts & feature importance & history
# -------------------------
with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Charts & Insights")

    # Feature importance (linear model coefficients)
    st.subheader("Feature importance (linear model coefficients)")
    try:
        if hasattr(model, "coef_"):
            coefs = np.asarray(model.coef_).flatten()
            # Determine names: prefer model.feature_names_in_ if available
            try:
                names = list(model.feature_names_in_)
            except Exception:
                names = MODEL_FEATURES
            # Align lengths
            names = [n for n in names if n in MODEL_FEATURES]
            if len(coefs) >= len(names):
                coefs = coefs[:len(names)]
            imp_df = pd.DataFrame({"feature": names, "coef": coefs})
            imp_df = imp_df.sort_values("coef", key=lambda s: s.abs(), ascending=False)
            st.table(imp_df.head(12))
            fig, ax = plt.subplots(figsize=(6,4))
            imp_df.set_index("feature")["coef"].head(12).plot(kind="barh", ax=ax)
            ax.set_title("Top coefficients")
            st.pyplot(fig)
        else:
            st.write("Model has no coefficients attribute.")
    except Exception as e:
        st.write("Could not render feature importance:", e)

    # Real-time preview chart: vary price and predict
    st.subheader("Real-time preview (price vs predicted liquidity)")
    try:
        # base numeric values from last UI 'ui' dict
        base_vals = {f: float(ui.get(f, 0.0)) for f in MODEL_FEATURES}
        base_price = base_vals.get("price", 1.0) or 1.0
        prices = np.linspace(base_price * 0.9, base_price * 1.1, 30)
        sim_rows = []
        for p in prices:
            r = base_vals.copy()
            r["price"] = float(p)
            sim_rows.append(r)
        sim_df = pd.DataFrame(sim_rows)
        # reorder to model expectation
        if all(name in sim_df.columns for name in model_feature_names):
            sim_df = sim_df[model_feature_names]
        else:
            sim_df = sim_df[MODEL_FEATURES]
        sim_preds = model.predict(sim_df)
        fig2, ax2 = plt.subplots(figsize=(6,3))
        ax2.plot(prices, sim_preds, marker="o")
        ax2.set_xlabel("price (simulated)")
        ax2.set_ylabel("predicted liquidity_score")
        st.pyplot(fig2)
    except Exception as e:
        st.write("Preview chart unavailable:", e)

    # History (CSV)
    st.subheader("Prediction history (recent)")
    if CSV_HISTORY.exists():
        try:
            hist = pd.read_csv(CSV_HISTORY, parse_dates=["timestamp"])
            st.dataframe(hist.tail(50))
            # plot daily average
            hist["timestamp"] = pd.to_datetime(hist["timestamp"])
            daily = hist.groupby(hist["timestamp"].dt.date)["prediction"].mean().reset_index()
            fig3, ax3 = plt.subplots(figsize=(6,3))
            ax3.plot(daily["timestamp"], daily["prediction"], marker="o")
            ax3.set_title("Daily average predicted liquidity_score")
            st.pyplot(fig3)
        except Exception as e:
            st.write("Could not load history:", e)
    else:
        st.info("No history yet. Make predictions to populate history.")

    st.markdown("</div>", unsafe_allow_html=True)

st.caption("This app sends only the numeric features the model was trained on to avoid mismatched feature-name errors. coin/symbol/date are kept for UX/history but are not passed to the model.")