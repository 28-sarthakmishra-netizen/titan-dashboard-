"""
=====================================================================
  TITAN COMPANY LIMITED  -  Financial Insights Dashboard
  Built with Python:  Streamlit (web app)  +  Plotly (interactive charts)
                      +  yfinance (live NSE share price)
=====================================================================

HOW TO RUN (in a terminal / command prompt, inside this folder):
    pip install -r requirements.txt
    streamlit run app.py

HOW TO CHANGE THINGS:
  * All financial numbers are in the  data/  folder (CSV files - open them in Excel).
      - titan_financials.csv   -> P&L, balance sheet, cash flow (FY20 ... FY26)
      - titan_segments.csv     -> segment revenue & profit
      - titan_shareholding.csv -> shareholding pattern
    Add a new year?  Just add a new column (e.g. FY27) to every CSV - the
    dashboard picks it up automatically.
  * Colours, company name, your name etc. are in SECTION 1 below.
  * Every chart lives in its own small block inside SECTION 7 - search for
    the chart title to find it.

Numbers: consolidated, Rs crore, taken from Titan's Annual Reports
(FY2019-20 to FY2025-26). Share prices: Yahoo Finance via yfinance.
"""

import math
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import forecast as fc                   # 'Forecast' tab: scenario & trend forecasts
import showcase                         # 'Why Titan' tab: drawings, cards, facts
from chatbot import SUGGESTIONS, TitanBot  # 'Ask TitanBot' tab: the chatbot brain

# Hide harmless "this will change in a future version" messages from pandas / yfinance
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", DeprecationWarning)
try:
    from pandas.errors import Pandas4Warning
    warnings.simplefilter("ignore", Pandas4Warning)
except ImportError:
    pass

# =====================================================================
# SECTION 1: SETTINGS  (safe to edit)
# =====================================================================
COMPANY = "Titan Company Limited"
NSE_SYMBOL = "TITAN.NS"          # Yahoo Finance code for Titan on NSE
BENCHMARK_SYMBOL = "^NSEI"       # Nifty 50 index
BENCHMARK_NAME = "Nifty 50"
SHARES_OUTSTANDING_CR = 88.78    # number of shares, in crore (face value Rs 1)

PREPARED_BY = "Sarthak Mishra"   # <- your name (shown in the sidebar)
PROGRAMME = "PGDM (FM), FIIB"    # <- your programme / institute

DATA_DIR = Path(__file__).parent / "data"
IST = timezone(timedelta(hours=5, minutes=30))

# Colour palette (checked for colour-blind safety on the dark background)
GOLD = "#B8862B"      # series 1 - Jewellery / Titan / main bars
BLUE = "#3987E5"      # series 2 - Watches / Nifty
AQUA = "#199E70"      # series 3 - EyeCare
VIOLET = "#9085E9"    # series 4 - Others
ACCENT = "#D4AF37"    # decorative gold (lines, borders, headings)
INK = "#EDE6D8"       # main text
INK2 = "#B9B0A0"      # secondary text
MUTED = "#857C6E"     # axis labels
SURFACE = "#15130F"   # card / chart background
GOOD, WARN, BAD = "#0CA30C", "#FAB219", "#D03B3B"   # status colours only

SEGMENT_COLORS = {
    "Jewellery": GOLD,
    "Watches & Wearables": BLUE,
    "EyeCare": AQUA,
    "Others": VIOLET,
}

FY_LONG = {f"FY{n:02d}": f"FY20{n-1:02d}-{n:02d}" for n in range(15, 40)}


def fy_end_date(fy: str) -> pd.Timestamp:
    """'FY26' -> 31 March 2026"""
    return pd.Timestamp(2000 + int(fy[2:]), 3, 31)


