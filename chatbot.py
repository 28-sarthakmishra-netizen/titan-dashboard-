"""
TitanBot - a small, FREE chatbot for the Titan dashboard.

* Understands simple questions in English or Hinglish, e.g.
      "How was FY24?"   "FY24 kaisa raha?"   "profit in 2023"
      "compare FY22 vs FY26"   "jewellery revenue 2025"   "debt kitna hai?"
* No internet and no API key needed - every answer is built from the
  annual-report numbers in the data/ folder.
* How it works (simple version):
      1. find the year(s) in the question        -> parse_years()
      2. find what the user is asking about      -> detect_topic()
      3. build an answer from the numbers        -> answer()
  Want TitanBot to understand a new word?  Add it to the KEYWORDS lists below.
"""

import math
import re

# ---------------------------------------------------------------------------
# Words that tell us the user is writing in Hinglish (reply in Hinglish then)
# ---------------------------------------------------------------------------
HINGLISH_MARKERS = {
    "kaisa", "kaisi", "kaise", "kitna", "kitni", "kitne", "kya", "hai", "hain", "tha", "thi",
    "raha", "rahi", "rahe", "mein", "batao", "bata", "bataiye", "saal", "pichle", "pichhle",
    "munafa", "kamai", "karz", "karza", "nuksan", "ghata", "achha", "acha", "accha", "sabse",
    "kaun", "kab", "kyun", "kyu", "hua", "hui", "badha", "badhi", "dikhao", "samjhao", "ka",
    "ki", "ke", "ko", "aur", "wala", "wali", "kaunsa", "kaunsi", "matlab", "hota",
}

# ---------------------------------------------------------------------------
# Topics and the words that point to them (checked in this order)
# ---------------------------------------------------------------------------
KEYWORDS = [
    ("greeting", ["hello", "hi", "hey", "namaste", "namaskar", "hii", "good morning", "good evening"]),
    ("help", ["help", "what can you", "kya puch", "kya pooch", "what should i ask", "options"]),
    ("glossary", ["what is", "what does", "meaning", "matlab", "kya hota", "define", "explain"]),
    ("shareholding", ["shareholding", "promoter", "owner", "owns", "fii", "dii", "malik", "stake"]),
    ("price", ["share price", "stock price", "price", "market cap", "mcap", "valuation", "p/e", "pe ratio",
               "share ka", "stock kaisa", "invest"]),
    ("profitable", ["profitable", "loss", "nuksan", "ghata", "ghate", "profit mein hai", "making money"]),
    ("best", ["best", "highest", "record", "sabse achha", "sabse acha", "sabse zyada", "peak"]),
    ("worst", ["worst", "lowest", "sabse kharab", "sabse kam", "weakest", "bura"]),
    ("why", ["why", "kyun", "kyu", "reason", "wajah", "kaise badha", "kaise gira"]),
    ("usp", ["usp", "special", "khaas", "khas", "unique", "ceramic", "slim", "edge watch", "innovation",
             "different", "strength"]),
    ("history", ["founded", "history", "established", "started", "kab bani", "kab shuru", "origin", "itihas"]),
    ("md", ["ceo", "managing director", " md ", "chairman", "who runs"]),
    ("stores", ["store", "showroom", "outlet", "dukan", "network"]),
    ("bullion", ["bullion", "gold bar", "gold ingot"]),
    ("dividend", ["dividend", "dps", "payout", "laabhansh", "labhansh"]),
    ("eps", ["eps", "earning per share", "earnings per share"]),
    ("roce", ["roce", "return on capital"]),
    ("roe", ["roe", "return on equity", "return on net worth"]),
    ("margin", ["margin"]),
    ("ebitda", ["ebitda", "operating profit"]),
    ("debt", ["debt", "borrowing", "loan", "karz", "karza", "udhaar", "udhar", "leverage", "liabilit"]),
    ("cash", ["cash flow", "cashflow", "cfo", "fcf", "free cash", "cash"]),
    ("inventory", ["inventory", "inventories", "stock in hand", "maal"]),
    ("equity", ["net worth", "equity", "book value", "reserves"]),
    ("assets", ["asset"]),
    ("tax", ["tax"]),
    ("expenses", ["expense", "cost", "kharcha", "kharch"]),
    ("profit", ["net profit", "profit", "pat", "earning", "munafa", "fayda", "bottom line", "kamaya"]),
    ("revenue", ["revenue", "sales", "sale", "turnover", "top line", "topline", "income", "kamai", "bikri"]),
    ("growth", ["growth", "grow", "cagr", "badha", "badhi", "increase", "trend"]),
    ("summary", ["how was", "how did", "performance", "summary", "overview", "financial", "kaisa", "kaisi",
                 "kaise", "report", "results", "result", "perform"]),
]

SEGMENT_WORDS = {
    "Jewellery": ["jewel", "tanishq", "gehne", "gehna", "zevar", "jewelry", "caratlane", "mia", "zoya", "damas"],
    "Watches & Wearables": ["watch", "ghadi", "ghadiyan", "fastrack", "sonata", "wearable", "smartwatch"],
    "EyeCare": ["eyecare", "eye care", "eyewear", "eye+", "titan eye", "glasses", "chashma", "spectacle", "lens"],
    "Others": ["taneira", "skinn", "irth", "teal", "fragrance", "perfume", "saree", "bags", "emerging"],
}

GLOSSARY = {
    "ebitda": ("**EBITDA** = Earnings Before Interest, Tax, Depreciation & Amortisation — the profit from day-to-day "
               "operations before financing costs, tax and wear-and-tear.",
               "**EBITDA** = interest, tax aur depreciation se pehle ka operating profit — yaani roz ke business se "
               "kitna kamaya, loan ke byaaj aur tax se pehle."),
    "roce": ("**ROCE** (Return on Capital Employed) = EBIT ÷ all money used in the business (equity + borrowings + "
             "gold on loan + leases). It shows how well the whole capital is used.",
             "**ROCE** = EBIT ÷ business mein lagaya gaya saara paisa (equity + loan + gold loan + lease). "
             "Batata hai poore capital pe kitna return aaya."),
    "roe": ("**ROE** (Return on Equity) = Net profit ÷ shareholders' equity. How much profit each ₹100 of owners' "
            "money earns.",
            "**ROE** = Net profit ÷ shareholders ka paisa (equity). Matlab owners ke har ₹100 pe kitna profit bana."),
    "eps": ("**EPS** (Earnings per Share) = Net profit ÷ number of shares.",
            "**EPS** = Net profit ÷ total shares. Ek share ke hisse mein kitna profit aaya."),
    "p/e": ("**P/E ratio** = Share price ÷ EPS. How many rupees investors pay for ₹1 of yearly profit — "
            "a high P/E means the market expects strong future growth.",
            "**P/E** = Share price ÷ EPS. Investors ₹1 ke saalana profit ke liye kitne rupaye de rahe hain. "
            "Zyada P/E = market ko aage achhi growth ki ummeed hai."),
    "cagr": ("**CAGR** (Compound Annual Growth Rate) = the average yearly growth rate between two years.",
             "**CAGR** = do saalon ke beech ki average saalana growth rate."),
    "margin": ("**Margin** = profit as a % of revenue. *Gross margin* uses gross profit, *EBITDA margin* uses "
               "operating profit and *net margin* uses final profit.",
               "**Margin** = revenue ka kitna % profit bana. Gross, EBITDA aur net — teen tarah ke margin hote hain."),
    "gold on loan": ("**Gold on loan**: Titan borrows physical gold from banks instead of buying it. It protects "
                     "against gold-price swings and is repaid in gold — it works like debt.",
                     "**Gold on loan**: Titan bank se sona udhaar leta hai, khareedta nahi. Isse sone ke daam ke "
                     "utaar-chadhaav se bachav hota hai. Ye ek tarah ka karz hi hai."),
    "inventory": ("**Inventory days** = how many days of sales the stock on hand can cover "
                  "(inventory ÷ cost of goods × 365).",
                  "**Inventory days** = jo maal pada hai woh kitne din ki bikri ke barabar hai."),
    "bullion": ("**Bullion sales** = selling gold bars (not jewellery), usually at almost zero margin. Titan does "
                "this to manage its gold position; it inflates revenue but adds little profit.",
                "**Bullion sales** = gehne nahi, seedha sone ki bars bechna, lagbhag bina margin ke. Isse revenue "
                "badhta hai par profit lagbhag nahi."),
    "dividend": ("**Dividend** = the part of profit paid out to shareholders in cash, per share.",
                 "**Dividend** = profit ka woh hissa jo har share pe shareholders ko cash mein milta hai."),
}

