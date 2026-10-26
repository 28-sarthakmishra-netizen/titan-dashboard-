# Titan Company Limited — Financial Insights Dashboard (Python)

Python mein bana ek interactive dashboard: **Streamlit** (web app) + **Plotly** (charts) + **yfinance** (live NSE share price).
Saare financial numbers Titan ki **Annual Reports FY2019-20 se FY2025-26** (consolidated statements + segment notes) se liye gaye hain.

---

## 1. Chalane ka sabse aasaan tarika

**Windows:** folder kholo aur `run_dashboard.bat` par double-click karo.
**Mac:** `run_dashboard.command` par double-click karo (pehli baar right-click → Open).

Pehli baar libraries install hongi (1-2 minute), phir browser mein dashboard khul jayega (`http://localhost:8501`).
Black window ko khula rehne do — band karoge to dashboard band ho jayega.

## 2. Terminal / VS Code se chalana

Is folder mein terminal kholo (VS Code: *File → Open Folder* → *Terminal → New Terminal*) aur ye do commands chalao:

```bash
pip install -r requirements.txt
streamlit run app.py
```

> `pip` na chale to `python -m pip install -r requirements.txt` try karo (Mac par `python3`).
> `streamlit` command na mile to `python -m streamlit run app.py` chalao.

Python 3.9 ya usse naya chahiye. Check: `python --version`.

## 3. Dashboard mein kya hai

| Tab | Kya dikhata hai |
|---|---|
| 🏛️ Overview | "Titan profitable hai ya nahi?" ka verdict, key numbers, company profile, revenue mix, shareholding, milestones |
| 📈 Share Price (Live) | Live NSE price (har minute refresh), candlestick/line chart, 50/200-day average, Nifty 50 se comparison, har saal ka P/E, monthly returns heat-map, "agar maine invest kiya hota" calculator |
| 💰 Profit & Loss | Revenue, profit, margins, growth, revenue → profit waterfall, common-size P&L |
| 💎 Segments | Jewellery / Watches / EyeCare / Others ka revenue, profit, margin, brands |
| 🏦 Balance Sheet & Cash | Equity, borrowings, gold on loan, inventory, cash flows, free cash flow, dividend |
| 🩺 Ratios & Health Check | 10-point health score, ratio explorer, do saal compare karo, saare ratios ki table |
| 📚 Data & Sources | Raw data, CSV download, automatic data checks, sources |

**Sidebar controls:** year range slider, "revenue excluding bullion" toggle, live price refresh button.

## 4. Changes kaise karein

* **Numbers badalne hain?** `data/` folder ki CSV files Excel mein kholo:
  * `titan_financials.csv` – P&L, balance sheet, cash flow
  * `titan_segments.csv` – segment revenue & profit
  * `titan_shareholding.csv` – shareholding pattern
* **Naya saal (FY27) add karna hai?** Har CSV mein ek naya column `FY27` jodo — dashboard khud pick kar lega.
* **Apna naam / colours badalne hain?** `app.py` kholo → **SECTION 1: SETTINGS** (top par).
* **Koi chart badalna hai?** `app.py` mein chart ka title search karo (jaise `"Net profit after tax"`) — har chart ka chhota block wahin hai.
* `app.py` save karte hi browser mein dashboard apne aap refresh ho jata hai.

## 5. Agar kuch problem aaye

* **Share price nahi dikh raha:** internet check karo, sidebar mein *Refresh prices now* dabao. Yahoo kabhi-kabhi kuch der ke liye rok deta hai — thodi der baad try karo. Ek baar price aa gaya to `data/` mein copy save ho jati hai, phir bina internet ke bhi chart dikhega.
* **`ModuleNotFoundError`:** `pip install -r requirements.txt` dobara chalao.
* **Port busy:** `streamlit run app.py --server.port 8502`

## 6. Notes

* Saare amounts **₹ crore, consolidated** hain.
* "Revenue from operations" mein bullion (gold bar) sales bhi shamil hain (FY26 mein ₹10,568 cr) — sidebar toggle se core business dekh sakte ho.
* Share prices: Yahoo Finance (NSE: TITAN). Shareholding: BSE filings. Store count: Titan Q4FY26 business update.
* Sirf academic use ke liye — investment advice nahi.