# =====================================================================
# SECTION 2: PAGE SETUP & LOOK
# =====================================================================
st.set_page_config(
    page_title="Titan · Financial Insights",
    page_icon="⌚",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp, .stMarkdown, p, li, label, input, textarea, button,
[data-testid="stWidgetLabel"], [data-testid="stMarkdownContainer"] {
    font-family: 'Inter', system-ui, sans-serif;
}
.stApp {
    background:
      radial-gradient(1100px 520px at 0% -8%, rgba(212,175,55,0.09), transparent 60%),
      radial-gradient(900px 480px at 100% -10%, rgba(57,135,229,0.05), transparent 60%),
      #100E0B;
}
.block-container { padding-top: 3.4rem; padding-bottom: 3rem; max-width: 1440px; }
h1, h2, h3, h4 { font-family: 'Cormorant Garamond', Georgia, serif !important; letter-spacing: .2px; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #19150F 0%, #100E0B 100%);
    border-right: 1px solid rgba(212,175,55,0.16);
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #F1DFA6; }

/* ---------- tabs ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 2px; border-bottom: 1px solid rgba(212,175,55,0.18); flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] { height: 44px; padding: 0 9px; color: #B9B0A0; font-weight: 500; font-size: 0.88rem; }
.stTabs [aria-selected="true"] { color: #F3E3B0 !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #D4AF37; height: 2px; }
.stTabs [data-baseweb="tab-border"] { display: none; }

/* ---------- hero ---------- */
.hero { display: flex; gap: 22px; align-items: center; padding: 18px 22px; border-radius: 18px;
        background: linear-gradient(135deg, rgba(212,175,55,0.10), rgba(255,255,255,0.015) 55%);
        border: 1px solid rgba(212,175,55,0.22); min-height: 150px; }
.hero svg.watch { width: 118px; height: 118px; flex: 0 0 auto; filter: drop-shadow(0 6px 18px rgba(0,0,0,0.55)); }
.eyebrow { font-size: 0.72rem; letter-spacing: 0.22em; color: #C9B37A; text-transform: uppercase; font-weight: 600; }
.hero-title { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 2.65rem; line-height: 1.05;
              color: #F6EBCD; margin: 4px 0 4px 0; font-weight: 600; }
.hero-sub { color: #B9B0A0; font-size: 0.98rem; }
.chips { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px; }
.chip { font-size: 0.74rem; color: #E6D9B5; padding: 3px 10px; border-radius: 999px;
        border: 1px solid rgba(212,175,55,0.30); background: rgba(212,175,55,0.06); }

/* ---------- live quote ---------- */
.quote { padding: 16px 18px; border-radius: 18px; border: 1px solid rgba(212,175,55,0.22);
         background: linear-gradient(160deg, rgba(255,255,255,0.035), rgba(255,255,255,0.01)); min-height: 150px; }
.quote .q-top { display:flex; flex-direction: column; gap: 2px; }
.quote .q-label { font-size: 0.72rem; letter-spacing: .16em; text-transform: uppercase; color: #C9B37A; font-weight: 600; }
.quote .q-live { font-size: 0.7rem; color: #B9B0A0; }
.quote .q-dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:5px; vertical-align: middle;
                animation: pulse 1.8s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .25; } }
.quote .q-price { font-size: 2.2rem; font-weight: 700; color: #F6EBCD; margin-top: 4px; font-variant-numeric: tabular-nums; }
.quote .q-chg { font-size: 0.95rem; font-weight: 600; }
.quote .q-grid { display: grid; grid-template-columns: 1.35fr 0.85fr 1.2fr; gap: 6px 12px; margin-top: 10px; }
.quote .q-grid div { font-size: 0.72rem; color: #857C6E; }
.quote .q-grid b { display:block; font-size: 0.86rem; white-space: nowrap; color: #EDE6D8; font-weight: 600; font-variant-numeric: tabular-nums; }

/* ---------- KPI cards ---------- */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 6px 0 14px 0; }
.kpi { padding: 14px 16px; border-radius: 14px; background: rgba(255,255,255,0.028);
       border: 1px solid rgba(237,230,216,0.08); position: relative; overflow: hidden; }
.kpi::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: linear-gradient(#D4AF37, #7A5A1C); }
.kpi .k-label { font-size: 0.7rem; color: #B9B0A0; text-transform: uppercase; letter-spacing: .08em; font-weight: 600; }
.kpi .k-value { font-size: 1.45rem; font-weight: 700; color: #F6EBCD; margin-top: 4px; font-variant-numeric: tabular-nums; }
.kpi .k-delta { font-size: 0.8rem; font-weight: 600; margin-top: 2px; }
.kpi .k-delta span, .kpi .k-note { color: #857C6E; font-weight: 400; font-size: 0.74rem; }

/* ---------- generic cards ---------- */
.card { padding: 16px 18px; border-radius: 14px; background: rgba(255,255,255,0.028);
        border: 1px solid rgba(237,230,216,0.08); height: 100%; }
.card h4 { margin: 0 0 6px 0; color: #F1DFA6; font-size: 1.25rem; }
.card p, .card li { color: #CFC6B6; font-size: 0.9rem; line-height: 1.55; }
.fact-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }
.fact { padding: 10px 12px; border-radius: 10px; background: rgba(212,175,55,0.05); border: 1px solid rgba(212,175,55,0.14); }
.fact .f-l { font-size: 0.7rem; color: #A99D86; text-transform: uppercase; letter-spacing: .08em; }
.fact .f-v { font-size: 0.98rem; color: #F1E7CF; font-weight: 600; margin-top: 2px; }

.verdict { padding: 16px 20px; border-radius: 14px; margin: 4px 0 12px 0;
           background: linear-gradient(90deg, rgba(12,163,12,0.12), rgba(12,163,12,0.02));
           border: 1px solid rgba(12,163,12,0.35); }
.verdict.warn { background: linear-gradient(90deg, rgba(250,178,25,0.12), rgba(250,178,25,0.02)); border-color: rgba(250,178,25,0.35); }
.verdict.bad  { background: linear-gradient(90deg, rgba(208,59,59,0.14), rgba(208,59,59,0.02)); border-color: rgba(208,59,59,0.38); }
.verdict .v-title { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.45rem; color: #F6EBCD; font-weight: 600; }
.verdict .v-body { color: #D8CFBF; font-size: 0.92rem; line-height: 1.6; margin-top: 4px; }

.section-title { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.6rem; color: #F1DFA6;
                 margin: 18px 0 2px 0; font-weight: 600; }
.section-sub { color: #9E9584; font-size: 0.86rem; margin-bottom: 6px; }
.note { color: #857C6E; font-size: 0.78rem; line-height: 1.5; }

.timeline { border-left: 2px solid rgba(212,175,55,0.35); margin: 8px 0 0 8px; padding-left: 18px; }
.tl-item { position: relative; margin-bottom: 14px; }
.tl-item::before { content: ""; position: absolute; left: -25px; top: 5px; width: 10px; height: 10px; border-radius: 50%;
                   background: #D4AF37; box-shadow: 0 0 0 3px rgba(212,175,55,0.18); }
.tl-year { color: #D4AF37; font-weight: 700; font-size: 0.82rem; letter-spacing: .06em; }
.tl-text { color: #CFC6B6; font-size: 0.88rem; }

.score-row { display: grid; grid-template-columns: 28px 1.4fr 0.8fr 2.2fr; gap: 10px; align-items: center;
             padding: 10px 12px; border-bottom: 1px solid rgba(237,230,216,0.06); }
.score-row .s-name { color: #EDE6D8; font-weight: 600; font-size: 0.9rem; }
.score-row .s-val { color: #F6EBCD; font-weight: 700; font-variant-numeric: tabular-nums; }
.score-row .s-why { color: #A99D86; font-size: 0.82rem; }

.brand-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }
.brand { padding: 14px 16px; border-radius: 14px; background: rgba(255,255,255,0.028); border: 1px solid rgba(237,230,216,0.08); }
.brand .b-head { display:flex; align-items:center; gap: 8px; font-weight: 700; color: #F1E7CF; }
.brand .b-dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
.brand .b-names { color: #CFC6B6; font-size: 0.86rem; margin-top: 6px; line-height: 1.5; }

div[data-testid="stDownloadButton"] button, div[data-testid="stButton"] button {
    border: 1px solid rgba(212,175,55,0.45); background: rgba(212,175,55,0.08); color: #F1DFA6;
}
footer { visibility: hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(showcase.CSS, unsafe_allow_html=True)


# =====================================================================
# SECTION 3: LOAD DATA (from the CSV files in data/)
# =====================================================================
@st.cache_data
def load_financials():
    raw = pd.read_csv(DATA_DIR / "titan_financials.csv")
    years = [c for c in raw.columns if c.upper().startswith("FY")]
    fin = raw.set_index("key")[years].T.astype(float)   # rows = years, columns = line items
    fin.index.name = "year"
    labels = raw.set_index("key")[["label", "statement", "unit"]]
    return fin, labels, years


@st.cache_data
def load_segments():
    seg = pd.read_csv(DATA_DIR / "titan_segments.csv")
    return seg


@st.cache_data
def load_shareholding():
    sh = pd.read_csv(DATA_DIR / "titan_shareholding.csv").set_index("holder")
    return sh.astype(float)


FIN, LABELS, YEARS = load_financials()
SEG_RAW = load_segments()
SHARE = load_shareholding()


def seg_table(metric: str, fold_corporate: bool = True) -> pd.DataFrame:
    """Segment numbers as a table: rows = years, columns = segments."""
    t = SEG_RAW[SEG_RAW["metric"] == metric].set_index("segment")[YEARS].T.astype(float)
    if fold_corporate and "Corporate (unallocated)" in t.columns:
        t["Others"] = t["Others"] + t["Corporate (unallocated)"]
        t = t.drop(columns=["Corporate (unallocated)"])
    return t


# =====================================================================
# SECTION 4: CALCULATIONS  (ratios & derived numbers)
# =====================================================================
def compute_metrics(f: pd.DataFrame, exclude_bullion: bool) -> pd.DataFrame:
    m = f.copy()
    m["core_revenue"] = m["revenue"] - m["bullion_sales"]
    m["rev_base"] = m["core_revenue"] if exclude_bullion else m["revenue"]
    m["total_income"] = m["revenue"] + m["other_income"]

    m["gross_profit"] = m["revenue"] - m["cogs"]          # bullion is sold at ~cost, so GP is unaffected
    m["ebitda"] = m["revenue"] - m["cogs"] - m["employee_cost"] - m["other_expenses"]
    m["ebit"] = m["pbt"] + m["finance_cost"] + m["exceptional"]   # before interest, tax & one-offs

    m["gross_margin"] = m["gross_profit"] / m["rev_base"] * 100
    m["ebitda_margin"] = m["ebitda"] / m["rev_base"] * 100
    m["ebit_margin"] = m["ebit"] / m["rev_base"] * 100
    m["pat_margin"] = m["pat"] / m["rev_base"] * 100

    m["revenue_growth"] = m["rev_base"].pct_change() * 100
    m["ebitda_growth"] = m["ebitda"].pct_change() * 100
    m["pat_growth"] = m["pat"].pct_change() * 100
    m["eps_growth"] = m["eps"].pct_change() * 100

    avg_equity = ((m["total_equity"] + m["total_equity"].shift(1)) / 2).fillna(m["total_equity"])
    m["total_debt"] = m["borrowings"] + m["gold_on_loan"] + m["lease_liabilities"]
    m["capital_employed"] = m["total_equity"] + m["total_debt"]
    avg_ce = ((m["capital_employed"] + m["capital_employed"].shift(1)) / 2).fillna(m["capital_employed"])

    m["roe"] = m["pat"] / avg_equity * 100
    m["roce"] = m["ebit"] / avg_ce * 100
    m["roa"] = m["pat"] / m["total_assets"] * 100
    m["debt_equity"] = m["borrowings"] / m["total_equity"]
    m["debt_equity_all"] = m["total_debt"] / m["total_equity"]
    m["interest_coverage"] = m["ebit"] / m["finance_cost"]
    m["current_ratio"] = m["current_assets"] / m["current_liabilities"]
    m["inventory_days"] = m["inventories"] / m["cogs"] * 365
    m["receivable_days"] = m["trade_receivables"] / m["revenue"] * 365
    m["asset_turnover"] = m["revenue"] / m["total_assets"]
    m["fcf"] = m["cfo"] - m["capex"]
    m["cash_conversion"] = m["cfo"] / m["pat"] * 100
    m["payout_ratio"] = m["dps"] / m["eps"] * 100
    m["tax_rate"] = m["tax"] / m["pbt"] * 100
    m["bvps"] = m["total_equity"] / SHARES_OUTSTANDING_CR
    m["liquid_funds"] = m["cash"] + m["bank_balances"] + m["current_investments"]
    m["net_debt"] = m["borrowings"] - m["liquid_funds"]
    return m


def cagr(first, last, years):
    try:
        if years <= 0 or first <= 0 or last <= 0:
            return np.nan
        return ((last / first) ** (1 / years) - 1) * 100
    except Exception:
        return np.nan


# =====================================================================
# SECTION 5: LIVE SHARE PRICE (Yahoo Finance via yfinance)
#   - downloads full daily history, refreshed every 15 minutes
#   - saves a copy in data/ so the dashboard still works offline
# =====================================================================
def _cache_file(symbol: str) -> Path:
    safe = "".join(ch for ch in symbol if ch.isalnum())
    return DATA_DIR / f"price_cache_{safe}.csv"


@st.cache_data(ttl=900, show_spinner=False)
def _download_history(symbol: str) -> pd.DataFrame:
    import yfinance as yf
    df = yf.Ticker(symbol).history(period="max", interval="1d", auto_adjust=False)
    if df is None or df.empty:
        raise ValueError("no data returned")
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    idx = pd.to_datetime(df.index)
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_localize(None)
    df.index = idx.normalize()
    df = df[~df.index.duplicated(keep="last")].dropna(subset=["Close"])
    return df


def load_price_history(symbol: str):
    """Returns (dataframe or None, status, message). status = live / saved / none"""
    cache = _cache_file(symbol)
    try:
        df = _download_history(symbol)
        try:
            df.to_csv(cache)
        except Exception:
            pass
        return df, "live", f"Live from Yahoo Finance · last trading day {df.index.max():%d %b %Y}"
    except Exception as err:
        if cache.exists():
            df = pd.read_csv(cache, index_col=0, parse_dates=True)
            saved = datetime.fromtimestamp(cache.stat().st_mtime)
            return df, "saved", (f"Could not reach Yahoo Finance, so showing prices saved on "
                                 f"{saved:%d %b %Y, %I:%M %p} (last trading day {df.index.max():%d %b %Y}).")
        return None, "none", str(err)


@st.cache_data(ttl=55, show_spinner=False)
def _download_quote(symbol: str) -> dict:
    import yfinance as yf
    fi = yf.Ticker(symbol).fast_info

    def grab(*names):
        for n in names:
            try:
                v = getattr(fi, n)
                if v is not None and not (isinstance(v, float) and math.isnan(v)):
                    return float(v)
            except Exception:
                continue
        return None

    last = grab("last_price")
    if last is None:
        raise ValueError("no live quote")
    return {
        "last": last,
        "prev": grab("previous_close", "regular_market_previous_close"),
        "day_high": grab("day_high"),
        "day_low": grab("day_low"),
        "year_high": grab("year_high"),
        "year_low": grab("year_low"),
        "time": datetime.now(IST),
        "live": True,
    }


def get_quote(symbol: str):
    try:
        return _download_quote(symbol)
    except Exception:
        df, status, _ = load_price_history(symbol)
        if df is None or len(df) < 2:
            return None
        last_year = df[df.index >= df.index.max() - pd.Timedelta(days=365)]
        return {
            "last": float(df["Close"].iloc[-1]), "prev": float(df["Close"].iloc[-2]),
            "day_high": float(df["High"].iloc[-1]), "day_low": float(df["Low"].iloc[-1]),
            "year_high": float(last_year["High"].max()), "year_low": float(last_year["Low"].min()),
            "time": df.index.max(), "live": False,
        }


# =====================================================================
# SECTION 6: SMALL HELPERS (number formats, chart style, cards)
# =====================================================================
def inr(x, decimals=0) -> str:
    """Indian number format: 384567.8 -> 3,84,568"""
    if x is None or (isinstance(x, (float, np.floating)) and (math.isnan(x) or math.isinf(x))):
        return "–"
    neg = x < 0
    s = f"{abs(x):.{decimals}f}"
    whole, frac = (s.split(".") + [""])[:2]
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    return ("-" if neg else "") + whole + (f".{frac}" if frac else "")


def crore(x, decimals=0) -> str:
    return f"₹{inr(x, decimals)} cr"


def pct(x, decimals=1) -> str:
    if x is None or (isinstance(x, (float, np.floating)) and math.isnan(x)):
        return "–"
    return f"{x:.{decimals}f}%"


PLOT_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2, "filename": "titan_chart"},
}


def style_fig(fig, title=None, height=380, ysuffix="", yprefix="", yfmt=None,
              legend=True, hovermode="x unified"):
    fig.update_layout(
        template="plotly_dark",
        title=dict(text=title, x=0, xanchor="left", y=0.98, yanchor="top",
                   font=dict(family="Cormorant Garamond, Georgia, serif", size=21, color=INK)) if title else None,
        height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=12.5, color=INK2),
        margin=dict(l=6, r=14, t=62 if title else 18, b=6),
        legend=dict(orientation="h", yanchor="top", y=-0.09, xanchor="left", x=0, traceorder="normal",
                    bgcolor="rgba(0,0,0,0)", font=dict(color=INK2, size=12)),
        hoverlabel=dict(bgcolor="#1E1A14", bordercolor=ACCENT, font=dict(color=INK, size=12.5)),
        hovermode=hovermode, showlegend=legend,
        bargap=0.34, bargroupgap=0.1, barcornerradius=4,
        uniformtext=dict(minsize=10, mode="hide"),
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(237,230,216,0.18)", tickfont=dict(color=INK2), ticks="")
    fig.update_yaxes(gridcolor="rgba(237,230,216,0.07)", zeroline=True, zerolinecolor="rgba(237,230,216,0.25)",
                     zerolinewidth=1, tickfont=dict(color=MUTED), ticksuffix=ysuffix, tickprefix=yprefix,
                     tickformat=yfmt)
    return fig


def show_chart(fig, key=None):
    try:
        st.plotly_chart(fig, width="stretch", theme=None, config=PLOT_CONFIG, key=key)
    except TypeError:   # older Streamlit versions
        st.plotly_chart(fig, use_container_width=True, theme=None, config=PLOT_CONFIG, key=key)


def show_table(df, **kwargs):
    kwargs.setdefault("height", 36 * (len(df) + 1) + 4)
    try:
        st.dataframe(df, width="stretch", **kwargs)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kwargs)


def stretch_button(label, key=None):
    try:
        return st.button(label, key=key, width="stretch")
    except TypeError:   # older Streamlit versions
        return st.button(label, key=key, use_container_width=True)


def kpi(label, value, delta=None, good_when_up=True, note=None) -> str:
    d = ""
    if delta is not None and not (isinstance(delta, float) and math.isnan(delta)):
        up = delta >= 0
        good = up if good_when_up else not up
        color = GOOD if good else BAD
        arrow = "▲" if up else "▼"
        d = f'<div class="k-delta" style="color:{color}">{arrow} {abs(delta):.1f}% <span>vs last year</span></div>'
    n = f'<div class="k-note">{note}</div>' if note else ""
    return f'<div class="kpi"><div class="k-label">{label}</div><div class="k-value">{value}</div>{d}{n}</div>'


def kpi_row(cards):
    st.markdown('<div class="kpi-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)


def section(title, sub=None):
    st.markdown(f'<div class="section-title">{title}</div>' + (f'<div class="section-sub">{sub}</div>' if sub else ""),
                unsafe_allow_html=True)


def watch_svg() -> str:
    """An original analog watch dial that shows the current Indian time and ticks live."""
    now = datetime.now(IST)
    s = now.second
    mnt = now.minute + s / 60
    hr = (now.hour % 12) + mnt / 60
    ticks = []
    for i in range(60):
        a = math.radians(i * 6)
        r1 = 41 if i % 5 == 0 else 44
        x1, y1 = 60 + r1 * math.sin(a), 60 - r1 * math.cos(a)
        x2, y2 = 60 + 46 * math.sin(a), 60 - 46 * math.cos(a)
        w = 2.2 if i % 5 == 0 else 0.7
        c = "#E9CF85" if i % 5 == 0 else "#7D6A45"
        ticks.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>')
    return f"""
<svg class="watch" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Analog watch showing Indian time">
  <style>
    .spin {{ transform-box: view-box; transform-origin: 60px 60px; }}
    .sec {{ animation: rot 60s steps(60) infinite; }}
    .min {{ animation: rot 3600s linear infinite; }}
    .hr  {{ animation: rot 43200s linear infinite; }}
    @keyframes rot {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
  </style>
  <defs>
    <linearGradient id="bz" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#F6E3A1"/><stop offset="45%" stop-color="#C8972F"/><stop offset="100%" stop-color="#6E4F17"/>
    </linearGradient>
    <radialGradient id="dl" cx="50%" cy="38%" r="70%">
      <stop offset="0%" stop-color="#2C251B"/><stop offset="100%" stop-color="#0B0907"/>
    </radialGradient>
  </defs>
  <rect x="49" y="0" width="22" height="12" rx="3" fill="#6E4F17"/>
  <rect x="49" y="108" width="22" height="12" rx="3" fill="#6E4F17"/>
  <rect x="113" y="56" width="6" height="8" rx="2" fill="#C8972F"/>
  <circle cx="60" cy="60" r="55" fill="url(#bz)"/>
  <circle cx="60" cy="60" r="49" fill="url(#dl)" stroke="#3A2F1E" stroke-width="1"/>
  {''.join(ticks)}
  <text x="60" y="42" text-anchor="middle" font-family="Cormorant Garamond, Georgia, serif" font-size="8" fill="#E9CF85" letter-spacing="1.5">TITAN</text>
  <text x="60" y="84" text-anchor="middle" font-family="Inter, sans-serif" font-size="4.2" fill="#8C7A55" letter-spacing="1">IST · LIVE</text>
  <g transform="rotate({hr*30:.2f} 60 60)"><g class="spin hr"><line x1="60" y1="64" x2="60" y2="35" stroke="#EDE6D8" stroke-width="3.2" stroke-linecap="round"/></g></g>
  <g transform="rotate({mnt*6:.2f} 60 60)"><g class="spin min"><line x1="60" y1="66" x2="60" y2="22" stroke="#EDE6D8" stroke-width="2.2" stroke-linecap="round"/></g></g>
  <g transform="rotate({s*6:.2f} 60 60)"><g class="spin sec"><line x1="60" y1="70" x2="60" y2="17" stroke="#D4AF37" stroke-width="0.9" stroke-linecap="round"/><circle cx="60" cy="60" r="2.6" fill="#D4AF37"/></g></g>
  <circle cx="60" cy="60" r="1.1" fill="#100E0B"/>
</svg>"""


# =====================================================================
# SECTION 7: THE DASHBOARD
# =====================================================================

# ---------------- Sidebar (filters) ----------------
with st.sidebar:
    st.markdown("## ⌚ Dashboard controls")
    yr_from, yr_to = st.select_slider(
        "Financial years to analyse",
        options=YEARS, value=(YEARS[0], YEARS[-1]),
        help="All charts, growth rates and the health check use this range.",
    )
    exclude_bullion = st.toggle(
        "Revenue excluding bullion sales", value=False,
        help=("Titan sometimes sells gold bars (bullion) at almost zero margin - e.g. ₹10,568 cr in FY26. "
              "Turn this on to see revenue and margins of the core business only."),
    )
    st.markdown("---")
    st.markdown("### Live market data")
    st.caption("Share price refreshes automatically every minute while the dashboard is open.")
    try:
        refresh = st.button("🔄 Refresh prices now", width="stretch")
    except TypeError:   # older Streamlit versions
        refresh = st.button("🔄 Refresh prices now", use_container_width=True)
    if refresh:
        _download_history.clear()
        _download_quote.clear()
        st.rerun()
    st.markdown("---")
    st.markdown(
        f"""<div class="note">
        <b style="color:#E6D9B5">Data sources</b><br>
        • Financials: Titan Annual Reports FY2019-20 to FY2025-26 (consolidated statements & segment notes)<br>
        • Share price: Yahoo Finance (NSE: TITAN) via <code>yfinance</code><br>
        • Shareholding: quarterly filings on BSE<br><br>
        <b style="color:#E6D9B5">Prepared by</b><br>{PREPARED_BY}<br>{PROGRAMME}<br><br>
        For academic use only. Not investment advice.
        </div>""",
        unsafe_allow_html=True,
    )

i0, i1 = YEARS.index(yr_from), YEARS.index(yr_to)
if i0 == i1:   # need at least two years for growth numbers
    i0 = max(0, i1 - 1)
SEL = YEARS[i0:i1 + 1]
M_ALL = compute_metrics(FIN, exclude_bullion)
M = M_ALL.loc[SEL]
LAST, FIRST = SEL[-1], SEL[0]
PREV = YEARS[YEARS.index(LAST) - 1] if YEARS.index(LAST) > 0 else None
N_YRS = len(SEL) - 1
REV_LABEL = "Revenue (excl. bullion)" if exclude_bullion else "Revenue from operations"


def yoy(col):
    if PREV is None:
        return None
    a, b = M_ALL.loc[PREV, col], M_ALL.loc[LAST, col]
    return (b / a - 1) * 100 if a else None


# ---------------- Header ----------------
h1, h2 = st.columns([2.15, 1], gap="medium")
with h1:
    st.markdown(
        f"""<div class="hero">{watch_svg()}
        <div>
          <div class="eyebrow">Tata Group company · NSE: TITAN · BSE: 500114</div>
          <div class="hero-title">Titan Company Limited</div>
          <div class="hero-sub">Financial Insights Dashboard &nbsp;·&nbsp; Jewellery · Watches · EyeCare · Lifestyle</div>
          <div class="chips">
            <span class="chip">{FY_LONG.get(FIRST, FIRST)} → {FY_LONG.get(LAST, LAST)}</span>
            <span class="chip">Consolidated · ₹ crore</span>
            <span class="chip">Source: Annual Reports</span>
            <span class="chip">Built with Python · Streamlit · Plotly</span>
          </div>
        </div></div>""",
        unsafe_allow_html=True,
    )


def live_quote_card():
    q = get_quote(NSE_SYMBOL)
    if q is None:
        st.markdown(
            """<div class="quote"><div class="q-label">Titan share price</div>
            <div class="q-price" style="font-size:1.2rem;margin-top:12px">Live price unavailable</div>
            <div class="note">Connect to the internet and press “Refresh prices now”.</div></div>""",
            unsafe_allow_html=True)
        return
    chg = q["last"] - q["prev"] if q["prev"] else 0.0
    chg_pct = chg / q["prev"] * 100 if q["prev"] else 0.0
    color = GOOD if chg >= 0 else BAD
    arrow = "▲" if chg >= 0 else "▼"
    mcap = q["last"] * SHARES_OUTSTANDING_CR
    pe = q["last"] / FIN.loc[YEARS[-1], "eps"]
    stamp = q["time"].strftime("%d %b %Y, %I:%M %p IST") if q["live"] else f"last close · {q['time']:%d %b %Y}"
    dot = GOOD if q["live"] else WARN
    st.markdown(
        f"""<div class="quote">
          <div class="q-top"><span class="q-label">Titan · NSE</span>
          <span class="q-live"><span class="q-dot" style="background:{dot}"></span>{'LIVE' if q['live'] else 'OFFLINE'} · {stamp}</span></div>
          <div class="q-price">₹{inr(q['last'], 2)}</div>
          <div class="q-chg" style="color:{color}">{arrow} ₹{abs(chg):,.2f} ({chg_pct:+.2f}%) <span style="color:#857C6E;font-weight:400">today</span></div>
          <div class="q-grid">
            <div>Market cap<b>₹{inr(mcap)} cr</b></div>
            <div>P/E ({YEARS[-1]} EPS)<b>{pe:.1f}x</b></div>
            <div>52-week range<b>{inr(q['year_low'])} – {inr(q['year_high'])}</b></div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


if hasattr(st, "fragment"):
    live_quote_card = st.fragment(run_every=60)(live_quote_card)

with h2:
    live_quote_card()

st.write("")

tab_over, tab_bot, tab_why, tab_stock, tab_pl, tab_seg, tab_bs, tab_ratio, tab_fc, tab_data = st.tabs([
    "🏛️ Overview", "💬 Ask TitanBot", "✨ Why Titan", "📈 Share Price", "💰 P&L", "💎 Segments",
    "🏦 Balance Sheet", "🩺 Health Check", "🔮 Forecast", "📚 Data",
])

# ---------- shared numbers for the selected range ----------
rev_cagr = cagr(M.loc[FIRST, "rev_base"], M.loc[LAST, "rev_base"], N_YRS)
pat_cagr = cagr(M.loc[FIRST, "pat"], M.loc[LAST, "pat"], N_YRS)
eps_cagr = cagr(M.loc[FIRST, "eps"], M.loc[LAST, "eps"], N_YRS)
loss_years = [y for y in SEL if M.loc[y, "pat"] <= 0]
cum_cfo, cum_pat = M["cfo"].sum(), M["pat"].sum()


# =====================================================================
# TAB 1: OVERVIEW
# =====================================================================
with tab_over:
    # ---- Verdict: is Titan profitable? ----
    if not loss_years:
        v_cls, v_icon = "", "✅"
        v_title = f"Is Titan profitable? Yes — net profit in every one of the {len(SEL)} years ({FIRST}–{LAST})."
    else:
        v_cls, v_icon = "warn", "⚠️"
        v_title = f"Titan made a loss in {', '.join(loss_years)}."
    best = M["pat"].idxmax()
    worst = M["pat"].idxmin()
    v_body = (
        f"Net profit moved from <b>{crore(M.loc[FIRST, 'pat'])}</b> in {FIRST} to <b>{crore(M.loc[LAST, 'pat'])}</b> in {LAST} "
        f"(growth of <b>{pct(pat_cagr)}</b> a year), while {REV_LABEL.lower()} grew <b>{pct(rev_cagr)}</b> a year. "
        f"Return on equity in {LAST} was <b>{pct(M.loc[LAST, 'roe'])}</b> — strong for a retailer. "
        f"Best year: {best}; weakest: {worst}. "
        f"Watch-out: Titan holds a lot of gold inventory, so operating cash flow is volatile — over this period it "
        f"turned only <b>{pct(cum_cfo / cum_pat * 100, 0)}</b> of profits into operating cash."
    )
    st.markdown(f'<div class="verdict {v_cls}"><div class="v-title">{v_icon} {v_title}</div>'
                f'<div class="v-body">{v_body}</div></div>', unsafe_allow_html=True)

    kpi_row([
        kpi(f"{REV_LABEL.split(' (')[0]} · {LAST}", crore(M.loc[LAST, "rev_base"]), yoy("rev_base")),
        kpi(f"Net profit · {LAST}", crore(M.loc[LAST, "pat"]), yoy("pat")),
        kpi(f"EBITDA margin · {LAST}", pct(M.loc[LAST, "ebitda_margin"]), note=f"EBITDA {crore(M.loc[LAST, 'ebitda'])}"),
        kpi(f"Return on equity · {LAST}", pct(M.loc[LAST, "roe"]), note="Profit ÷ average shareholders' equity"),
        kpi(f"EPS · {LAST}", f"₹{M.loc[LAST, 'eps']:.2f}", yoy("eps")),
        kpi(f"Dividend / share · {LAST}", f"₹{M.loc[LAST, 'dps']:g}", yoy("dps"),
            note=f"Payout {pct(M.loc[LAST, 'payout_ratio'], 0)} of EPS"),
    ])

    c1, c2 = st.columns([1.25, 1], gap="large")
    with c1:
        st.markdown(
            f"""<div class="card"><h4>About the company</h4>
            <p>Titan is India's largest branded jewellery and watch company. It started in 1984 as a joint venture
            between the <b>Tata Group</b> and the <b>Tamil Nadu Industrial Development Corporation (TIDCO)</b>,
            began operations in 1987 as Titan Watches, and entered jewellery in 1994 with <b>Tanishq</b>.
            Today jewellery brings in roughly nine of every ten rupees of revenue, while watches, eyewear (Titan Eye+),
            sarees (Taneira), fragrances (SKINN), bags (IRTH) and an engineering arm (TEAL) make up the rest.</p>
            <div class="fact-grid">
              <div class="fact"><div class="f-l">Founded</div><div class="f-v">1984 · Hosur, TN</div></div>
              <div class="fact"><div class="f-l">Headquarters</div><div class="f-v">Bengaluru</div></div>
              <div class="fact"><div class="f-l">Promoters</div><div class="f-v">Tata Group + TIDCO · {SHARE.iloc[0, -1]:.1f}%</div></div>
              <div class="fact"><div class="f-l">Retail network</div><div class="f-v">3,603 stores (Mar 2026)</div></div>
              <div class="fact"><div class="f-l">Managing Director</div><div class="f-v">Ajoy Chawla</div></div>
              <div class="fact"><div class="f-l">Listed on</div><div class="f-v">NSE · BSE · Nifty 50</div></div>
            </div></div>""",
            unsafe_allow_html=True,
        )
    with c2:
        segs = seg_table("revenue").loc[LAST]
        fig = go.Figure(go.Pie(
            labels=segs.index, values=segs.values, hole=0.62, sort=False, direction="clockwise",
            marker=dict(colors=[SEGMENT_COLORS[s] for s in segs.index], line=dict(color=SURFACE, width=2)),
            textinfo="percent", textposition="inside", insidetextorientation="horizontal", textfont=dict(color="#FFFFFF", size=12),
            hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} cr<br>%{percent}<extra></extra>",
        ))
        fig.add_annotation(text=f"<b>{crore(segs.sum())}</b><br><span style='font-size:11px;color:{INK2}'>total income {LAST}</span>",
                           showarrow=False, font=dict(size=15, color=INK))
        style_fig(fig, f"Where the money comes from · {LAST}", height=330, hovermode="closest")
        fig.update_layout(legend=dict(orientation="v", x=1.02, y=0.5, xanchor="left", yanchor="middle"))
        show_chart(fig, "ov_donut")

    c1, c2 = st.columns([1.25, 1], gap="large")
    with c1:
        base = M.iloc[0]
        fig = go.Figure()
        for col, name, color in [("rev_base", "Revenue", GOLD), ("pat", "Net profit", BLUE), ("total_equity", "Equity", AQUA)]:
            idx = M[col] / base[col] * 100
            fig.add_trace(go.Scatter(
                x=SEL, y=idx, name=name, mode="lines+markers", line=dict(color=color, width=2.4),
                marker=dict(size=8, line=dict(color=SURFACE, width=2)),
                customdata=M[col], hovertemplate=f"{name}: %{{y:.0f}} (actual %{{customdata:,.2f}})<extra></extra>",
            ))
            fig.add_annotation(x=SEL[-1], y=idx.iloc[-1], text=f"{name} {idx.iloc[-1]/100:.1f}x", showarrow=False,
                               xanchor="left", xshift=8, font=dict(color=INK2, size=11))
        fig.add_hline(y=100, line=dict(color="rgba(237,230,216,0.25)", width=1))
        style_fig(fig, f"Growth since {FIRST} (indexed, {FIRST} = 100)", height=360)
        fig.update_layout(margin=dict(r=90))
        show_chart(fig, "ov_index")
    with c2:
        latest_col = SHARE.columns[-1]
        sh = SHARE[latest_col]
        fig = go.Figure(go.Pie(
            labels=sh.index, values=sh.values, hole=0.6, sort=False,
            marker=dict(colors=[GOLD, BLUE, AQUA, VIOLET], line=dict(color=SURFACE, width=2)),
            textinfo="percent", textposition="inside", insidetextorientation="horizontal", textfont=dict(color="#FFFFFF", size=12),
            hovertemplate="<b>%{label}</b><br>%{value:.2f}%<extra></extra>",
        ))
        style_fig(fig, f"Who owns Titan · {latest_col}", height=360, hovermode="closest")
        fig.update_layout(legend=dict(orientation="v", x=1.02, y=0.5, xanchor="left", yanchor="middle"))
        show_chart(fig, "ov_share")

    section("Key milestones", "From the annual reports")
    st.markdown(
        f"""<div class="timeline">
        <div class="tl-item"><div class="tl-year">1984 – 1994</div><div class="tl-text">Incorporated as a Tata–TIDCO joint venture; Titan watches launched in 1987; entered jewellery with Tanishq in 1994, later eyewear.</div></div>
        <div class="tl-item"><div class="tl-year">FY2020-21 · COVID year</div><div class="tl-text">Stores shut for weeks; revenue held at {crore(FIN.loc['FY21','revenue'])} but net profit fell {abs(M_ALL.loc['FY21','pat_growth']):.0f}% to {crore(FIN.loc['FY21','pat'])}.</div></div>
        <div class="tl-item"><div class="tl-year">FY2021-22 · Rebound</div><div class="tl-text">Net profit more than doubled to {crore(FIN.loc['FY22','pat'])} as weddings and festivals came back.</div></div>
        <div class="tl-item"><div class="tl-year">FY2023-24 · CaratLane buy-out</div><div class="tl-text">Raised its CaratLane stake to ~99.99% (₹4,621 cr paid to the founders) — this is why reported equity dips in FY24.</div></div>
        <div class="tl-item"><div class="tl-year">FY2024-25 · ₹50,000 cr club</div><div class="tl-text">Crossed ₹50,000 crore of annual revenue for the first time.</div></div>
        <div class="tl-item"><div class="tl-year">FY2025-26 · Record year</div><div class="tl-text">Bought 67% of Damas Jewellery (GCC); revenue {crore(FIN.loc['FY26','revenue'])} and net profit up {M_ALL.loc['FY26','pat_growth']:.0f}% to {crore(FIN.loc['FY26','pat'])}.</div></div>
        </div>""",
        unsafe_allow_html=True,
    )


# =====================================================================
# TAB: ASK TITANBOT (chatbot)
#   The "brain" is in chatbot.py - it reads the same numbers as the charts.
# =====================================================================
def bot_price_info():
    """Live price summary for TitanBot (None when offline)."""
    df, status, _ = load_price_history(NSE_SYMBOL)
    if df is None or len(df) < 2:
        return None
    close = df["Close"]
    end = df.index.max()
    q = get_quote(NSE_SYMBOL)
    last = q["last"] if q else float(close.iloc[-1])
    prev = q["prev"] if (q and q["prev"]) else float(close.iloc[-2])

    def ret(years):
        s = close[close.index >= end - pd.DateOffset(years=years)]
        return (float(close.iloc[-1]) / float(s.iloc[0]) - 1) * 100 if len(s) > 1 else None

    yr = df[df.index >= end - pd.Timedelta(days=365)]
    when = (q["time"].strftime("live · %d %b %Y, %I:%M %p IST") if (q and q["live"])
            else f"last close · {end:%d %b %Y}")
    return {"last": last, "chg": (last / prev - 1) * 100 if prev else 0.0, "when": when,
            "mcap": last * SHARES_OUTSTANDING_CR, "pe": last / FIN.loc[YEARS[-1], "eps"],
            "low52": float(yr["Low"].min()), "high52": float(yr["High"].max()),
            "ret1y": ret(1), "ret5y": ret(5)}


CORE_REVENUE = FIN["revenue"] - FIN["bullion_sales"]      # revenue without bullion (gold-bar) sales
FC_BASE = {"revenue": float(CORE_REVENUE.iloc[-1])}       # forecasts start from the latest actual year


def preset_forecasts(n_years):
    """Bear / Base / Bull forecasts (used by TitanBot and the Forecast tab)."""
    return {name: fc.preset_forecast(name, FC_BASE, n_years, shares_cr=SHARES_OUTSTANDING_CR, last_fy=YEARS[-1])
            for name in fc.SCENARIOS}


BOT = TitanBot(
    fin=FIN, metrics=compute_metrics(FIN, exclude_bullion=False),
    seg_rev=seg_table("revenue", fold_corporate=False), seg_ebit=seg_table("ebit", fold_corporate=False),
    shareholding=SHARE, years=YEARS, price_fn=bot_price_info, forecast_fn=preset_forecasts,
)


def bot_chart(spec):
    """Turns the small chart description from TitanBot into a Plotly chart."""
    if spec["kind"] == "compare":
        fig = go.Figure()
        fig.add_trace(go.Bar(x=spec["labels"], y=spec["va"], name=spec["a"], marker_color=BLUE,
                             hovertemplate=f"{spec['a']}: ₹%{{y:,.0f}} cr<extra></extra>"))
        fig.add_trace(go.Bar(x=spec["labels"], y=spec["vb"], name=spec["b"], marker_color=GOLD,
                             hovertemplate=f"{spec['b']}: ₹%{{y:,.0f}} cr<extra></extra>"))
        style_fig(fig, spec["title"], height=300)
        fig.update_layout(barmode="group")
        return fig
    base = SEGMENT_COLORS.get(spec.get("segment"), GOLD)
    hl = spec.get("highlight")
    d, pre, suf = spec.get("decimals", 0), spec.get("prefix", ""), spec.get("suffix", "")
    labels = [f"{pre}{v:,.{d}f}{suf}" for v in spec["y"]]
    if spec["kind"] == "line":
        sizes = [13 if (hl and x == hl) else 8 for x in spec["x"]]
        fig = go.Figure(go.Scatter(
            x=spec["x"], y=spec["y"], mode="lines+markers+text", text=labels, textposition="top center",
            textfont=dict(color=INK2, size=11), line=dict(color=base, width=2.2),
            marker=dict(size=sizes, color=base, line=dict(color=SURFACE, width=2)),
            hovertemplate="%{x}: %{text}<extra></extra>"))
        lo, hi = min(spec["y"]), max(spec["y"])
        pad = (hi - lo) * 0.3 or abs(hi) * 0.2 or 1
        fig.update_yaxes(range=[min(0, lo - pad), hi + pad])
    else:
        colors = [base if (hl is None or x == hl) else "rgba(237,230,216,0.16)" for x in spec["x"]]
        fstart = spec.get("forecast_from")
        is_fc = [bool(fstart) and spec["x"].index(x) >= spec["x"].index(fstart) for x in spec["x"]]
        fig = go.Figure(go.Bar(x=spec["x"], y=spec["y"], marker_color=colors, text=labels, textposition="outside",
                               marker_pattern=dict(shape=["/" if f else "" for f in is_fc], fgcolor=SURFACE,
                                                   solidity=0.25),
                               textfont=dict(color=INK2, size=11), cliponaxis=False,
                               hovertemplate="%{x}: %{text}<extra></extra>"))
        if fstart:
            fig.add_vline(x=spec["x"].index(fstart) - 0.5, line=dict(color="rgba(212,175,55,0.5)", width=1, dash="dot"))
            fig.add_annotation(x=spec["x"].index(fstart) - 0.5, y=1.02, yref="paper", text="forecast →",
                               showarrow=False, xanchor="left", font=dict(color=MUTED, size=11))
        fig.update_yaxes(range=[min(0, min(spec["y"]) * 1.2), max(spec["y"]) * 1.2])
    style_fig(fig, spec["title"], height=290, legend=False, ysuffix=suf, yprefix=pre, hovermode="closest")
    return fig


with tab_bot:
    st.markdown(
        """<div class="sc-hero"><h2>💬 Ask TitanBot</h2>
        <p>Type any question about Titan's finances in <b>English or Hinglish</b> — for example
        <i>“How was FY24?”</i>, <i>“FY26 kaisa raha?”</i>, <i>“compare FY22 vs FY26”</i> or <i>“debt kitna hai?”</i>.
        TitanBot answers instantly from the annual-report numbers (FY2019-20 to FY2025-26), with a chart.
        It runs fully inside this Python app — no paid AI service needed.</p></div>""",
        unsafe_allow_html=True)

    if "chat" not in st.session_state:
        st.session_state.chat = [{"role": "assistant", **BOT.answer("hi")}]

    st.markdown('<div class="note" style="margin-bottom:6px">Quick questions — click one:</div>', unsafe_allow_html=True)
    clicked = None
    sug_cols = st.columns(4)
    for i, sug in enumerate(SUGGESTIONS):
        with sug_cols[i % 4]:
            if stretch_button(sug, key=f"sugg_{i}"):
                clicked = sug

    chat_box = st.container()
    typed = st.chat_input("Ask TitanBot… e.g. “FY24 kaisa raha?” or “profit in 2023”", key="bot_input")
    question = typed or clicked
    if question:
        st.session_state.chat.append({"role": "user", "text": question})
        st.session_state.chat.append({"role": "assistant", **BOT.answer(question)})

    with chat_box:
        for i, msg in enumerate(st.session_state.chat):
            with st.chat_message(msg["role"], avatar="⌚" if msg["role"] == "assistant" else "🧑‍💼"):
                st.markdown(msg["text"])
                if msg.get("table"):
                    show_table(pd.DataFrame(msg["table"]), hide_index=True)
                if msg.get("chart"):
                    show_chart(bot_chart(msg["chart"]), key=f"botchart_{i}")

    c1, c2 = st.columns([1, 5])
    with c1:
        if stretch_button("🧹 Clear chat", key="clear_chat"):
            st.session_state.chat = [{"role": "assistant", **BOT.answer("hi")}]
            st.rerun()
    with c2:
        st.markdown('<div class="note" style="padding-top:8px">TitanBot is rule-based: it understands questions about '
                    'revenue, profit, margins, EPS, dividend, ROE/ROCE, debt, cash flow, inventory, segments, share price, '
                    'shareholding, history and USPs. Years can be written as FY24, 2023-24 or 2024.</div>',
                    unsafe_allow_html=True)


# =====================================================================
# TAB: WHY TITAN (USP showcase) - drawings & facts live in showcase.py
# =====================================================================
with tab_why:
    st.markdown(
        """<div class="sc-hero"><h2>✨ What makes Titan, Titan</h2>
        <p>Titan's edge is <b>engineering + trust + reach</b>: watches thin enough to set world records, jewellery
        customers can verify, and India's widest lifestyle retail network. Hover over (or tap) the cards to flip them.</p></div>""",
        unsafe_allow_html=True)
    st.markdown(showcase.stats_html(), unsafe_allow_html=True)

    section("Signature products", "Original illustrations · hover or tap a card to see the facts behind it")
    st.markdown(showcase.cards_html(), unsafe_allow_html=True)

    c1, c2 = st.columns([1.25, 1], gap="large")
    with c1:
        section("How slim is slim?", "Titan Edge next to everyday objects — drawn to scale")
        st.markdown(showcase.slim_html(), unsafe_allow_html=True)
    with c2:
        section("Quick facts", "Changes every few seconds")
        st.markdown(showcase.did_you_know_html(), unsafe_allow_html=True)

    section("Innovation timeline", "Hover over a dot for the story")
    tl = showcase.TIMELINE
    xs = list(range(len(tl)))
    levels = [1.0, -1.0, 1.7, -1.7]
    ys = [levels[i % 4] for i in xs]
    fig = go.Figure()
    for x, y in zip(xs, ys):
        fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=y * 0.82, line=dict(color="rgba(212,175,55,0.35)", width=1))
    fig.add_hline(y=0, line=dict(color="rgba(212,175,55,0.55)", width=2))
    fig.add_trace(go.Scatter(
        x=xs, y=[0] * len(xs), mode="markers", marker=dict(size=13, color=ACCENT, line=dict(color=SURFACE, width=3)),
        customdata=[[e[0], e[1], e[2]] for e in tl],
        hovertemplate="<b>%{customdata[0]} · %{customdata[1]}</b><br>%{customdata[2]}<extra></extra>", showlegend=False))
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="text", text=[f"<b>{e[0]}</b><br>{e[1]}" for e in tl],
        textposition=["top center" if y > 0 else "bottom center" for y in ys],
        textfont=dict(color=INK, size=12), customdata=[[e[0], e[1], e[2]] for e in tl],
        hovertemplate="<b>%{customdata[0]} · %{customdata[1]}</b><br>%{customdata[2]}<extra></extra>", showlegend=False))
    style_fig(fig, None, height=330, legend=False, hovermode="closest")
    fig.update_xaxes(visible=False, range=[-0.6, len(xs) - 0.4])
    fig.update_yaxes(visible=False, range=[-2.9, 2.9])
    show_chart(fig, "why_timeline")
    st.markdown('<div class="note">Facts come from Titan\'s annual reports and company releases; product drawings are '
                'original illustrations, not photographs.</div>', unsafe_allow_html=True)


# =====================================================================
# TAB 2: SHARE PRICE (LIVE)
# =====================================================================
with tab_stock:
    with st.spinner("Fetching Titan share prices from Yahoo Finance…"):
        px_df, px_status, px_msg = load_price_history(NSE_SYMBOL)

    if px_df is None:
        st.warning(
            "Couldn't load share prices. Check that the internet is on and that `yfinance` is installed "
            "(`pip install yfinance`), then press **Refresh prices now** in the sidebar. "
            f"(Technical detail: {px_msg})"
        )
    else:
        if px_status == "live":
            st.caption(f"🟢 {px_msg}")
        else:
            st.info(f"🟠 {px_msg}")

        c1, c2, c3 = st.columns([2.2, 1.3, 1.6])
        with c1:
            period = st.radio("Period", ["1M", "6M", "YTD", "1Y", "3Y", "5Y", "10Y", "Max"], index=5,
                              horizontal=True, key="px_period")
        with c2:
            ctype = st.radio("Chart", ["Candles", "Line"], index=1, horizontal=True, key="px_type")
        with c3:
            ma_choice = st.multiselect("Moving averages", ["50-day", "200-day"], default=["200-day"], key="px_ma")

        close = px_df["Close"]
        ma50, ma200 = close.rolling(50).mean(), close.rolling(200).mean()
        end = px_df.index.max()
        starts = {
            "1M": end - pd.DateOffset(months=1), "6M": end - pd.DateOffset(months=6),
            "YTD": pd.Timestamp(end.year, 1, 1), "1Y": end - pd.DateOffset(years=1),
            "3Y": end - pd.DateOffset(years=3), "5Y": end - pd.DateOffset(years=5),
            "10Y": end - pd.DateOffset(years=10), "Max": px_df.index.min(),
        }
        start = max(starts[period], px_df.index.min())
        view = px_df[px_df.index >= start]
        vclose = view["Close"]

        # ---- quick stats for the chosen period ----
        days = (vclose.index[-1] - vclose.index[0]).days
        period_ret = (vclose.iloc[-1] / vclose.iloc[0] - 1) * 100
        period_cagr = cagr(vclose.iloc[0], vclose.iloc[-1], days / 365.25) if days > 365 else np.nan
        vol = vclose.pct_change().std() * np.sqrt(252) * 100
        drawdown = (vclose / vclose.cummax() - 1).min() * 100
        last252 = px_df[px_df.index >= end - pd.Timedelta(days=365)]
        hi52, lo52 = last252["High"].max(), last252["Low"].min()
        kpi_row([
            kpi(f"Return · {period}", pct(period_ret), note=f"₹{inr(vclose.iloc[0], 0)} → ₹{inr(vclose.iloc[-1], 0)}"),
            kpi("Yearly growth (CAGR)", pct(period_cagr) if not math.isnan(period_cagr) else "–",
                note="Only shown for periods longer than 1 year"),
            kpi("Volatility (annual)", pct(vol), note="How much the price swings"),
            kpi("Biggest fall in period", pct(drawdown), note="Peak-to-bottom drop"),
            kpi("52-week high / low", f"₹{inr(hi52)}", note=f"Low ₹{inr(lo52)} · now {pct((close.iloc[-1]/hi52-1)*100)} from high"),
        ])

        # ---- price chart + volume ----
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.76, 0.24], vertical_spacing=0.03)
        if ctype == "Candles":
            fig.add_trace(go.Candlestick(
                x=view.index, open=view["Open"], high=view["High"], low=view["Low"], close=view["Close"],
                name="Titan", increasing=dict(line=dict(color=AQUA, width=1), fillcolor=AQUA),
                decreasing=dict(line=dict(color=BAD, width=1), fillcolor=BAD)), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=view.index, y=vclose, name="Titan close", mode="lines",
                line=dict(color=ACCENT, width=2), fill="tozeroy", fillcolor="rgba(212,175,55,0.07)",
                hovertemplate="₹%{y:,.2f}<extra>Close</extra>"), row=1, col=1)
        if "50-day" in ma_choice:
            fig.add_trace(go.Scatter(x=view.index, y=ma50.loc[view.index], name="50-day average",
                                     line=dict(color=BLUE, width=1.6), hovertemplate="₹%{y:,.0f}<extra>50-day avg</extra>"),
                          row=1, col=1)
        if "200-day" in ma_choice:
            fig.add_trace(go.Scatter(x=view.index, y=ma200.loc[view.index], name="200-day average",
                                     line=dict(color=VIOLET, width=1.6), hovertemplate="₹%{y:,.0f}<extra>200-day avg</extra>"),
                          row=1, col=1)
        fig.add_trace(go.Bar(x=view.index, y=view["Volume"], name="Volume", marker_color="rgba(184,134,43,0.45)",
                             hovertemplate="%{y:,.0f} shares<extra>Volume</extra>", showlegend=False), row=2, col=1)
        style_fig(fig, f"Titan share price · {period}", height=560)
        lo, hi = view["Low"].min(), view["High"].max()
        fig.update_yaxes(range=[lo * 0.95, hi * 1.03], tickprefix="₹", row=1, col=1)
        fig.update_yaxes(tickformat="~s", zeroline=False, row=2, col=1)
        fig.update_xaxes(rangeslider_visible=False, rangebreaks=[dict(bounds=["sat", "mon"])])
        fig.update_layout(bargap=0, barcornerradius=0)
        show_chart(fig, "px_main")

        # ---- Titan vs Nifty ----
        bench_df, bench_status, _ = load_price_history(BENCHMARK_SYMBOL)
        if bench_df is not None:
            section(f"Titan vs {BENCHMARK_NAME}", "Both start at 100 on the first day of the chosen period, so you can compare returns directly")
            joined = pd.concat([vclose.rename("Titan"), bench_df["Close"].rename(BENCHMARK_NAME)],
                               axis=1, sort=True).dropna()
            if len(joined) > 2:
                idx = joined / joined.iloc[0] * 100
                fig = go.Figure()
                for col, color in [("Titan", GOLD), (BENCHMARK_NAME, BLUE)]:
                    fig.add_trace(go.Scatter(x=idx.index, y=idx[col], name=col, line=dict(color=color, width=2.2),
                                             hovertemplate=f"{col}: %{{y:.1f}}<extra></extra>"))
                    fig.add_annotation(x=idx.index[-1], y=idx[col].iloc[-1], text=f"{col} {idx[col].iloc[-1]-100:+.0f}%",
                                       showarrow=False, xanchor="left", xshift=6, font=dict(color=INK2, size=11))
                fig.add_hline(y=100, line=dict(color="rgba(237,230,216,0.25)", width=1))
                style_fig(fig, None, height=340)
                fig.update_layout(margin=dict(r=110))
                fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
                show_chart(fig, "px_bench")

        # ---- valuation at each financial-year end ----
        section("Valuation at each year-end", "Share price on the last trading day of March vs that year's earnings (P/E) and dividend")
        rows = []
        for y in YEARS:
            before = close[close.index <= fy_end_date(y)]
            if before.empty:
                continue
            price = float(before.iloc[-1])
            eps_y, dps_y = FIN.loc[y, "eps"], FIN.loc[y, "dps"]
            rows.append({"Year": y, "Price (₹)": price, "EPS (₹)": eps_y, "P/E (x)": price / eps_y,
                         "Market cap (₹ cr)": price * SHARES_OUTSTANDING_CR,
                         "Dividend yield (%)": dps_y / price * 100,
                         "Price / Book (x)": price / (FIN.loc[y, "total_equity"] / SHARES_OUTSTANDING_CR)})
        val = pd.DataFrame(rows)
        if not val.empty:
            c1, c2 = st.columns([1.1, 1], gap="large")
            with c1:
                fig = go.Figure(go.Bar(x=val["Year"], y=val["P/E (x)"], marker_color=GOLD,
                                       text=[f"{v:.0f}x" for v in val["P/E (x)"]], textposition="outside",
                                       textfont=dict(color=INK2), cliponaxis=False,
                                       hovertemplate="%{x}: P/E %{y:.1f}x<extra></extra>"))
                style_fig(fig, "Price-to-earnings at year-end", height=340, ysuffix="x", legend=False, hovermode="closest")
                show_chart(fig, "px_pe")
            with c2:
                show_table(val, hide_index=True, column_config={
                    "Price (₹)": st.column_config.NumberColumn(format="%.0f"),
                    "EPS (₹)": st.column_config.NumberColumn(format="%.2f"),
                    "P/E (x)": st.column_config.NumberColumn(format="%.1f"),
                    "Market cap (₹ cr)": st.column_config.NumberColumn(format="%.0f"),
                    "Dividend yield (%)": st.column_config.NumberColumn(format="%.2f"),
                    "Price / Book (x)": st.column_config.NumberColumn(format="%.1f"),
                })

        # ---- monthly returns heat-map ----
        section("Monthly returns", "Blue = month went up, red = month went down")
        try:
            monthly = close.resample("ME").last()
        except ValueError:
            monthly = close.resample("M").last()
        mret = monthly.pct_change() * 100
        mret = mret[mret.index >= pd.Timestamp(end.year - 7, 1, 1)]
        heat = pd.DataFrame({"year": mret.index.year, "month": mret.index.strftime("%b"), "ret": mret.values})
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        piv = heat.pivot(index="year", columns="month", values="ret").reindex(columns=months)
        zmax = float(np.nanpercentile(np.abs(piv.values), 95)) if piv.notna().any().any() else 10
        fig = go.Figure(go.Heatmap(
            z=piv.values, x=months, y=[str(y) for y in piv.index], zmid=0, zmin=-zmax, zmax=zmax,
            colorscale=[[0, "#D03B3B"], [0.5, "#383835"], [1, "#3987E5"]],
            text=[[("" if (isinstance(v, float) and math.isnan(v)) else f"{v:+.1f}%") for v in row] for row in piv.values],
            texttemplate="%{text}", textfont=dict(size=11, color="#FFFFFF"), xgap=2, ygap=2,
            hovertemplate="%{x} %{y}: %{z:+.1f}%<extra></extra>", colorbar=dict(ticksuffix="%", thickness=10),
        ))
        style_fig(fig, None, height=320, hovermode="closest")
        fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)", zeroline=False)
        show_chart(fig, "px_heat")

        # ---- what if I had invested? ----
        section("What if I had invested?", "Price growth only (dividends not included)")
        c1, c2, c3 = st.columns([1, 1, 2.2])
        with c1:
            amount = st.number_input("Amount invested (₹)", min_value=1000, value=100000, step=5000)
        with c2:
            default_start = (end - pd.DateOffset(years=5)).date()
            inv_date = st.date_input("Invested on", value=default_start,
                                     min_value=px_df.index.min().date(), max_value=end.date())
        bought = close[close.index >= pd.Timestamp(inv_date)]
        if len(bought) > 1:
            buy_px, now_px = float(bought.iloc[0]), float(close.iloc[-1])
            value_now = amount * now_px / buy_px
            yrs = (close.index[-1] - bought.index[0]).days / 365.25
            cards = [
                kpi("Titan investment today", f"₹{inr(value_now)}", note=f"Bought at ₹{inr(buy_px, 0)} on {bought.index[0]:%d %b %Y}"),
                kpi("Total gain", pct((value_now / amount - 1) * 100, 0),
                    note=f"CAGR {pct(cagr(buy_px, now_px, yrs))}" if yrs > 1 else None),
            ]
            if bench_df is not None:
                bb = bench_df["Close"][bench_df.index >= pd.Timestamp(inv_date)]
                if len(bb) > 1:
                    nifty_val = amount * float(bench_df["Close"].iloc[-1]) / float(bb.iloc[0])
                    cards.append(kpi(f"Same money in {BENCHMARK_NAME}", f"₹{inr(nifty_val)}",
                                     note=f"Gain {pct((nifty_val / amount - 1) * 100, 0)}"))
            with c3:
                kpi_row(cards)


# =====================================================================
# TAB 3: PROFIT & LOSS
# =====================================================================
with tab_pl:
    kpi_row([
        kpi(f"{REV_LABEL} · {LAST}", crore(M.loc[LAST, "rev_base"]), yoy("rev_base"),
            note=f"{pct(rev_cagr)} a year since {FIRST}"),
        kpi(f"EBITDA · {LAST}", crore(M.loc[LAST, "ebitda"]), yoy("ebitda"), note=f"Margin {pct(M.loc[LAST, 'ebitda_margin'])}"),
        kpi(f"Profit before tax · {LAST}", crore(M.loc[LAST, "pbt"]), yoy("pbt")),
        kpi(f"Net profit · {LAST}", crore(M.loc[LAST, "pat"]), yoy("pat"), note=f"{pct(pat_cagr)} a year since {FIRST}"),
        kpi(f"EPS · {LAST}", f"₹{M.loc[LAST, 'eps']:.2f}", yoy("eps")),
    ])

    c1, c2 = st.columns(2, gap="large")
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=SEL, y=M["core_revenue"], name="Core business", marker_color=GOLD,
                             marker_line=dict(color=SURFACE, width=1.5),
                             hovertemplate="Core business: ₹%{y:,.0f} cr<extra></extra>"))
        if not exclude_bullion:
            fig.add_trace(go.Bar(x=SEL, y=M["bullion_sales"], name="Bullion (gold bar) sales", marker_color=BLUE,
                                 marker_line=dict(color=SURFACE, width=1.5),
                                 hovertemplate="Bullion: ₹%{y:,.0f} cr<extra></extra>"))
        fig.add_trace(go.Scatter(x=SEL, y=M["rev_base"], mode="text", text=[inr(v) for v in M["rev_base"]],
                                 textposition="top center", textfont=dict(color=INK2, size=11), showlegend=False,
                                 hoverinfo="skip"))
        style_fig(fig, f"{REV_LABEL} (₹ crore)", height=380, legend=not exclude_bullion)
        fig.update_layout(barmode="stack")
        fig.update_yaxes(range=[0, M["rev_base"].max() * 1.15])
        show_chart(fig, "pl_rev")
    with c2:
        fig = go.Figure(go.Bar(x=SEL, y=M["pat"], marker_color=GOLD, text=[inr(v) for v in M["pat"]],
                               textposition="outside", textfont=dict(color=INK2, size=11), cliponaxis=False,
                               hovertemplate="%{x}: ₹%{y:,.0f} cr<extra>Net profit</extra>"))
        style_fig(fig, "Net profit after tax (₹ crore)", height=380, legend=False)
        fig.update_yaxes(range=[0, M["pat"].max() * 1.18])
        show_chart(fig, "pl_pat")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        fig = go.Figure()
        for col, name, color in [("gross_margin", "Gross margin", GOLD), ("ebitda_margin", "EBITDA margin", BLUE),
                                 ("pat_margin", "Net profit margin", AQUA)]:
            fig.add_trace(go.Scatter(x=SEL, y=M[col], name=name, mode="lines+markers",
                                     line=dict(color=color, width=2.2), marker=dict(size=8, line=dict(color=SURFACE, width=2)),
                                     hovertemplate=f"{name}: %{{y:.1f}}%<extra></extra>"))
        style_fig(fig, "Margins (% of revenue)", height=360, ysuffix="%")
        show_chart(fig, "pl_margin")
    with c2:
        gr = M[["revenue_growth", "pat_growth"]].dropna()
        fig = go.Figure()
        for col, name, color in [("revenue_growth", "Revenue growth", GOLD), ("pat_growth", "Net profit growth", BLUE)]:
            fig.add_trace(go.Bar(x=list(gr.index), y=gr[col], name=name, marker_color=color,
                                 hovertemplate=f"{name}: %{{y:+.1f}}%<extra></extra>"))
        style_fig(fig, "Year-on-year growth", height=360, ysuffix="%")
        show_chart(fig, "pl_growth")

    section("How revenue turns into profit", "Pick a year — each bar shows what is added or taken away on the way to net profit")
    wy = st.selectbox("Year", SEL[::-1], key="wf_year", format_func=lambda y: FY_LONG.get(y, y))
    r = FIN.loc[wy]
    ebitda_y = r["revenue"] - r["cogs"] - r["employee_cost"] - r["other_expenses"]
    steps = [
        ("Revenue", r["revenue"], "absolute"), ("Cost of goods", -r["cogs"], "relative"),
        ("Employee cost", -r["employee_cost"], "relative"), ("Other expenses", -r["other_expenses"], "relative"),
        ("EBITDA", ebitda_y, "total"), ("Other income", r["other_income"], "relative"),
        ("Depreciation", -r["depreciation"], "relative"), ("Interest", -r["finance_cost"], "relative"),
        ("One-offs & JV", r["share_of_jv"] - r["exceptional"], "relative"), ("Tax", -r["tax"], "relative"),
        ("Net profit", r["pat"], "total"),
    ]
    fig = go.Figure(go.Waterfall(
        x=[s[0] for s in steps], y=[0 if s[2] == "total" else s[1] for s in steps], measure=[s[2] for s in steps],
        text=[inr(s[1]) for s in steps], textposition="outside", textfont=dict(color=INK2, size=11),
        increasing=dict(marker=dict(color=AQUA)), decreasing=dict(marker=dict(color="#C9505A")),
        totals=dict(marker=dict(color=GOLD)), connector=dict(line=dict(color="rgba(237,230,216,0.25)", width=1)),
        hovertemplate="%{x}: ₹%{text} cr<extra></extra>", cliponaxis=False,
    ))
    style_fig(fig, f"{FY_LONG.get(wy, wy)}: from ₹{inr(r['revenue'])} cr revenue to ₹{inr(r['pat'])} cr profit",
              height=420, legend=False, hovermode="closest")
    show_chart(fig, "pl_waterfall")
    st.markdown('<div class="note">Gold bars are totals; red bars reduce profit; green bars add to it. '
                'Cost of goods = raw materials + purchases ± change in inventory.</div>', unsafe_allow_html=True)

    section("Common-size P&L", "Every line as a % of revenue — shows where each rupee of sales goes")
    cs = pd.DataFrame({
        "Cost of goods sold": M["cogs"] / M["revenue"] * 100,
        "Employee cost": M["employee_cost"] / M["revenue"] * 100,
        "Other expenses (incl. ads)": M["other_expenses"] / M["revenue"] * 100,
        "EBITDA": M["ebitda"] / M["revenue"] * 100,
        "Depreciation": M["depreciation"] / M["revenue"] * 100,
        "Interest": M["finance_cost"] / M["revenue"] * 100,
        "Tax": M["tax"] / M["revenue"] * 100,
        "Net profit": M["pat"] / M["revenue"] * 100,
    }).T
    show_table(cs, column_config={c: st.column_config.NumberColumn(format="%.1f%%") for c in cs.columns})


# =====================================================================
# TAB 4: SEGMENTS
# =====================================================================
with tab_seg:
    rev_seg = seg_table("revenue").loc[SEL]
    ebit_seg = seg_table("ebit", fold_corporate=False).loc[SEL]
    seg_names = list(SEGMENT_COLORS.keys())

    cards = []
    for s in seg_names:
        g = cagr(rev_seg.loc[FIRST, s], rev_seg.loc[LAST, s], N_YRS)
        share = rev_seg.loc[LAST, s] / rev_seg.loc[LAST].sum() * 100
        cards.append(kpi(f"{s} · {LAST}", crore(rev_seg.loc[LAST, s]),
                         note=f"{pct(share)} of total · grew {pct(g)} a year"))
    kpi_row(cards)

    c1, c2 = st.columns([1.35, 1], gap="large")
    with c1:
        fig = go.Figure()
        for s in seg_names:
            fig.add_trace(go.Bar(x=SEL, y=rev_seg[s], name=s, marker_color=SEGMENT_COLORS[s],
                                 marker_line=dict(color=SURFACE, width=1.5),
                                 hovertemplate=f"{s}: ₹%{{y:,.0f}} cr<extra></extra>"))
        style_fig(fig, "Revenue by segment (₹ crore, incl. other income)", height=420)
        fig.update_layout(barmode="stack")
        show_chart(fig, "seg_stack")
    with c2:
        mix_year = st.selectbox("Revenue mix for year", SEL[::-1], key="mix_year", format_func=lambda y: FY_LONG.get(y, y))
        mix = seg_table("revenue").loc[mix_year]
        fig = go.Figure(go.Pie(
            labels=mix.index, values=mix.values, hole=0.6, sort=False,
            marker=dict(colors=[SEGMENT_COLORS[s] for s in mix.index], line=dict(color=SURFACE, width=2)),
            textinfo="percent", textposition="inside", insidetextorientation="horizontal", textfont=dict(color="#FFFFFF", size=12),
            hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} cr<br>%{percent}<extra></extra>"))
        style_fig(fig, None, height=345, hovermode="closest")
        fig.update_layout(legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center", yanchor="top"))
        show_chart(fig, "seg_pie")

    fig = make_subplots(rows=1, cols=4, subplot_titles=seg_names, horizontal_spacing=0.05)
    for i, s in enumerate(seg_names, start=1):
        fig.add_trace(go.Bar(x=SEL, y=ebit_seg[s], name=s, marker_color=SEGMENT_COLORS[s], showlegend=False,
                             hovertemplate=f"{s} %{{x}}: ₹%{{y:,.0f}} cr<extra></extra>"), row=1, col=i)
    style_fig(fig, "Segment profit (EBIT, ₹ crore) — each segment on its own scale", height=330,
              legend=False, hovermode="closest")
    fig.update_annotations(font=dict(color=INK2, size=13))
    fig.update_layout(margin=dict(t=80))
    show_chart(fig, "seg_ebit")

    c1, c2 = st.columns([1.4, 1], gap="large")
    with c1:
        fig = go.Figure()
        for s in ["Jewellery", "Watches & Wearables", "EyeCare"]:
            margin = ebit_seg[s] / seg_table("revenue", fold_corporate=False).loc[SEL, s] * 100
            fig.add_trace(go.Scatter(x=SEL, y=margin, name=s, mode="lines+markers",
                                     line=dict(color=SEGMENT_COLORS[s], width=2.2),
                                     marker=dict(size=8, line=dict(color=SURFACE, width=2)),
                                     hovertemplate=f"{s}: %{{y:.1f}}%<extra></extra>"))
        style_fig(fig, "Segment EBIT margin (%)", height=380, ysuffix="%")
        show_chart(fig, "seg_margin")
    with c2:
        prof = ebit_seg[seg_names].loc[LAST].clip(lower=0)
        fig = go.Figure(go.Pie(
            labels=prof.index, values=prof.values, hole=0.6, sort=False,
            marker=dict(colors=[SEGMENT_COLORS[s] for s in prof.index], line=dict(color=SURFACE, width=2)),
            textinfo="percent", textposition="inside", insidetextorientation="horizontal",
            textfont=dict(color="#FFFFFF", size=12),
            hovertemplate="<b>%{label}</b><br>EBIT ₹%{value:,.0f} cr<br>%{percent}<extra></extra>"))
        style_fig(fig, f"Who earns the profit · {LAST}", height=380, hovermode="closest")
        fig.update_layout(legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center", yanchor="top"))
        show_chart(fig, "seg_profit_pie")
    st.markdown('<div class="note">Segment revenue includes other income, so the totals equal “total income”. '
                '“Others” = Taneira, SKINN, IRTH, TEAL (engineering & automation) and corporate income. '
                'Segment profit is before interest, tax and one-off items.</div>', unsafe_allow_html=True)

    section("The brand portfolio")
    st.markdown(
        f"""<div class="brand-grid">
        <div class="brand"><div class="b-head"><span class="b-dot" style="background:{GOLD}"></span>Jewellery</div>
          <div class="b-names">Tanishq · Mia · Zoya · CaratLane · beYon (lab-grown diamonds) · Damas (GCC, 67% owned since Jan 2026)</div></div>
        <div class="brand"><div class="b-head"><span class="b-dot" style="background:{BLUE}"></span>Watches & Wearables</div>
          <div class="b-names">Titan · Fastrack · Sonata · Raga · Edge · Xylys · Nebula · smart watches; sold via Titan World, Helios & Helios Luxe</div></div>
        <div class="brand"><div class="b-head"><span class="b-dot" style="background:{AQUA}"></span>EyeCare</div>
          <div class="b-names">Titan Eye+ stores · Fastrack & Titan eyewear · sunglasses · lenses</div></div>
        <div class="brand"><div class="b-head"><span class="b-dot" style="background:{VIOLET}"></span>Others / Emerging</div>
          <div class="b-names">Taneira (sarees) · SKINN (fragrances) · IRTH (women's bags) · TEAL (aerospace, defence & automation)</div></div>
        </div>""",
        unsafe_allow_html=True,
    )

    section("Segment table", f"₹ crore · growth is the yearly average (CAGR) from {FIRST} to {LAST}")
    tbl = seg_table("revenue", fold_corporate=False).loc[SEL].T
    tbl[f"CAGR {FIRST}–{LAST}"] = [cagr(tbl.loc[s, FIRST], tbl.loc[s, LAST], N_YRS) for s in tbl.index]
    show_table(tbl, column_config={**{y: st.column_config.NumberColumn(format="%.0f") for y in SEL},
                                   f"CAGR {FIRST}–{LAST}": st.column_config.NumberColumn(format="%.1f%%")})


# =====================================================================
# TAB 5: BALANCE SHEET & CASH FLOW
# =====================================================================
with tab_bs:
    kpi_row([
        kpi(f"Shareholders' equity · {LAST}", crore(M.loc[LAST, "total_equity"]), yoy("total_equity"),
            note=f"Book value ₹{M.loc[LAST, 'bvps']:.0f} per share"),
        kpi(f"Inventory · {LAST}", crore(M.loc[LAST, "inventories"]), yoy("inventories"), good_when_up=False,
            note=f"{M.loc[LAST, 'inventory_days']:.0f} days of cost of sales"),
        kpi(f"Borrowings · {LAST}", crore(M.loc[LAST, "borrowings"]), yoy("borrowings"), good_when_up=False,
            note=f"+ gold on loan {crore(M.loc[LAST, 'gold_on_loan'])}"),
        kpi(f"Operating cash flow · {LAST}", crore(M.loc[LAST, "cfo"]), note=f"Free cash flow {crore(M.loc[LAST, 'fcf'])}"),
        kpi(f"Cash & liquid investments · {LAST}", crore(M.loc[LAST, "liquid_funds"])),
    ])

    c1, c2 = st.columns(2, gap="large")
    with c1:
        fig = go.Figure()
        for col, name, color in [("total_equity", "Shareholders' equity", GOLD), ("borrowings", "Borrowings", BLUE),
                                 ("gold_on_loan", "Gold on loan", AQUA), ("lease_liabilities", "Lease liabilities", VIOLET)]:
            fig.add_trace(go.Bar(x=SEL, y=M[col], name=name, marker_color=color, marker_line=dict(color=SURFACE, width=1.5),
                                 hovertemplate=f"{name}: ₹%{{y:,.0f}} cr<extra></extra>"))
        style_fig(fig, "How Titan funds itself (₹ crore)", height=400)
        fig.update_layout(barmode="stack")
        show_chart(fig, "bs_funding")
    with c2:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=SEL, y=M["inventories"], name="Inventory", marker_color=GOLD,
                             hovertemplate="Inventory: ₹%{y:,.0f} cr<extra></extra>"))
        fig.add_trace(go.Bar(x=SEL, y=M["liquid_funds"], name="Cash & liquid investments", marker_color=BLUE,
                             hovertemplate="Cash & investments: ₹%{y:,.0f} cr<extra></extra>"))
        fig.add_trace(go.Bar(x=SEL, y=M["ppe"], name="Property, plant & equipment", marker_color=AQUA,
                             hovertemplate="PPE: ₹%{y:,.0f} cr<extra></extra>"))
        style_fig(fig, "Key assets (₹ crore)", height=400)
        fig.update_layout(barmode="group")
        show_chart(fig, "bs_assets")
    st.markdown('<div class="note"><b>Gold on loan</b>: Titan borrows physical gold from banks instead of buying it, '
                'which protects it from gold-price swings. It works like debt, so it is shown separately. '
                'The dip in equity in FY24 is because ₹4,621 cr paid to buy out CaratLane minority shareholders was '
                'adjusted against reserves.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        fig = go.Figure()
        for col, name, color in [("cfo", "Operating", GOLD), ("cfi", "Investing", BLUE), ("cff", "Financing", AQUA)]:
            fig.add_trace(go.Bar(x=SEL, y=M[col], name=name, marker_color=color,
                                 hovertemplate=f"{name}: ₹%{{y:,.0f}} cr<extra></extra>"))
        style_fig(fig, "Cash flows (₹ crore)", height=380)
        fig.update_layout(barmode="group")
        show_chart(fig, "cf_main")
    with c2:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=SEL, y=M["pat"], name="Net profit", marker_color=GOLD,
                             hovertemplate="Net profit: ₹%{y:,.0f} cr<extra></extra>"))
        fig.add_trace(go.Bar(x=SEL, y=M["cfo"], name="Operating cash flow", marker_color=BLUE,
                             hovertemplate="Operating cash flow: ₹%{y:,.0f} cr<extra></extra>"))
        fig.add_trace(go.Bar(x=SEL, y=M["fcf"], name="Free cash flow", marker_color=AQUA,
                             hovertemplate="Free cash flow: ₹%{y:,.0f} cr<extra></extra>"))
        style_fig(fig, "Profit vs actual cash generated (₹ crore)", height=380)
        fig.update_layout(barmode="group")
        show_chart(fig, "cf_quality")
    st.markdown(f'<div class="note">Free cash flow = operating cash flow − capex. Across {FIRST}–{LAST}, '
                f'Titan earned {crore(cum_pat)} of profit but generated {crore(cum_cfo)} of operating cash — '
                f'most of the gap went into building up jewellery inventory as the business (and the gold price) grew.</div>',
                unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        fig = go.Figure(go.Bar(x=SEL, y=M["dps"], marker_color=GOLD, text=[f"₹{v:g}" for v in M["dps"]],
                               textposition="outside", textfont=dict(color=INK2), cliponaxis=False,
                               hovertemplate="%{x}: ₹%{y} per share<extra>Dividend</extra>"))
        style_fig(fig, "Dividend per share (₹)", height=340, legend=False, yprefix="₹")
        fig.update_yaxes(range=[0, M["dps"].max() * 1.22])
        show_chart(fig, "div_dps")
    with c2:
        fig = go.Figure(go.Scatter(x=SEL, y=M["inventory_days"], mode="lines+markers+text",
                                   text=[f"{v:.0f}" for v in M["inventory_days"]], textposition="top center",
                                   textfont=dict(color=INK2, size=11),
                                   line=dict(color=GOLD, width=2.2), marker=dict(size=8, line=dict(color=SURFACE, width=2)),
                                   hovertemplate="%{x}: %{y:.0f} days<extra>Inventory days</extra>"))
        style_fig(fig, "Inventory days (how long stock sits before it is sold)", height=340, legend=False)
        fig.update_yaxes(range=[0, M["inventory_days"].max() * 1.2])
        show_chart(fig, "bs_invdays")


# =====================================================================
# TAB 6: RATIOS & HEALTH CHECK
# =====================================================================
RATIOS = {
    # name: (column, unit, higher_is_better, what it means)
    "Return on equity (ROE)": ("roe", "%", True, "Net profit ÷ average shareholders' equity. How much profit each ₹100 of owners' money earns."),
    "Return on capital employed (ROCE)": ("roce", "%", True, "EBIT ÷ average (equity + borrowings + gold on loan + leases). Return on all money used in the business."),
    "Return on assets (ROA)": ("roa", "%", True, "Net profit ÷ total assets."),
    "Gross margin": ("gross_margin", "%", True, "(Revenue − cost of goods) ÷ revenue."),
    "EBITDA margin": ("ebitda_margin", "%", True, "Operating profit before depreciation, interest & tax ÷ revenue."),
    "Net profit margin": ("pat_margin", "%", True, "Net profit ÷ revenue."),
    "Debt-to-equity (borrowings only)": ("debt_equity", "x", False, "Bank borrowings ÷ equity."),
    "Debt-to-equity (incl. gold loan & leases)": ("debt_equity_all", "x", False, "(Borrowings + gold on loan + lease liabilities) ÷ equity."),
    "Interest coverage": ("interest_coverage", "x", True, "EBIT ÷ interest cost. How many times profit covers interest."),
    "Current ratio": ("current_ratio", "x", True, "Current assets ÷ current liabilities. Short-term paying ability."),
    "Inventory days": ("inventory_days", " days", False, "Inventory ÷ cost of goods sold × 365."),
    "Receivable days": ("receivable_days", " days", False, "Trade receivables ÷ revenue × 365."),
    "Asset turnover": ("asset_turnover", "x", True, "Revenue ÷ total assets."),
    "Cash conversion (CFO ÷ PAT)": ("cash_conversion", "%", True, "Operating cash flow as a % of net profit."),
    "Dividend payout": ("payout_ratio", "%", None, "Dividend per share ÷ EPS."),
    "Effective tax rate": ("tax_rate", "%", None, "Tax ÷ profit before tax."),
    "EPS (₹)": ("eps", "₹", True, "Net profit per share."),
    "Book value per share (₹)": ("bvps", "₹", True, "Equity ÷ number of shares."),
}


def fmt_ratio(v, unit):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    if unit == "%":
        return f"{v:.1f}%"
    if unit == "x":
        return f"{v:.2f}x"
    if unit == "₹":
        return f"₹{v:.2f}"
    return f"{v:.0f}{unit}"


with tab_ratio:
    # ---------- health check scorecard ----------
    section("Financial health check", f"Simple pass / watch / fail tests on {FIRST}–{LAST} (rules of thumb, not investment advice)")

    def grade(value, good, okay, higher_better=True):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return "watch"
        if higher_better:
            return "pass" if value >= good else ("watch" if value >= okay else "fail")
        return "pass" if value <= good else ("watch" if value <= okay else "fail")

    inv_change = (M.loc[LAST, "inventory_days"] / M.loc[FIRST, "inventory_days"] - 1) * 100
    checks = [
        ("Profitable every year", "Yes" if not loss_years else f"Loss in {len(loss_years)} yr",
         "pass" if not loss_years else "fail", "Net profit was positive in every year of the range."),
        ("Revenue growth (CAGR)", pct(rev_cagr), grade(rev_cagr, 15, 8), "Pass ≥ 15% a year · watch 8–15%."),
        ("Profit growth (CAGR)", pct(pat_cagr), grade(pat_cagr, 15, 8), "Pass ≥ 15% a year · watch 8–15%."),
        (f"Return on equity ({LAST})", pct(M.loc[LAST, "roe"]), grade(M.loc[LAST, "roe"], 20, 12), "Pass ≥ 20% · watch 12–20%."),
        (f"ROCE ({LAST})", pct(M.loc[LAST, "roce"]), grade(M.loc[LAST, "roce"], 15, 10), "Pass ≥ 15% · watch 10–15%."),
        (f"Interest coverage ({LAST})", fmt_ratio(M.loc[LAST, "interest_coverage"], "x"),
         grade(M.loc[LAST, "interest_coverage"], 5, 2), "Pass ≥ 5x · watch 2–5x."),
        (f"Debt-to-equity ({LAST})", fmt_ratio(M.loc[LAST, "debt_equity"], "x"),
         grade(M.loc[LAST, "debt_equity"], 1, 2, higher_better=False), "Bank borrowings only. Pass ≤ 1x · watch 1–2x."),
        ("Cash conversion (total CFO ÷ total PAT)", pct(cum_cfo / cum_pat * 100, 0),
         grade(cum_cfo / cum_pat * 100, 80, 40), "Pass ≥ 80% · watch 40–80%. Gold inventory build-up eats cash."),
        ("Inventory days trend", f"{inv_change:+.0f}%", grade(inv_change, 10, 30, higher_better=False),
         f"Change from {FIRST} to {LAST}. Rising days = stock sits longer."),
        ("Dividend every year", "Yes" if (M["dps"] > 0).all() else "No",
         "pass" if (M["dps"] > 0).all() else "watch", "Paid a dividend in every year of the range."),
    ]
    icon = {"pass": ("✅", GOOD, "Pass"), "watch": ("⚠️", WARN, "Watch"), "fail": ("❌", BAD, "Fail")}
    score = sum(1 for c in checks if c[2] == "pass")
    rows_html = "".join(
        f'<div class="score-row"><div>{icon[g][0]}</div><div class="s-name">{n}</div>'
        f'<div class="s-val">{v} <span style="color:{icon[g][1]};font-size:0.75rem;font-weight:700">{icon[g][2]}</span></div>'
        f'<div class="s-why">{why}</div></div>'
        for n, v, g, why in checks
    )
    c1, c2 = st.columns([2.3, 1], gap="large")
    with c1:
        st.markdown(f'<div class="card" style="padding:4px 4px">{rows_html}</div>', unsafe_allow_html=True)
    with c2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=score, number=dict(suffix=f" / {len(checks)}", font=dict(color=INK, size=36)),
            gauge=dict(axis=dict(range=[0, len(checks)], tickcolor=MUTED, tickfont=dict(color=MUTED)),
                       bar=dict(color=ACCENT, thickness=0.28), bgcolor="rgba(255,255,255,0.04)", borderwidth=0,
                       steps=[dict(range=[0, len(checks) * 0.5], color="rgba(208,59,59,0.18)"),
                              dict(range=[len(checks) * 0.5, len(checks) * 0.75], color="rgba(250,178,25,0.16)"),
                              dict(range=[len(checks) * 0.75, len(checks)], color="rgba(12,163,12,0.18)")]),
        ))
        style_fig(fig, "Health score", height=280, legend=False, hovermode=False)
        fig.update_layout(margin=dict(l=30, r=30, t=60, b=10))
        show_chart(fig, "health_gauge")
        verdict = ("Financially strong" if score >= 8 else "Healthy with some watch-points" if score >= 6
                   else "Mixed picture" if score >= 4 else "Weak")
        st.markdown(f'<div class="card"><h4>{verdict}</h4><p>Titan passes {score} of {len(checks)} tests. '
                    f'Profitability and returns are excellent; the main watch-points are cash tied up in gold '
                    f'inventory and rising gold-linked borrowings.</p></div>', unsafe_allow_html=True)

    # ---------- ratio explorer ----------
    section("Ratio explorer", "Pick any ratio to see how it moved")
    rname = st.selectbox("Ratio", list(RATIOS.keys()), index=0, key="ratio_pick")
    col, unit, hib, meaning = RATIOS[rname]
    c1, c2 = st.columns([2.2, 1], gap="large")
    with c1:
        fig = go.Figure(go.Scatter(
            x=SEL, y=M[col], mode="lines+markers+text", text=[fmt_ratio(v, unit) for v in M[col]],
            textposition="top center", textfont=dict(color=INK2, size=11),
            line=dict(color=GOLD, width=2.4), marker=dict(size=9, line=dict(color=SURFACE, width=2)),
            hovertemplate="%{x}: %{text}<extra></extra>"))
        style_fig(fig, rname, height=360, legend=False)
        lo_v, hi_v = float(np.nanmin(M[col])), float(np.nanmax(M[col]))
        pad = (hi_v - lo_v) * 0.25 or abs(hi_v) * 0.2 or 1
        fig.update_yaxes(range=[min(0, lo_v - pad), hi_v + pad])
        show_chart(fig, "ratio_line")
    with c2:
        trend = M[col].iloc[-1] - M[col].iloc[0]
        direction = "improved" if (hib and trend > 0) or (hib is False and trend < 0) else (
            "weakened" if hib is not None else "changed")
        st.markdown(f'<div class="card"><h4>What it means</h4><p>{meaning}</p>'
                    f'<p><b>{FIRST}:</b> {fmt_ratio(M[col].iloc[0], unit)} &nbsp;→&nbsp; <b>{LAST}:</b> {fmt_ratio(M[col].iloc[-1], unit)}'
                    f'<br>The ratio has <b>{direction}</b> over the period.</p></div>', unsafe_allow_html=True)

    # ---------- compare two years ----------
    section("Compare any two years")
    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        ya = st.selectbox("From", YEARS, index=0, key="cmp_a", format_func=lambda y: FY_LONG.get(y, y))
    with c2:
        yb = st.selectbox("To", YEARS, index=len(YEARS) - 1, key="cmp_b", format_func=lambda y: FY_LONG.get(y, y))
    cmp_items = [("Revenue", "rev_base"), ("EBITDA", "ebitda"), ("Net profit", "pat"), ("EPS (₹)", "eps"),
                 ("Total equity", "total_equity"), ("Inventory", "inventories"), ("Borrowings", "borrowings"),
                 ("Operating cash flow", "cfo")]
    cmp_cards = []
    for name, c in cmp_items:
        a, b = M_ALL.loc[ya, c], M_ALL.loc[yb, c]
        chg = (b / a - 1) * 100 if a > 0 else None
        val = f"₹{b:.2f}" if c == "eps" else crore(b)
        good_up = c not in ("inventories", "borrowings")
        d = ""
        if chg is not None:
            color = GOOD if (chg >= 0) == good_up else BAD
            d = f'<div class="k-delta" style="color:{color}">{"▲" if chg >= 0 else "▼"} {abs(chg):.0f}% <span>vs {ya}</span></div>'
        prev_txt = f"₹{a:.2f}" if c == "eps" else crore(a)
        cmp_cards.append(f'<div class="kpi"><div class="k-label">{name} · {yb}</div><div class="k-value">{val}</div>{d}'
                         f'<div class="k-note">{ya}: {prev_txt}</div></div>')
    kpi_row(cmp_cards)

    # ---------- full ratio table ----------
    section("All ratios", "Values for every year in the selected range")
    ratio_tbl = pd.DataFrame({name: [fmt_ratio(M.loc[y, c], u) for y in SEL] for name, (c, u, _, _) in RATIOS.items()},
                             index=SEL).T
    show_table(ratio_tbl)
    st.markdown('<div class="note">ROE and ROCE use the average of opening and closing balances '
                f'(for {YEARS[0]} the closing balance is used). EBIT = profit before tax + interest + exceptional items.</div>',
                unsafe_allow_html=True)


# =====================================================================
# TAB: FORECAST (scenario + statistical trend) - maths lives in forecast.py
# =====================================================================
FC_KEYS = {"growth": "fc_growth", "fade": "fc_fade", "ebitda": "fc_ebitda", "tax": "fc_tax", "payout": "fc_payout"}
ADV_KEYS = {"dep": "fc_dep", "interest": "fc_interest", "other_income": "fc_oi"}


def _apply_preset():
    name = st.session_state.get("fc_preset", "Base")
    if name in fc.SCENARIOS:
        for k, key in FC_KEYS.items():
            st.session_state[key] = float(fc.SCENARIOS[name][k])
        for k, key in ADV_KEYS.items():
            st.session_state[key] = float(fc.ADVANCED_DEFAULTS[k])


def _mark_custom():
    st.session_state["fc_preset"] = "Custom"


if "fc_preset" not in st.session_state:
    st.session_state["fc_preset"] = "Base"
    _apply_preset()

with tab_fc:
    st.markdown(
        """<div class="sc-hero"><h2>🔮 Forecast — Titan FY27 to FY31</h2>
        <p>Pick a scenario or move the sliders: the projected revenue, profit, EPS and dividend update instantly.
        Forecasts start from FY26 revenue <b>excluding bullion</b> (gold-bar) sales. These are model estimates for
        learning — not predictions you should invest on.</p></div>""", unsafe_allow_html=True)

    hist_core = CORE_REVENUE
    n_hist = len(YEARS) - 1
    ref_cagr = cagr(hist_core.iloc[0], hist_core.iloc[-1], n_hist)
    ref_cagr3 = cagr(hist_core.iloc[-4], hist_core.iloc[-1], 3)
    hist_margin = (M_ALL["ebitda"] / hist_core * 100)

    # ---------- controls ----------
    c1, c2 = st.columns([1.6, 1])
    with c1:
        st.radio("Scenario", ["Bear", "Base", "Bull", "Custom"], key="fc_preset", horizontal=True,
                 on_change=_apply_preset,
                 help="Bear / Base / Bull load ready-made assumptions. Moving any slider switches to Custom.")
    with c2:
        n_ahead = st.slider("Years to forecast", 1, 5, 5, key="fc_years")
    if st.session_state["fc_preset"] in fc.SCENARIOS:
        st.markdown(f'<div class="note">📌 {fc.SCENARIO_NOTES[st.session_state["fc_preset"]]}</div>',
                    unsafe_allow_html=True)

    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.slider("Revenue growth, first year (%)", 0.0, 40.0, step=0.5, key="fc_growth", on_change=_mark_custom,
                  help=f"History: {ref_cagr:.1f}% a year over FY20–FY26, {ref_cagr3:.1f}% over the last 3 years.")
    with s2:
        st.slider("Growth slows by (pts / year)", 0.0, 5.0, step=0.5, key="fc_fade", on_change=_mark_custom,
                  help="Big companies usually grow a bit slower each year. 1 = 18%, 17%, 16% …")
    with s3:
        st.slider("EBITDA margin (%)", 6.0, 16.0, step=0.1, key="fc_ebitda", on_change=_mark_custom,
                  help=f"FY26 actual: {hist_margin.iloc[-1]:.1f}% · 7-year average: {hist_margin.mean():.1f}% (on revenue excl. bullion).")
    with s4:
        st.slider("Tax rate (%)", 18.0, 32.0, step=0.5, key="fc_tax", on_change=_mark_custom,
                  help=f"FY26 actual: {M_ALL.loc[YEARS[-1], 'tax_rate']:.1f}%")
    with s5:
        st.slider("Dividend payout (%)", 0.0, 60.0, step=1.0, key="fc_payout", on_change=_mark_custom,
                  help=f"FY26 actual: {M_ALL.loc[YEARS[-1], 'payout_ratio']:.0f}% of EPS")
    with st.expander("Advanced: smaller costs as % of revenue"):
        a1, a2, a3 = st.columns(3)
        with a1:
            st.slider("Depreciation (%)", 0.5, 2.0, step=0.05, key="fc_dep", on_change=_mark_custom)
        with a2:
            st.slider("Interest cost (%)", 0.5, 3.0, step=0.05, key="fc_interest", on_change=_mark_custom)
        with a3:
            st.slider("Other income (%)", 0.0, 1.5, step=0.05, key="fc_oi", on_change=_mark_custom)

    ss = st.session_state
    mine = fc.scenario_forecast(FC_BASE, n_ahead, ss.fc_growth, ss.fc_fade, ss.fc_ebitda, ss.fc_tax, ss.fc_payout,
                                dep=ss.fc_dep, interest=ss.fc_interest, other_income=ss.fc_oi,
                                shares_cr=SHARES_OUTSTANDING_CR, last_fy=YEARS[-1])
    rng = preset_forecasts(n_ahead)
    bear, bull = rng["Bear"], rng["Bull"]
    fy_end = mine.index[-1]
    last = YEARS[-1]

    kpi_row([
        kpi(f"Revenue excl. bullion · {fy_end}E", crore(mine.loc[fy_end, "revenue"]),
            note=f"{pct(cagr(hist_core.iloc[-1], mine.loc[fy_end, 'revenue'], n_ahead))} a year from {last}"),
        kpi(f"Net profit · {fy_end}E", crore(mine.loc[fy_end, "pat"]),
            note=f"{pct(cagr(FIN.loc[last, 'pat'], mine.loc[fy_end, 'pat'], n_ahead))} a year from {last}"),
        kpi(f"EPS · {fy_end}E", f"₹{mine.loc[fy_end, 'eps']:.1f}", note=f"{last} actual ₹{FIN.loc[last, 'eps']:.2f}"),
        kpi(f"Dividend / share · {fy_end}E", f"₹{mine.loc[fy_end, 'dps']:.1f}", note=f"{last} actual ₹{FIN.loc[last, 'dps']:g}"),
        kpi(f"Net margin · {fy_end}E", pct(mine.loc[fy_end, "pat_margin"]),
            note=f"{last} actual {pct(FIN.loc[last, 'pat'] / hist_core.iloc[-1] * 100)}"),
    ])

    def fc_bar_chart(hist_vals, col, title, decimals=0):
        fig = go.Figure()
        fig.add_trace(go.Bar(x=YEARS, y=hist_vals, name="Actual", marker_color=GOLD,
                             hovertemplate="%{x}: ₹%{y:,.0f} cr<extra>Actual</extra>"))
        err_hi = np.clip(bull[col].values - mine[col].values, 0, None)
        err_lo = np.clip(mine[col].values - bear[col].values, 0, None)
        fig.add_trace(go.Bar(
            x=list(mine.index), y=mine[col], name="Forecast (your scenario)", marker_color="rgba(212,175,55,0.55)",
            marker_pattern=dict(shape="/", fgcolor=SURFACE, solidity=0.3),
            error_y=dict(type="data", symmetric=False, array=err_hi, arrayminus=err_lo, color=INK2, thickness=1.2,
                         width=6),
            customdata=np.stack([bear[col].values, bull[col].values], axis=1),
            hovertemplate="%{x}E: ₹%{y:,.0f} cr<br>Bear–Bull: ₹%{customdata[0]:,.0f} – ₹%{customdata[1]:,.0f} cr"
                          "<extra>Forecast</extra>"))
        fig.add_vline(x=len(YEARS) - 0.5, line=dict(color="rgba(212,175,55,0.5)", width=1, dash="dot"))
        fig.add_annotation(x=len(YEARS) - 0.5, y=1.0, yref="paper", text="forecast →", showarrow=False,
                           xanchor="left", font=dict(color=MUTED, size=11))
        style_fig(fig, title, height=380, hovermode="closest")
        fig.update_layout(barmode="overlay")
        return fig

    c1, c2 = st.columns(2, gap="large")
    with c1:
        show_chart(fc_bar_chart(hist_core.values, "revenue", "Revenue excl. bullion (₹ crore)"), "fc_rev")
    with c2:
        show_chart(fc_bar_chart(FIN["pat"].values, "pat", "Net profit (₹ crore)"), "fc_pat")
    st.markdown('<div class="note">Striped bars = your forecast. The thin whiskers show the range between the '
                '<b>Bear</b> and <b>Bull</b> scenarios.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1.2, 1], gap="large")
    with c1:
        fig = go.Figure()
        fx = list(mine.index)
        fig.add_trace(go.Scatter(x=fx + fx[::-1], y=list(bull["eps"]) + list(bear["eps"])[::-1], fill="toself",
                                 mode="lines", fillcolor="rgba(212,175,55,0.12)", line=dict(width=0), hoverinfo="skip",
                                 name="Bear–Bull range"))
        fig.add_trace(go.Scatter(x=YEARS, y=FIN["eps"], name="Actual EPS", mode="lines+markers",
                                 line=dict(color=GOLD, width=2.4), marker=dict(size=8, line=dict(color=SURFACE, width=2)),
                                 hovertemplate="%{x}: ₹%{y:.2f}<extra>Actual</extra>"))
        fig.add_trace(go.Scatter(x=[YEARS[-1]] + fx, y=[FIN.loc[last, "eps"]] + list(mine["eps"]),
                                 name="Forecast EPS", mode="lines+markers", line=dict(color=ACCENT, width=2.4, dash="dash"),
                                 marker=dict(size=8, line=dict(color=SURFACE, width=2)),
                                 hovertemplate="%{x}: ₹%{y:.1f}<extra>Forecast</extra>"))
        style_fig(fig, "Earnings per share (₹)", height=360, yprefix="₹")
        fig.update_xaxes(categoryorder="array", categoryarray=YEARS + fx)
        show_chart(fig, "fc_eps")
    with c2:
        tbl = pd.DataFrame({
            "Revenue growth": [f"{v:.1f}%" for v in mine["growth"]],
            "Revenue (₹ cr)": [inr(v) for v in mine["revenue"]],
            "EBITDA (₹ cr)": [inr(v) for v in mine["ebitda"]],
            "Net profit (₹ cr)": [inr(v) for v in mine["pat"]],
            "Net margin": [f"{v:.1f}%" for v in mine["pat_margin"]],
            "EPS (₹)": [f"{v:.1f}" for v in mine["eps"]],
            "Dividend (₹)": [f"{v:.1f}" for v in mine["dps"]],
        }, index=[f"{y}E" for y in mine.index]).T
        section("Forecast table", "E = estimate")
        show_table(tbl)

    # ---------- what could the share be worth? ----------
    section("What could the share be worth?", "Simple maths: forecast EPS × a P/E multiple you choose (illustrative only)")
    live = bot_price_info()
    cur_pe = live["pe"] if live else 60.0
    c1, c2 = st.columns([1, 2.2], gap="large")
    with c1:
        pe_pick = st.slider("P/E multiple", 20, 100, int(min(max(round(cur_pe / 5) * 5, 20), 100)), step=5,
                            key="fc_pe", help="How many times yearly earnings investors pay. Titan has usually "
                                              "traded at a high P/E because of its steady growth.")
        if live:
            st.markdown(f'<div class="note">Today: ₹{inr(live["last"], 0)} per share, which is '
                        f'{live["pe"]:.0f}× {last} EPS.</div>', unsafe_allow_html=True)
        st.markdown('<div class="note">This is a classroom illustration, not a price target or investment advice.</div>',
                    unsafe_allow_html=True)
    with c2:
        implied = mine["eps"] * pe_pick
        fig = go.Figure(go.Bar(x=[f"{y}E" for y in mine.index], y=implied, marker_color=GOLD,
                               text=[f"₹{inr(v)}" for v in implied], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK2, size=11),
                               hovertemplate="%{x}: ₹%{y:,.0f} per share<extra></extra>"))
        if live:
            fig.add_hline(y=live["last"], line=dict(color=BLUE, width=1.5, dash="dot"),
                          annotation_text=f"today ₹{inr(live['last'], 0)}", annotation_position="top left",
                          annotation_font=dict(color=BLUE, size=11))
        style_fig(fig, f"Implied value per share at {pe_pick}× earnings", height=320, legend=False, yprefix="₹",
                  hovermode="closest")
        fig.update_yaxes(range=[0, max(implied.max(), live["last"] if live else 0) * 1.2])
        show_chart(fig, "fc_value")

    # ---------- sensitivity ----------
    section("Sensitivity: what matters most?",
            f"Net profit in {fy_end}E (₹ crore) if growth or margin turn out different — your other settings stay the same")
    g0, m0 = ss.fc_growth, ss.fc_ebitda
    g_list = [g0 + d for d in (-8, -4, 0, 4, 8)]
    m_list = [round(m0 + d, 1) for d in (-1.2, -0.6, 0, 0.6, 1.2)]
    grid = np.array([[fc.scenario_forecast(FC_BASE, n_ahead, g, ss.fc_fade, m, ss.fc_tax, ss.fc_payout,
                                           dep=ss.fc_dep, interest=ss.fc_interest, other_income=ss.fc_oi,
                                           shares_cr=SHARES_OUTSTANDING_CR, last_fy=last)["pat"].iloc[-1]
                      for m in m_list] for g in g_list])
    text = [[("★ " if (i == 2 and j == 2) else "") + inr(v) for j, v in enumerate(row)] for i, row in enumerate(grid)]
    fig = go.Figure(go.Heatmap(
        z=grid, x=[f"{m:.1f}%" for m in m_list], y=[f"{g:.1f}%" for g in g_list], text=text, texttemplate="%{text}",
        textfont=dict(size=12, color="#FFFFFF"), xgap=3, ygap=3,
        colorscale=[[0, "#2A2216"], [0.5, "#7A5A1C"], [1, "#D4AF37"]], showscale=False,
        hovertemplate="Growth %{y}, EBITDA margin %{x}<br>Net profit ₹%{z:,.0f} cr<extra></extra>"))
    style_fig(fig, None, height=330, legend=False, hovermode="closest")
    fig.update_xaxes(title=dict(text="EBITDA margin →", font=dict(color=MUTED, size=12)), side="bottom")
    fig.update_yaxes(title=dict(text="First-year revenue growth →", font=dict(color=MUTED, size=12)),
                     gridcolor="rgba(0,0,0,0)", zeroline=False, autorange="reversed")
    show_chart(fig, "fc_sens")
    st.markdown('<div class="note">★ = your current scenario. Brighter = more profit.</div>', unsafe_allow_html=True)

    # ---------- statistical trend ----------
    section("Statistical trend forecast", "No assumptions — just extends the past growth trend (log-linear regression) with an 80% range")
    c1, c2, c3 = st.columns([1.3, 1.2, 1.5])
    with c1:
        t_metric = st.selectbox("Metric", ["Revenue excl. bullion", "Net profit", "EPS"], key="fc_tmetric")
    with c2:
        drop_covid = st.toggle("Leave out FY21 (COVID year)", value=True, key="fc_dropcovid",
                               help="FY21 was distorted by lockdowns, so it can bend the trend.")
    series = {"Revenue excl. bullion": hist_core, "Net profit": FIN["pat"], "EPS": FIN["eps"]}[t_metric]
    hist_fit, tfc, info = fc.trend_forecast(series, n_ahead, exclude=("FY21",) if drop_covid else ())
    with c3:
        st.markdown(f'<div class="note" style="padding-top:6px">Trend growth: <b style="color:#F1DFA6">'
                    f'{info["growth"]:.1f}% a year</b> · fit quality R² = {info["r2"]:.2f} '
                    f'(1.0 = perfect) · based on {info["n"]} years.</div>', unsafe_allow_html=True)
    is_money = t_metric != "EPS"
    unit = "₹%{y:,.0f} cr" if is_money else "₹%{y:,.2f}"
    rfmt = ",.0f" if is_money else ",.1f"
    fig = go.Figure()
    fx = list(tfc.index)
    fig.add_trace(go.Scatter(x=fx + fx[::-1], y=list(tfc["high"]) + list(tfc["low"])[::-1], fill="toself",
                             mode="lines", fillcolor="rgba(57,135,229,0.14)", line=dict(width=0), hoverinfo="skip",
                             name="80% range"))
    fig.add_trace(go.Scatter(x=YEARS, y=hist_fit["trend"], name="Trend line", mode="lines",
                             line=dict(color="rgba(237,230,216,0.35)", width=1.5, dash="dot"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=YEARS, y=hist_fit["actual"], name="Actual", mode="lines+markers",
                             line=dict(color=GOLD, width=2.4), marker=dict(size=8, line=dict(color=SURFACE, width=2)),
                             hovertemplate=f"%{{x}}: {unit}<extra>Actual</extra>"))
    fig.add_trace(go.Scatter(x=[YEARS[-1]] + fx, y=[hist_fit["trend"].iloc[-1]] + list(tfc["forecast"]),
                             name="Trend forecast", mode="lines+markers", line=dict(color=BLUE, width=2.4, dash="dash"),
                             marker=dict(size=8, line=dict(color=SURFACE, width=2)),
                             customdata=np.stack([[np.nan] + list(tfc["low"]), [np.nan] + list(tfc["high"])], axis=1),
                             hovertemplate=f"%{{x}}: {unit}<br>80% range: %{{customdata[0]:{rfmt}}} – %{{customdata[1]:{rfmt}}}"
                                           f"<extra>Trend</extra>"))
    if drop_covid:
        fig.add_annotation(x="FY21", y=float(series["FY21"]), text="left out", showarrow=True, arrowhead=0, ay=-30,
                           font=dict(color=MUTED, size=11), arrowcolor=MUTED)
    style_fig(fig, f"{t_metric}: actual and trend forecast", height=400, yprefix="₹")
    fig.update_xaxes(categoryorder="array", categoryarray=YEARS + fx)
    show_chart(fig, "fc_trend")
    st.markdown(f'<div class="note">How to read it: if Titan keeps growing the way it did in the past, {t_metric.lower()} '
                f'in {fy_end} would land around <b>{"₹" + inr(tfc["forecast"].iloc[-1]) + (" cr" if is_money else "")}</b>, '
                f'most likely between {"₹" + inr(tfc["low"].iloc[-1])} and {"₹" + inr(tfc["high"].iloc[-1])}'
                f'{" cr" if is_money else ""}. Compare this with your scenario above — if your numbers are far above '
                f'the trend, you are assuming Titan does better than its own history.</div>', unsafe_allow_html=True)


# =====================================================================
# TAB 7: DATA & SOURCES
# =====================================================================
with tab_data:
    section("Raw data from the annual reports", "Consolidated figures in ₹ crore unless stated · edit the CSV files in the data/ folder to change them")
    raw = pd.read_csv(DATA_DIR / "titan_financials.csv")
    for stmt in ["Profit & Loss", "Balance Sheet", "Cash Flow"]:
        with st.expander(stmt, expanded=(stmt == "Profit & Loss")):
            part = raw[raw["statement"] == stmt].set_index("label")
            nice = pd.DataFrame({y: [f"{v:.2f}" if u == "Rs per share" else inr(v)
                                     for v, u in zip(part[y], part["unit"])] for y in YEARS}, index=part.index)
            nice.insert(0, "Unit", part["unit"].str.replace("Rs", "₹"))
            show_table(nice)
    with st.expander("Segments"):
        show_table(SEG_RAW, hide_index=True)
    with st.expander("Shareholding pattern (%)"):
        show_table(SHARE)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.download_button("⬇️ Financials CSV", (DATA_DIR / "titan_financials.csv").read_bytes(),
                           "titan_financials.csv", "text/csv")
    with c2:
        st.download_button("⬇️ Segments CSV", (DATA_DIR / "titan_segments.csv").read_bytes(),
                           "titan_segments.csv", "text/csv")
    with c3:
        out = M_ALL[[c for c, *_ in RATIOS.values()]].copy()
        out.columns = list(RATIOS.keys())
        st.download_button("⬇️ Ratios CSV", out.round(2).to_csv().encode(), "titan_ratios.csv", "text/csv")
    with c4:
        st.download_button("⬇️ Shareholding CSV", (DATA_DIR / "titan_shareholding.csv").read_bytes(),
                           "titan_shareholding.csv", "text/csv")

    # ---------- automatic checks that the numbers add up ----------
    section("Data checks", "The dashboard re-adds the numbers to make sure nothing was typed wrongly")
    f = FIN
    seg_all = SEG_RAW.set_index(["metric", "segment"])[YEARS].astype(float)
    tests = []
    for y in YEARS:
        r = f.loc[y]
        expenses = r["cogs"] + r["employee_cost"] + r["other_expenses"] + r["depreciation"] + r["finance_cost"]
        pbt_calc = r["revenue"] + r["other_income"] - expenses + r["share_of_jv"] - r["exceptional"]
        tests.append((f"{y}: revenue − expenses = profit before tax", abs(pbt_calc - r["pbt"]) <= 2))
        tests.append((f"{y}: profit before tax − tax = net profit", abs(r["pbt"] - r["tax"] - r["pat"]) <= 2))
        tests.append((f"{y}: segment revenues add up to total income",
                      abs(seg_all.loc["revenue", y].sum() - (r["revenue"] + r["other_income"])) <= 2))
        tests.append((f"{y}: segment profits − interest − one-offs = profit before tax",
                      abs(seg_all.loc["ebit", y].sum() - r["finance_cost"] - r["exceptional"] - r["pbt"]) <= 2))
        tests.append((f"{y}: net profit ÷ number of shares ≈ reported EPS (within 2%)",
                      abs(r["pat"] / SHARES_OUTSTANDING_CR / r["eps"] - 1) <= 0.02))
    passed = sum(ok for _, ok in tests)
    if passed == len(tests):
        st.success(f"✅ All {len(tests)} checks passed — every year's statements add up.")
    else:
        st.error(f"{len(tests) - passed} of {len(tests)} checks failed:")
        for name, ok in tests:
            if not ok:
                st.write("❌", name)

    section("Sources & method")
    st.markdown(
        """<div class="card"><p>
        <b>Financial statements:</b> Titan Company Limited Annual Reports for FY2019-20, 2020-21, 2021-22, 2022-23,
        2023-24, 2024-25 and 2025-26 — consolidated balance sheet, statement of profit and loss, cash-flow statement
        and the segment-information note. FY2019-20 and FY2020-21 figures are as shown in the 2020-21 report.<br>
        <b>Share prices:</b> daily NSE prices from Yahoo Finance via the <code>yfinance</code> Python library
        (refreshed every 15 minutes; live quote every minute). A copy is saved in <code>data/</code> so the dashboard
        still opens without internet.<br>
        <b>Shareholding:</b> quarterly shareholding-pattern filings (BSE).<br>
        <b>Store count:</b> Titan's Q4FY26 business update (3,603 stores incl. 127 Damas stores).<br><br>
        <b>Notes:</b> “Revenue” = revenue from operations, which includes bullion (gold-bar) sales. Toggle
        “excluding bullion” in the sidebar to see the core business. Cost of goods sold = materials consumed +
        purchases of stock-in-trade ± change in inventories. This dashboard is for learning purposes and is not
        investment advice.</p></div>""",
        unsafe_allow_html=True,
    )