EVENTS = {
    "FY20": ("The COVID-19 lockdown began in the last week of March 2020, at the very end of the year.",
             "Saal ke bilkul end (March 2020 ka aakhri hafta) mein COVID lockdown shuru hua."),
    "FY21": ("The COVID year — stores were shut for weeks, yet revenue held up because of gold & bullion sales.",
             "COVID wala saal — stores hafton band rahe, phir bhi gold aur bullion sales se revenue tika raha."),
    "FY22": ("A strong rebound as weddings and festivals came back after COVID.",
             "COVID ke baad zabardast rebound — shaadiyan aur tyohaar wapas aaye."),
    "FY23": ("Record year — the first Tanishq store opened in the USA.",
             "Record saal — USA mein pehla Tanishq store khula."),
    "FY24": ("Titan bought out CaratLane's founders (stake raised to ~99.99% for ₹4,621 cr), paid partly with "
             "borrowings — that pushed up interest costs.",
             "Titan ne ₹4,621 cr dekar CaratLane ka ~99.99% stake le liya, kuch paisa loan se — isse interest "
             "kharcha badha."),
    "FY25": ("Titan crossed ₹50,000 crore of annual revenue for the first time; high gold prices squeezed margins.",
             "Pehli baar ₹50,000 crore revenue cross kiya; sone ke ooche daam se margin thoda dabe."),
    "FY26": ("Landmark year — 67% stake in Damas Jewellery (GCC) and ~₹25,000 crore of revenue added in one year.",
             "Landmark saal — Damas Jewellery (GCC) mein 67% stake liya aur ek hi saal mein ~₹25,000 crore "
             "revenue juda."),
}

SUGGESTIONS = [
    "How was FY24?",
    "FY26 kaisa raha?",
    "Compare FY22 vs FY26",
    "Is Titan profitable?",
    "Jewellery revenue trend",
    "Debt kitna hai?",
    "Why did profit fall in FY25?",
    "FY28 mein profit kitna hoga?",
]

FORECAST_WORDS = ["forecast", "predict", "projection", "project", "estimate", "future", "next year", "next 5",
                  "agle saal", "agla saal", "aage", "aane wale", "expected", "outlook", "will be", "hoga", "hogi",
                  "honge", "badhega", "badhegi"]


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def _inr(x, d=0):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "–"
    neg = x < 0
    s = f"{abs(x):.{d}f}"
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


def _cr(x):
    return f"₹{_inr(x)} cr"


def _chg(a, b):
    """percentage change from a to b (None if not meaningful)"""
    try:
        if a is None or b is None or a <= 0:
            return None
        return (b / a - 1) * 100
    except Exception:
        return None


def _arrow(p, good_up=True):
    """'🟢 ▲ 12.3%' style change label (green = good direction)"""
    if p is None:
        return ""
    up = p >= 0
    good = up if good_up else not up
    return f"{'🟢' if good else '🔴'} {'▲' if up else '▼'} {abs(p):.1f}%"


def _cagr(a, b, n):
    try:
        if n <= 0 or a <= 0 or b <= 0:
            return None
        return ((b / a) ** (1 / n) - 1) * 100
    except Exception:
        return None


def _long(y):
    n = int(y[2:])
    return f"FY20{n-1:02d}-{n:02d}"


def _period(y):
    n = int(y[2:])
    return f"Apr 20{n-1:02d} – Mar 20{n:02d}"


def _has(text, word):
    """keyword match: short words must match as whole words"""
    w = word.strip()
    if len(w) <= 3 and w.isalpha():
        return re.search(rf"\b{re.escape(w)}\b", text) is not None
    return word in text


# ---------------------------------------------------------------------------
# 1. understand the question
# ---------------------------------------------------------------------------
def is_hinglish(text):
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    return len(tokens & HINGLISH_MARKERS) >= 1


def parse_years(text, years):
    """Returns (valid_years_in_order, invalid_years, notes)"""
    t = text.lower()
    found, notes = [], []

    def add(fy, pos):
        found.append((pos, fy))

    for m in re.finditer(r"\b(20\d{2})\s*[-–/]\s*(20\d{2}|\d{2})\b", t):          # 2023-24, 2023-2024
        add("FY" + m.group(2)[-2:], m.start())
    t2 = re.sub(r"\b(20\d{2})\s*[-–/]\s*(20\d{2}|\d{2})\b", lambda m: " " * len(m.group(0)), t)
    for m in re.finditer(r"\bfy\s*'?\s*(20\d{2}|\d{2})\b", t2):                    # FY24, fy 2024, fy'24
        add("FY" + m.group(1)[-2:], m.start())
    t3 = re.sub(r"\bfy\s*'?\s*(20\d{2}|\d{2})\b", lambda m: " " * len(m.group(0)), t2)
    for m in re.finditer(r"\b(20\d{2})\b", t3):                                     # plain 2024
        fy = "FY" + m.group(1)[-2:]
        add(fy, m.start())
        notes.append((m.group(1), fy))

    last_n = re.search(r"\b(last|pichle|pichhle|past)\s+(\d+)\s+(years?|saal)", t)
    if not found and not last_n:
        if re.search(r"\b(this year|is saal|current year|latest|abhi|recent|is baar)\b", t):
            add(years[-1], 0)
        elif re.search(r"\b(last year|previous year|pichle saal|pichhle saal|pichla saal|pichhla saal)\b", t):
            add(years[-2], 0)
        elif "covid" in t or "corona" in t or "pandemic" in t:
            add("FY21", 0)

    seen, ordered = set(), []
    for _, fy in sorted(found):
        if fy not in seen:
            seen.add(fy)
            ordered.append(fy)
    valid = [y for y in ordered if y in years]
    invalid = [y for y in ordered if y not in years]
    return valid, invalid, notes


def detect_topics(text):
    t = " " + text.lower() + " "
    hits = []
    for topic, words in KEYWORDS:
        if any(_has(t, w) for w in words):
            hits.append(topic)
    return hits


def detect_segment(text):
    t = text.lower()
    for seg, words in SEGMENT_WORDS.items():
        if any(w in t for w in words):
            return seg
    return None


# ---------------------------------------------------------------------------
# 2. the answer builder
# ---------------------------------------------------------------------------
class TitanBot:
    def __init__(self, fin, metrics, seg_rev, seg_ebit, shareholding, years, price_fn=None, stores="3,603",
                 forecast_fn=None):
        self.f = fin                # raw numbers (rows = years)
        self.m = metrics            # computed ratios (rows = years)
        self.sr = seg_rev           # segment revenue (rows = years)
        self.se = seg_ebit          # segment EBIT (rows = years)
        self.sh = shareholding
        self.years = years
        self.price_fn = price_fn    # function that returns live price info (or None)
        self.stores = stores
        self.forecast_fn = forecast_fn  # function(n_years) -> {"Base": df, "Bear": df, "Bull": df}

    # ---- public -----------------------------------------------------------
    def answer(self, question):
        q = (question or "").strip()
        H = is_hinglish(q)
        self._H = H
        L = (lambda en, hi: hi if H else en)
        if not q:
            return self._out(L("Please type a question 🙂", "Kuch puchiye 🙂"))

        years, invalid, notes = parse_years(q, self.years)
        topics = detect_topics(q)
        seg = detect_segment(q)
        prefix = ""
        if notes:
            n = ", ".join(f"{cal} → **{_long(fy)}** (year ending March {cal})" for cal, fy in notes if fy in self.years)
            if n:
                prefix = L(f"_I've read {n}. Ask with “FY” (e.g. FY24) if you meant a different year._\n\n",
                           f"_Maine {n} samjha hai. Alag saal chahiye to “FY” likh ke puchiye (jaise FY24)._\n\n")
        latest_n = int(self.years[-1][2:])
        future = [i for i in invalid if int(i[2:]) > latest_n]
        wants_fc = any(w in q.lower() for w in FORECAST_WORDS)
        if self.forecast_fn and (future or (wants_fc and not years)):
            return self._forecast(future[0] if future else None, detect_topics(q), L)
        if invalid and not years:
            latest = self.years[-1]
            return self._out(L(
                f"I only have annual-report data for **{self.years[0]}–{latest}** "
                f"({_long(self.years[0])} to {_long(latest)}). {', '.join(invalid)} isn't available"
                f"{' yet — that annual report is not out' if any(int(i[2:]) > int(latest[2:]) for i in invalid) else ''}.",
                f"Mere paas sirf **{self.years[0]}–{latest}** ka annual-report data hai. "
                f"{', '.join(invalid)} ka data nahi hai"
                f"{' — uski annual report abhi aayi nahi' if any(int(i[2:]) > int(latest[2:]) for i in invalid) else ''}."))
        if re.search(r"\b(q[1-4]|quarter|quarterly|timahi)\b", q.lower()):
            return self._out(L("I work with **yearly** annual-report numbers only (no quarterly data). "
                               "Try e.g. “How was FY26?”",
                               "Mere paas sirf **saalana** (annual report) numbers hain, quarterly nahi. "
                               "Jaise puchiye: “FY26 kaisa raha?”"))

        main = topics[0] if topics else None

        # ---- intent routing ----
        if main == "greeting" and len(topics) == 1 and not years:
            return self._intro(L)
        if main == "help":
            return self._intro(L)
        if "glossary" in topics and not years:
            g = self._glossary(q.lower(), H)
            if g:
                return g
        if len(years) >= 2 and not seg:
            return self._compare(years[0], years[-1], L, prefix)
        if "shareholding" in topics:
            return self._shareholding(L)
        if "price" in topics:
            return self._price(L)
        if "profitable" in topics:
            return self._profitable(years[0] if years else None, L, prefix)
        if "best" in topics or "worst" in topics:
            return self._best_worst("best" in topics, topics, seg, L)
        if "why" in topics and (years or "profit" in topics or "revenue" in topics):
            return self._why(years[0] if years else self.years[-1], topics, L, prefix)
        if "usp" in topics and not years:
            return self._usp(L)
        if "history" in topics:
            return self._history(L)
        if "md" in topics:
            return self._md(L)
        if "stores" in topics and not years:
            return self._stores(L)
        if "bullion" in topics and not years:
            return self._out(GLOSSARY["bullion"][1 if H else 0] + "\n\n" + self._bullion_table(L))
        if seg:
            return self._segment(seg, years[0] if years else None, L, prefix)

        metric_topics = ["dividend", "eps", "roce", "roe", "margin", "ebitda", "debt", "cash", "inventory",
                         "equity", "assets", "tax", "expenses", "profit", "revenue", "growth"]
        metric = next((t for t in topics if t in metric_topics), None)
        if metric:
            return self._metric(metric, years[0] if years else None, q.lower(), L, prefix)
        if years:
            return self._year_summary(years[0], L, prefix)
        if "summary" in topics:
            return self._overall(L)
        if "greeting" in topics:
            return self._intro(L)
        return self._fallback(L)

    # ---- building blocks --------------------------------------------------
    @staticmethod
    def _out(text, chart=None, table=None):
        return {"text": text, "chart": chart, "table": table}

    def _chart(self, col, title, highlight=None, kind="bar", suffix="", prefix="", decimals=0):
        return {"kind": kind, "x": list(self.years), "y": [float(v) for v in self.m[col]], "title": title,
                "highlight": highlight, "suffix": suffix, "prefix": prefix, "decimals": decimals}

    def _prev(self, y):
        i = self.years.index(y)
        return self.years[i - 1] if i > 0 else None

    def _intro(self, L):
        return self._out(L(
            "Hi! I'm **TitanBot** ⌚ — I answer questions about Titan's finances from the annual reports "
            f"(**{self.years[0]}–{self.years[-1]}**). You can type in English or Hinglish. Try:\n\n"
            "- *How was FY24?* · *FY26 kaisa raha?*\n- *Compare FY22 vs FY26*\n- *Profit in 2023* · *Debt kitna hai?*\n"
            "- *Jewellery revenue trend* · *Watches FY25*\n- *Why did profit fall in FY25?*\n"
            "- *Share price* · *Who owns Titan?* · *What is ROCE?*\n- *FY28 profit forecast* · *next year revenue*",
            "Namaste! Main **TitanBot** ⌚ hoon — Titan ki annual reports "
            f"(**{self.years[0]}–{self.years[-1]}**) se aapke sawaalon ke jawab deta hoon. English ya Hinglish, "
            "dono mein puch sakte hain. Jaise:\n\n"
            "- *FY24 kaisa raha?* · *How was FY26?*\n- *FY22 aur FY26 compare karo*\n- *2023 mein profit kitna tha?* · "
            "*Debt kitna hai?*\n- *Jewellery revenue trend* · *Watches FY25*\n- *FY25 mein profit kyun gira?*\n"
            "- *Share price* · *Titan ka malik kaun hai?* · *ROCE kya hota hai?*\n"
            "- *FY28 mein profit kitna hoga?* · *agle saal ka revenue*"))

    def _fallback(self, L):
        return self._out(L(
            "Sorry, I didn't catch that 🤔. I can answer about **revenue, profit, margins, EPS, dividend, ROE/ROCE, "
            "debt, cash flow, inventory, segments (jewellery, watches, eyecare), share price, shareholding** — for any "
            f"year from {self.years[0]} to {self.years[-1]}. Try *“How was FY24?”* or *“compare FY22 vs FY26”*.",
            "Maaf kijiye, samajh nahi aaya 🤔. Main **revenue, profit, margin, EPS, dividend, ROE/ROCE, debt, cash flow, "
            "inventory, segments (jewellery, watches, eyecare), share price, shareholding** ke baare mein bata sakta hoon "
            f"— {self.years[0]} se {self.years[-1]} tak kisi bhi saal ka. Jaise: *“FY24 kaisa raha?”* ya "
            "*“FY22 vs FY26 compare karo”*."))

    def _glossary(self, t, H):
        order = ["gold on loan", "ebitda", "roce", "roe", "eps", "p/e", "cagr", "margin", "inventory", "bullion",
                 "dividend"]
        for k in order:
            if k in t or (k == "p/e" and re.search(r"\bpe\b", t)):
                return self._out(GLOSSARY[k][1 if H else 0])
        return None

    # ---- year summary -----------------------------------------------------
    def _drivers(self, y, L):
        p = self._prev(y)
        if not p:
            return []
        a, b = self.m.loc[p], self.m.loc[y]
        out = []
        dm = b["ebitda_margin"] - a["ebitda_margin"]
        if abs(dm) >= 0.5:
            out.append(L(f"EBITDA margin {'rose' if dm > 0 else 'fell'} from {a['ebitda_margin']:.1f}% to "
                         f"{b['ebitda_margin']:.1f}%",
                         f"EBITDA margin {a['ebitda_margin']:.1f}% se {'badh' if dm > 0 else 'gir'} kar "
                         f"{b['ebitda_margin']:.1f}% {'hua' if dm > 0 else 'gaya'}"))
        fc = _chg(a["finance_cost"], b["finance_cost"])
        if fc is not None and abs(fc) >= 25:
            out.append(L(f"interest cost {'jumped' if fc > 0 else 'dropped'} {abs(fc):.0f}% "
                         f"({_cr(a['finance_cost'])} → {_cr(b['finance_cost'])})",
                         f"interest ka kharcha {abs(fc):.0f}% {'badha' if fc > 0 else 'ghata'} "
                         f"({_cr(a['finance_cost'])} → {_cr(b['finance_cost'])})"))
        if b["exceptional"] > 0:
            out.append(L(f"a one-off charge of {_cr(b['exceptional'])}",
                         f"{_cr(b['exceptional'])} ka ek one-time kharcha"))
        bl = b["bullion_sales"] - a["bullion_sales"]
        if abs(bl) >= 1000:
            out.append(L(f"bullion (gold-bar) sales {'rose' if bl > 0 else 'fell'} to {_cr(b['bullion_sales'])} "
                         "— this moves revenue but hardly any profit",
                         f"bullion (sone ki bar) sales {_cr(b['bullion_sales'])} {'tak badhi' if bl > 0 else 'tak giri'} "
                         "— isse revenue badalta hai, profit lagbhag nahi"))
        return out

    def _verdict(self, y, L):
        p = self._prev(y)
        if not p:
            return L("This is the first year in my data, so there is no earlier year to compare with.",
                     "Ye mere data ka pehla saal hai, isliye pichle saal se tulna nahi ho sakti.")
        rg = _chg(self.m.loc[p, "revenue"], self.m.loc[y, "revenue"])
        pg = _chg(self.m.loc[p, "pat"], self.m.loc[y, "pat"])
        if self.m.loc[y, "pat"] <= 0:
            return L("❌ Titan made a loss this year.", "❌ Is saal Titan ko nuksan hua.")
        if rg is not None and pg is not None:
            if rg > 15 and pg > 15:
                return L("🌟 Excellent year — both sales and profit grew strongly.",
                         "🌟 Bahut badhiya saal — sales aur profit dono tezi se badhe.")
            if rg >= 0 and pg < 0:
                return L("⚠️ Mixed year — sales grew but profit fell, because costs rose faster.",
                         "⚠️ Mila-jula saal — sales badhi par profit gira, kyunki kharche zyada tezi se badhe.")
            if rg < 0 and pg < 0:
                return L("🔴 Tough year — both sales and profit fell.",
                         "🔴 Mushkil saal — sales aur profit dono gire.")
            if pg > rg:
                return L("✅ Good year — profit grew faster than sales, so margins improved.",
                         "✅ Achha saal — profit sales se bhi tez badha, yaani margin sudhre.")
            return L("✅ Steady year — profit grew, though slower than sales.",
                     "✅ Theek-thaak achha saal — profit badha, par sales se thoda dheere.")
        return ""

    def _year_summary(self, y, L, prefix=""):
        r, p = self.m.loc[y], self._prev(y)
        rg = _chg(self.m.loc[p, "revenue"], r["revenue"]) if p else None
        pg = _chg(self.m.loc[p, "pat"], r["pat"]) if p else None
        segs = self.sr.loc[y]
        total = segs.sum()
        jw = segs.get("Jewellery", 0) / total * 100
        drivers = self._drivers(y, L)
        event = EVENTS.get(y)
        lines = [
            L(f"### {_long(y)} at a glance", f"### {_long(y)} ek nazar mein"),
            f"_{_period(y)}_",
            "",
            self._verdict(y, L),
            "",
            f"- **{L('Revenue', 'Revenue')}:** {_cr(r['revenue'])} {_arrow(rg)}",
            f"- **{L('Net profit', 'Net profit')}:** {_cr(r['pat'])} {_arrow(pg)}",
            f"- **{L('Margins', 'Margin')}:** EBITDA {r['ebitda_margin']:.1f}% · {L('net', 'net')} {r['pat_margin']:.1f}%",
            f"- **ROE:** {r['roe']:.1f}% · **EPS:** ₹{r['eps']:.2f} · **{L('Dividend', 'Dividend')}:** ₹{r['dps']:g}/share",
            L(f"- **Mix:** jewellery brought in {jw:.0f}% of segment revenue; watches {_cr(segs.get('Watches & Wearables', 0))}",
              f"- **Mix:** segment revenue ka {jw:.0f}% jewellery se aaya; watches se {_cr(segs.get('Watches & Wearables', 0))}"),
        ]
        if drivers:
            lines.append(f"- **{L('What moved profit', 'Profit pe asar')}:** " + "; ".join(drivers))
        if event:
            lines.append(f"- **{L('Key event', 'Khaas baat')}:** {event[1] if self._H else event[0]}")
        return self._out(prefix + "\n".join(lines),
                         chart=self._chart("pat", L("Net profit by year (₹ crore)", "Saal-dar-saal net profit (₹ crore)"),
                                           highlight=y))

    def _overall(self, L):
        f, l = self.years[0], self.years[-1]
        n = len(self.years) - 1
        return self._out(L(
            f"### Titan {f}–{l} in short\n"
            f"- Revenue grew from {_cr(self.m.loc[f, 'revenue'])} to {_cr(self.m.loc[l, 'revenue'])} "
            f"(**{_cagr(self.m.loc[f, 'revenue'], self.m.loc[l, 'revenue'], n):.1f}%** a year).\n"
            f"- Net profit grew from {_cr(self.m.loc[f, 'pat'])} to {_cr(self.m.loc[l, 'pat'])} "
            f"(**{_cagr(self.m.loc[f, 'pat'], self.m.loc[l, 'pat'], n):.1f}%** a year) — profitable every year.\n"
            f"- ROE in {l}: **{self.m.loc[l, 'roe']:.1f}%**. Weakest year: {self.m['pat'].idxmin()} (COVID); "
            f"best: {self.m['pat'].idxmax()}.\n\nAsk about any year, e.g. *“How was FY24?”*",
            f"### Titan {f}–{l} short mein\n"
            f"- Revenue {_cr(self.m.loc[f, 'revenue'])} se {_cr(self.m.loc[l, 'revenue'])} hua "
            f"(**{_cagr(self.m.loc[f, 'revenue'], self.m.loc[l, 'revenue'], n):.1f}%** saalana).\n"
            f"- Net profit {_cr(self.m.loc[f, 'pat'])} se {_cr(self.m.loc[l, 'pat'])} hua "
            f"(**{_cagr(self.m.loc[f, 'pat'], self.m.loc[l, 'pat'], n):.1f}%** saalana) — har saal profit.\n"
            f"- {l} mein ROE: **{self.m.loc[l, 'roe']:.1f}%**. Sabse kamzor saal: {self.m['pat'].idxmin()} (COVID); "
            f"sabse achha: {self.m['pat'].idxmax()}.\n\nKisi bhi saal ka puchiye, jaise *“FY24 kaisa raha?”*"),
            chart=self._chart("revenue", L("Revenue by year (₹ crore)", "Saal-dar-saal revenue (₹ crore)")))

    # ---- compare ------------------------------------------------------------
    def _compare(self, a, b, L, prefix=""):
        if self.years.index(a) > self.years.index(b):
            a, b = b, a
        rows = [("Revenue", "revenue", "cr"), ("EBITDA", "ebitda", "cr"), ("Net profit", "pat", "cr"),
                ("EBITDA margin", "ebitda_margin", "%"), ("Net margin", "pat_margin", "%"), ("ROE", "roe", "%"),
                ("EPS (₹)", "eps", "₹"), ("Dividend (₹)", "dps", "₹"), ("Borrowings", "borrowings", "cr"),
                ("Inventory", "inventories", "cr")]
        table = []
        for name, col, u in rows:
            va, vb = self.m.loc[a, col], self.m.loc[b, col]
            if u == "cr":
                fa, fb, ch = _cr(va), _cr(vb), _chg(va, vb)
                chs = f"{ch:+.0f}%" if ch is not None else "–"
            elif u == "%":
                fa, fb, chs = f"{va:.1f}%", f"{vb:.1f}%", f"{vb - va:+.1f} pts"
            else:
                fa, fb, ch = f"₹{va:.2f}", f"₹{vb:.2f}", _chg(va, vb)
                chs = f"{ch:+.0f}%" if ch is not None else "–"
            table.append({L("Metric", "Metric"): name, a: fa, b: fb, L("Change", "Badlav"): chs})
        n = self.years.index(b) - self.years.index(a)
        rc = _cagr(self.m.loc[a, "revenue"], self.m.loc[b, "revenue"], n)
        pc = _cagr(self.m.loc[a, "pat"], self.m.loc[b, "pat"], n)
        text = L(f"### {a} vs {b}\nOver {n} year{'s' if n > 1 else ''}, revenue grew **{rc:.1f}%** a year and net profit "
                 f"**{pc:.1f}%** a year.",
                 f"### {a} vs {b}\n{n} saal mein revenue **{rc:.1f}%** saalana aur net profit **{pc:.1f}%** saalana badha.")
        items = [("Revenue", "revenue"), ("EBITDA", "ebitda"), ("Net profit", "pat"), ("EPS", "eps"),
                 ("Dividend", "dps")]
        chart = {"kind": "bar", "x": [nm for nm, _ in items],
                 "y": [(_chg(self.m.loc[a, c], self.m.loc[b, c]) or 0.0) for _, c in items],
                 "highlight": None, "suffix": "%", "prefix": "", "decimals": 0,
                 "title": L(f"Growth from {a} to {b} (%)", f"{a} se {b} tak growth (%)")}
        return self._out(prefix + text, chart=chart, table=table)

    # ---- metric answers ---------------------------------------------------
    def _metric(self, metric, y, t, L, prefix=""):
        m = self.m
        last = self.years[-1]
        first = self.years[0]
        n = len(self.years) - 1
        spec = {
            "revenue": ("revenue", L("Revenue from operations", "Revenue"), "cr", True),
            "profit": ("pat", L("Net profit (PAT)", "Net profit (PAT)"), "cr", True),
            "ebitda": ("ebitda", "EBITDA", "cr", True),
            "eps": ("eps", "EPS", "₹", True),
            "roe": ("roe", L("Return on equity (ROE)", "Return on equity (ROE)"), "%", True),
            "roce": ("roce", "ROCE", "%", True),
            "dividend": ("dps", L("Dividend per share", "Dividend per share"), "₹", True),
            "debt": ("borrowings", L("Borrowings", "Borrowings (karz)"), "cr", False),
            "cash": ("cfo", L("Operating cash flow", "Operating cash flow"), "cr", True),
            "inventory": ("inventories", L("Inventory", "Inventory (maal)"), "cr", False),
            "equity": ("total_equity", L("Shareholders' equity", "Shareholders' equity"), "cr", True),
            "assets": ("total_assets", L("Total assets", "Total assets"), "cr", True),
            "tax": ("tax", L("Tax expense", "Tax"), "cr", None),
            "expenses": ("cogs", L("Cost of goods sold", "Cost of goods sold"), "cr", False),
        }
        if metric == "margin":
            if "gross" in t:
                spec["margin"] = ("gross_margin", "Gross margin", "%", True)
            elif "net" in t or "pat" in t or "profit" in t:
                spec["margin"] = ("pat_margin", L("Net profit margin", "Net profit margin"), "%", True)
            else:
                spec["margin"] = ("ebitda_margin", "EBITDA margin", "%", True)
        if metric == "growth":
            col = "pat" if any(w in t for w in ("profit", "munafa", "pat")) else "revenue"
            name = L("Net profit", "Net profit") if col == "pat" else L("Revenue", "Revenue")
            if y and self._prev(y):
                g = _chg(m.loc[self._prev(y), col], m.loc[y, col])
                txt = L(f"**{name} growth in {_long(y)}:** {_arrow(g)} ({_cr(m.loc[self._prev(y), col])} → {_cr(m.loc[y, col])}).",
                        f"**{_long(y)} mein {name} growth:** {_arrow(g)} ({_cr(m.loc[self._prev(y), col])} → {_cr(m.loc[y, col])}).")
            else:
                c = _cagr(m.loc[first, col], m.loc[last, col], n)
                txt = L(f"**{name}** grew from {_cr(m.loc[first, col])} ({first}) to {_cr(m.loc[last, col])} ({last}) — "
                        f"a CAGR of **{c:.1f}%** a year.",
                        f"**{name}** {first} mein {_cr(m.loc[first, col])} tha, {last} mein {_cr(m.loc[last, col])} — "
                        f"yaani **{c:.1f}%** saalana growth (CAGR).")
            return self._out(prefix + txt, chart=self._chart(col, f"{name} (₹ crore)", highlight=y))

        col, name, unit, good_up = spec[metric]

        def fmt(v):
            if unit == "cr":
                return _cr(v)
            if unit == "%":
                return f"{v:.1f}%"
            return f"₹{v:.2f}" if metric != "dividend" else f"₹{v:g}"

        extra = ""
        if metric == "debt":
            yy = y or last
            extra = L(f"\n\nPlus **gold on loan** of {_cr(m.loc[yy, 'gold_on_loan'])} and lease liabilities of "
                      f"{_cr(m.loc[yy, 'lease_liabilities'])}. Debt-to-equity: **{m.loc[yy, 'debt_equity']:.2f}x** "
                      f"(borrowings only) or **{m.loc[yy, 'debt_equity_all']:.2f}x** including gold loan & leases. "
                      f"Interest cover is a comfortable **{m.loc[yy, 'interest_coverage']:.1f}x**.",
                      f"\n\nIske alawa **gold on loan** {_cr(m.loc[yy, 'gold_on_loan'])} aur lease {_cr(m.loc[yy, 'lease_liabilities'])}. "
                      f"Debt-to-equity: **{m.loc[yy, 'debt_equity']:.2f}x** (sirf borrowings) ya "
                      f"**{m.loc[yy, 'debt_equity_all']:.2f}x** (gold loan aur lease milake). Interest cover "
                      f"**{m.loc[yy, 'interest_coverage']:.1f}x** hai — byaaj aaraam se chuk jaata hai.")
        elif metric == "cash":
            yy = y or last
            extra = L(f"\n\nFree cash flow (after capex): **{_cr(m.loc[yy, 'fcf'])}**. Over {first}–{last} Titan turned "
                      f"{m['cfo'].sum() / m['pat'].sum() * 100:.0f}% of its profit into operating cash — gold inventory "
                      "build-up absorbs the rest.",
                      f"\n\nFree cash flow (capex ke baad): **{_cr(m.loc[yy, 'fcf'])}**. {first}–{last} mein Titan ne apne "
                      f"profit ka {m['cfo'].sum() / m['pat'].sum() * 100:.0f}% hi cash mein badla — baaki sone ke "
                      "inventory mein lag gaya.")
        elif metric == "inventory":
            yy = y or last
            extra = L(f"\n\nThat is about **{m.loc[yy, 'inventory_days']:.0f} days** of cost of sales.",
                      f"\n\nYe lagbhag **{m.loc[yy, 'inventory_days']:.0f} din** ki bikri ke barabar maal hai.")
        elif metric == "dividend":
            yy = y or last
            extra = L(f"\n\nPayout ratio: **{m.loc[yy, 'payout_ratio']:.0f}%** of EPS.",
                      f"\n\nPayout ratio: EPS ka **{m.loc[yy, 'payout_ratio']:.0f}%**.")
        elif metric == "revenue":
            yy = y or last
            if m.loc[yy, "bullion_sales"] > 0:
                extra = L(f"\n\nThis includes **{_cr(m.loc[yy, 'bullion_sales'])}** of bullion (gold-bar) sales; "
                          f"core business revenue was {_cr(m.loc[yy, 'revenue'] - m.loc[yy, 'bullion_sales'])}.",
                          f"\n\nIsme **{_cr(m.loc[yy, 'bullion_sales'])}** bullion (sone ki bar) sales bhi hai; "
                          f"core business ka revenue {_cr(m.loc[yy, 'revenue'] - m.loc[yy, 'bullion_sales'])} tha.")
        elif metric == "tax":
            yy = y or last
            extra = L(f"\n\nEffective tax rate: **{m.loc[yy, 'tax_rate']:.1f}%**.",
                      f"\n\nEffective tax rate: **{m.loc[yy, 'tax_rate']:.1f}%**.")
        elif metric == "expenses":
            yy = y or last
            extra = L(f"\n\nOther big costs that year: employees {_cr(m.loc[yy, 'employee_cost'])}, other expenses "
                      f"(incl. ads) {_cr(m.loc[yy, 'other_expenses'])}, interest {_cr(m.loc[yy, 'finance_cost'])}.",
                      f"\n\nUs saal baaki bade kharche: employees {_cr(m.loc[yy, 'employee_cost'])}, other expenses "
                      f"(ads milake) {_cr(m.loc[yy, 'other_expenses'])}, interest {_cr(m.loc[yy, 'finance_cost'])}.")

        if y:
            p = self._prev(y)
            v = m.loc[y, col]
            if unit == "%":
                ch = (v - m.loc[p, col]) if p else None
                chtxt = (f" ({'▲' if ch >= 0 else '▼'} {abs(ch):.1f} pts {L('vs', 'vs')} {p})" if ch is not None else "")
            else:
                ch = _chg(m.loc[p, col], v) if p else None
                chtxt = (f" ({_arrow(ch, good_up if good_up is not None else True)} {L('vs', 'vs')} {p})"
                         if ch is not None else "")
            rank = int((m[col] > v).sum()) + 1
            rank_txt = ""
            if rank == 1:
                rank_txt = L(" — the **highest** in the 7 years.", " — 7 saalon mein **sabse zyada**.")
            elif rank == len(self.years):
                rank_txt = L(" — the **lowest** in the 7 years.", " — 7 saalon mein **sabse kam**.")
            txt = L(f"**{name} in {_long(y)}:** {fmt(v)}{chtxt}{rank_txt}",
                    f"**{_long(y)} mein {name}:** {fmt(v)}{chtxt}{rank_txt}")
        else:
            v0, v1 = m.loc[first, col], m.loc[last, col]
            if unit in ("cr", "₹") and v0 > 0 and v1 > 0:
                c = _cagr(v0, v1, n)
                trend = L(f"up from {fmt(v0)} in {first} (**{c:.1f}%** a year)",
                          f"{first} mein {fmt(v0)} tha (**{c:.1f}%** saalana growth)")
            else:
                trend = L(f"vs {fmt(v0)} in {first}", f"{first} mein {fmt(v0)} tha")
            txt = L(f"**{name} in {_long(last)} (latest):** {fmt(v1)}, {trend}.",
                    f"**{_long(last)} (latest) mein {name}:** {fmt(v1)}, {trend}.")
        suffix = "%" if unit == "%" else ""
        prefixc = "₹" if unit == "₹" else ""
        return self._out(prefix + txt + extra,
                         chart=self._chart(col, f"{name}{' (₹ crore)' if unit == 'cr' else ''}", highlight=y,
                                           kind="line" if unit == "%" else "bar", suffix=suffix, prefix=prefixc,
                                           decimals=1 if unit in ("%",) else (2 if unit == "₹" else 0)))


    # ---- forecasts ------------------------------------------------------------
    def _forecast(self, fy, topics, L):
        last = self.years[-1]
        latest_n = int(last[2:])
        if fy is None:
            fy = f"FY{latest_n + 1:02d}"
        ahead = int(fy[2:]) - latest_n
        if ahead > 5:
            return self._out(L(f"My forecasts go up to **FY{latest_n + 5:02d}** (5 years ahead). Try a nearer year, "
                               "or open the **🔮 Forecast** tab.",
                               f"Mere forecast sirf **FY{latest_n + 5:02d}** tak hain (5 saal aage). Thoda paas ka saal "
                               "puchiye, ya **🔮 Forecast** tab dekhiye."))
        sc = self.forecast_fn(5)
        base, bear, bull = sc["Base"], sc["Bear"], sc["Bull"]
        if "revenue" in topics:
            col, name = "revenue", L("Revenue (excl. bullion)", "Revenue (bullion ke bina)")
        elif "eps" in topics:
            col, name = "eps", "EPS"
        elif "dividend" in topics:
            col, name = "dps", L("Dividend per share", "Dividend per share")
        else:
            col, name = "pat", L("Net profit", "Net profit")

        def fmt(v):
            return _cr(v) if col in ("revenue", "pat") else f"₹{v:.2f}"

        r = base.loc[fy]
        g_pat = _cagr(self.m.loc[last, "pat"], r["pat"], ahead)
        text = L(
            f"### 🔮 {_long(fy)} — forecast (estimate)\n"
            f"**{name}, base case:** about **{fmt(base.loc[fy, col])}**  \n"
            f"_Range: {fmt(bear.loc[fy, col])} (bear) to {fmt(bull.loc[fy, col])} (bull)_\n\n"
            f"- Revenue excl. bullion ≈ {_cr(r['revenue'])} · net profit ≈ {_cr(r['pat'])} "
            f"(≈{g_pat:.0f}% a year from {last}) · EPS ≈ ₹{r['eps']:.1f}\n"
            f"- Base case = revenue growth starting at 18% and slowing 1 point a year, EBITDA margin 10.8%, "
            f"tax 25.5%.\n\n"
            f"_This is a model estimate, not a fact or investment advice. Change the assumptions in the "
            f"**🔮 Forecast** tab._",
            f"### 🔮 {_long(fy)} — forecast (andaaza)\n"
            f"**{name}, base case:** lagbhag **{fmt(base.loc[fy, col])}**  \n"
            f"_Range: {fmt(bear.loc[fy, col])} (bear) se {fmt(bull.loc[fy, col])} (bull) tak_\n\n"
            f"- Revenue (bullion ke bina) ≈ {_cr(r['revenue'])} · net profit ≈ {_cr(r['pat'])} "
            f"({last} se ≈{g_pat:.0f}% saalana) · EPS ≈ ₹{r['eps']:.1f}\n"
            f"- Base case = revenue growth 18% se shuru, har saal 1 point dheemi; EBITDA margin 10.8%; tax 25.5%.\n\n"
            f"_Ye model ka andaaza hai, pakka number ya investment advice nahi. Assumptions **🔮 Forecast** tab "
            f"mein badal sakte hain._")
        hist_col = {"revenue": None, "pat": "pat", "eps": "eps", "dps": "dps"}[col]
        if hist_col:
            hist_vals = [float(v) for v in self.m[hist_col]]
        else:
            hist_vals = [float(a - b) for a, b in zip(self.m["revenue"], self.m["bullion_sales"])]
        fut = list(base.index)
        chart = {"kind": "bar", "x": list(self.years) + fut, "y": hist_vals + [float(v) for v in base[col]],
                 "highlight": fy, "title": L(f"{name}: actual + base-case forecast", f"{name}: actual + forecast"),
                 "suffix": "", "prefix": "" if col in ("revenue", "pat") else "₹",
                 "decimals": 0 if col in ("revenue", "pat") else 1, "forecast_from": fut[0]}
        return self._out(text, chart=chart)

    # ---- segments -----------------------------------------------------------
    def _segment(self, seg, y, L, prefix=""):
        first, last = self.years[0], self.years[-1]
        n = len(self.years) - 1
        rev, ebit = self.sr[seg], self.se[seg]
        chart = {"kind": "bar", "x": list(self.years), "y": [float(v) for v in rev], "highlight": y,
                 "title": L(f"{seg} revenue (₹ crore)", f"{seg} revenue (₹ crore)"), "suffix": "", "prefix": "",
                 "decimals": 0, "segment": seg}
        if y:
            p = self._prev(y)
            g = _chg(rev[p], rev[y]) if p else None
            share = rev[y] / self.sr.loc[y].sum() * 100
            margin = ebit[y] / rev[y] * 100 if rev[y] else float("nan")
            txt = L(f"**{seg} in {_long(y)}**\n- Revenue: {_cr(rev[y])} {_arrow(g)}\n- Share of Titan's total: "
                    f"{share:.1f}%\n- Segment profit (EBIT): {_cr(ebit[y])} · margin {margin:.1f}%",
                    f"**{_long(y)} mein {seg}**\n- Revenue: {_cr(rev[y])} {_arrow(g)}\n- Titan ke total ka hissa: "
                    f"{share:.1f}%\n- Segment profit (EBIT): {_cr(ebit[y])} · margin {margin:.1f}%")
        else:
            c = _cagr(rev[first], rev[last], n)
            margin = ebit[last] / rev[last] * 100
            txt = L(f"**{seg}**: revenue went from {_cr(rev[first])} ({first}) to {_cr(rev[last])} ({last}) — "
                    f"**{c:.1f}%** a year. In {last} it earned {_cr(ebit[last])} of segment profit "
                    f"({margin:.1f}% margin).",
                    f"**{seg}**: revenue {first} mein {_cr(rev[first])} tha, {last} mein {_cr(rev[last])} — "
                    f"**{c:.1f}%** saalana growth. {last} mein segment profit {_cr(ebit[last])} "
                    f"({margin:.1f}% margin) raha.")
        if seg == "Others":
            txt += L("\n\n_“Others” = Taneira, SKINN, IRTH and TEAL (engineering & automation)._",
                     "\n\n_“Others” = Taneira, SKINN, IRTH aur TEAL (engineering & automation)._")
        return self._out(prefix + txt, chart=chart)

    # ---- other topics -------------------------------------------------------
    def _profitable(self, y, L, prefix=""):
        if y:
            v = self.m.loc[y, "pat"]
            ok = v > 0
            return self._out(prefix + L(
                f"{'✅ Yes' if ok else '❌ No'} — net profit in {_long(y)} was **{_cr(v)}** "
                f"(net margin {self.m.loc[y, 'pat_margin']:.1f}%).",
                f"{'✅ Haan' if ok else '❌ Nahi'} — {_long(y)} mein net profit **{_cr(v)}** tha "
                f"(net margin {self.m.loc[y, 'pat_margin']:.1f}%)."),
                chart=self._chart("pat", L("Net profit by year (₹ crore)", "Net profit (₹ crore)"), highlight=y))
        loss = [yy for yy in self.years if self.m.loc[yy, "pat"] <= 0]
        f, l = self.years[0], self.years[-1]
        if not loss:
            txt = L(f"✅ **Yes.** Titan made a net profit in **every year** from {f} to {l}. Profit rose from "
                    f"{_cr(self.m.loc[f, 'pat'])} to {_cr(self.m.loc[l, 'pat'])}, and ROE in {l} was "
                    f"**{self.m.loc[l, 'roe']:.1f}%** — very strong. Even in the COVID year (FY21) it earned "
                    f"{_cr(self.m.loc['FY21', 'pat'])}.",
                    f"✅ **Haan.** Titan ne {f} se {l} tak **har saal** profit kamaya. Profit "
                    f"{_cr(self.m.loc[f, 'pat'])} se badhkar {_cr(self.m.loc[l, 'pat'])} ho gaya, aur {l} mein ROE "
                    f"**{self.m.loc[l, 'roe']:.1f}%** raha — bahut strong. COVID wale saal (FY21) mein bhi "
                    f"{_cr(self.m.loc['FY21', 'pat'])} ka profit hua.")
        else:
            txt = L(f"Titan made a loss in {', '.join(loss)}.", f"Titan ko {', '.join(loss)} mein nuksan hua.")
        return self._out(txt, chart=self._chart("pat", L("Net profit by year (₹ crore)", "Net profit (₹ crore)")))

    def _best_worst(self, best, topics, seg, L):
        if seg:
            s = self.sr[seg]
            y = s.idxmax() if best else s.idxmin()
            return self._out(L(f"{'Best' if best else 'Weakest'} year for **{seg}** revenue: **{_long(y)}** "
                               f"with {_cr(s[y])}.",
                               f"**{seg}** revenue ka {'sabse achha' if best else 'sabse kamzor'} saal: "
                               f"**{_long(y)}** — {_cr(s[y])}."),
                             chart={"kind": "bar", "x": list(self.years), "y": [float(v) for v in s], "highlight": y,
                                    "title": f"{seg} revenue (₹ crore)", "suffix": "", "prefix": "", "decimals": 0,
                                    "segment": seg})
        col, name = ("revenue", "revenue") if "revenue" in topics else ("pat", L("net profit", "net profit"))
        if "margin" in topics:
            col, name = "ebitda_margin", "EBITDA margin"
        if "roe" in topics:
            col, name = "roe", "ROE"
        s = self.m[col]
        y = s.idxmax() if best else s.idxmin()
        val = f"{s[y]:.1f}%" if col in ("ebitda_margin", "roe") else _cr(s[y])
        why = ""
        if not best and y == "FY21":
            why = L(" — the COVID year.", " — COVID wala saal.")
        return self._out(L(f"{'Best' if best else 'Weakest'} year by {name}: **{_long(y)}** at {val}{why}",
                           f"{name} ke hisaab se {'sabse achha' if best else 'sabse kamzor'} saal: **{_long(y)}** — "
                           f"{val}{why}"),
                         chart=self._chart(col, name, highlight=y,
                                           kind="line" if col in ("ebitda_margin", "roe") else "bar",
                                           suffix="%" if col in ("ebitda_margin", "roe") else "",
                                           decimals=1 if col in ("ebitda_margin", "roe") else 0))

    def _why(self, y, topics, L, prefix=""):
        p = self._prev(y)
        if not p:
            return self._year_summary(y, L, prefix)
        pg = _chg(self.m.loc[p, "pat"], self.m.loc[y, "pat"])
        rg = _chg(self.m.loc[p, "revenue"], self.m.loc[y, "revenue"])
        drivers = self._drivers(y, L)
        if not drivers:
            drivers = [L("costs moved broadly in line with sales", "kharche lagbhag sales ke saath hi badhe")]
        event = EVENTS.get(y)
        txt = L(f"**{_long(y)}:** revenue {_arrow(rg)}, net profit {_arrow(pg)}.\n\n**Main reasons:**\n- " +
                "\n- ".join(drivers) + (f"\n- {event[0]}" if event else ""),
                f"**{_long(y)}:** revenue {_arrow(rg)}, net profit {_arrow(pg)}.\n\n**Mukhya wajah:**\n- " +
                "\n- ".join(drivers) + (f"\n- {event[1]}" if event else ""))
        return self._out(prefix + txt, chart=self._chart("ebitda_margin", "EBITDA margin (%)", highlight=y,
                                                         kind="line", suffix="%", decimals=1))

    def _shareholding(self, L):
        col = self.sh.columns[-1]
        s = self.sh[col]
        lines = "\n".join(f"- {k}: **{v:.2f}%**" for k, v in s.items())
        return self._out(L(f"**Who owns Titan ({col}):**\n{lines}\n\nThe promoters are the **Tata Group** "
                           "(about 25%) and **TIDCO**, the Tamil Nadu government's industrial body (about 28%).",
                           f"**Titan ka malik kaun ({col}):**\n{lines}\n\nPromoters hain **Tata Group** (lagbhag 25%) aur "
                           "**TIDCO** — Tamil Nadu sarkar ki industrial body (lagbhag 28%)."))

    def _price(self, L):
        info = None
        if self.price_fn:
            try:
                info = self.price_fn()
            except Exception:
                info = None
        if not info:
            return self._out(L("I can't reach the live share price right now (no internet?). Open the **Share Price** "
                               "tab after connecting, or press *Refresh prices now* in the sidebar.",
                               "Abhi live share price nahi mil raha (shayad internet nahi hai). Internet chalu karke "
                               "**Share Price** tab dekhiye ya sidebar mein *Refresh prices now* dabaiye."))
        lines = [L(f"**Titan share price:** ₹{_inr(info['last'], 2)} "
                   f"({info['chg']:+.2f}% today) · _{info['when']}_",
                   f"**Titan ka share price:** ₹{_inr(info['last'], 2)} "
                   f"(aaj {info['chg']:+.2f}%) · _{info['when']}_"),
                 f"- Market cap: **₹{_inr(info['mcap'])} cr**",
                 f"- P/E ({self.years[-1]} EPS): **{info['pe']:.1f}x**",
                 f"- 52-week range: ₹{_inr(info['low52'])} – ₹{_inr(info['high52'])}"]
        if info.get("ret1y") is not None:
            lines.append(L(f"- 1-year return: **{info['ret1y']:+.1f}%**", f"- 1 saal ka return: **{info['ret1y']:+.1f}%**"))
        if info.get("ret5y") is not None:
            lines.append(L(f"- 5-year return: **{info['ret5y']:+.1f}%**", f"- 5 saal ka return: **{info['ret5y']:+.1f}%**"))
        lines.append(L("\n_Not investment advice._", "\n_Ye investment advice nahi hai._"))
        return self._out("\n".join(lines))

    def _usp(self, L):
        return self._out(L(
            "**What makes Titan special:**\n"
            "- ⌚ **Edge** — launched in 2002 at just **3.5 mm**, then billed as the world's slimmest watch; "
            "Edge Ceramic (4.4 mm) as the slimmest ceramic watch; the 2.2 mm Edge Mechanical movement.\n"
            "- 🏆 Design awards — Edge Ultraslim won the **iF Design Award** and was nominated at the GPHG in Geneva.\n"
            "- 📊 About **27%** of India's analog-watch market, and **over 50%** in watches under ₹25,000.\n"
            "- 💍 **Tanishq** — trust built on the **Karatmeter** gold-purity check and gold-exchange schemes.\n"
            "- 🏬 **3,603 stores** in 440+ towns and **49 million** Encircle loyalty members (FY26).\n\n"
            "See the **✨ Why Titan** tab for the full showcase.",
            "**Titan ko khaas kya banata hai:**\n"
            "- ⌚ **Edge** — 2002 mein sirf **3.5 mm** ki ghadi, us waqt duniya ki sabse patli kahi gayi; "
            "Edge Ceramic (4.4 mm) sabse patli ceramic ghadi; Edge Mechanical ka 2.2 mm movement.\n"
            "- 🏆 Design awards — Edge Ultraslim ko **iF Design Award** mila aur Geneva ke GPHG mein nomination.\n"
            "- 📊 India ke analog-watch market ka lagbhag **27%**, aur ₹25,000 se sasti ghadiyon mein **50% se zyada**.\n"
            "- 💍 **Tanishq** — **Karatmeter** (sone ki shuddhta check) aur gold-exchange se bharosa.\n"
            "- 🏬 **3,603 stores**, 440+ shehar aur **4.9 crore** Encircle loyalty members (FY26).\n\n"
            "Poora showcase **✨ Why Titan** tab mein dekhiye."))

    def _history(self, L):
        return self._out(L(
            "**Titan's story:** incorporated in **1984** as a joint venture of the **Tata Group** and **TIDCO** "
            "(Tamil Nadu); started making watches in **1987** at Hosur; entered jewellery with **Tanishq** in **1994**, "
            "then eyewear (Titan Eye+). Bought control of **CaratLane** in 2016, launched **Taneira** in 2017, "
            "**beYon** lab-grown diamonds in 2025 and took **67% of Damas** (GCC) in January 2026.",
            "**Titan ki kahani:** **1984** mein **Tata Group** aur **TIDCO** (Tamil Nadu) ke joint venture ke roop "
            "mein bani; **1987** mein Hosur mein ghadiyan banana shuru kiya; **1994** mein **Tanishq** ke saath "
            "jewellery mein aayi, phir eyewear (Titan Eye+). 2016 mein **CaratLane** ka control liya, 2017 mein "
            "**Taneira**, 2025 mein **beYon** (lab-grown diamonds), aur January 2026 mein **Damas** (GCC) ka 67%."))

    def _md(self, L):
        return self._out(L("Titan's Managing Director is **Ajoy Chawla** (as per the FY26 results). "
                           "Titan is a Tata Group company.",
                           "Titan ke Managing Director **Ajoy Chawla** hain (FY26 results ke hisaab se). "
                           "Titan ek Tata Group company hai."))

    def _stores(self, L):
        return self._out(L(f"Titan had **{self.stores} stores** at the end of March 2026 across 440+ towns — including "
                           "Tanishq, Mia, Zoya, CaratLane, Titan World, Helios, Fastrack, Titan Eye+, Taneira and 123 "
                           "Damas stores in the GCC.",
                           f"March 2026 ke end tak Titan ke **{self.stores} stores** the, 440+ shehron mein — Tanishq, "
                           "Mia, Zoya, CaratLane, Titan World, Helios, Fastrack, Titan Eye+, Taneira aur GCC mein Damas ke "
                           "123 stores milake."))

    def _bullion_table(self, L):
        rows = " · ".join(f"{y}: {_cr(self.m.loc[y, 'bullion_sales'])}" for y in self.years)
        return L(f"Bullion sales by year — {rows}", f"Saal-dar-saal bullion sales — {rows}")
