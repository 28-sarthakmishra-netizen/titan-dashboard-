"""
Forecast engine for the Titan dashboard.

Two ways of looking ahead (both are estimates, not facts):

1. SCENARIO forecast (driver-based) - you choose the assumptions:
       revenue growth, how fast growth slows ("fade"), EBITDA margin, tax rate, dividend payout ...
   and the model builds the P&L year by year:
       Revenue  -> EBITDA (= revenue x margin)
       EBITDA + other income - depreciation - interest = Profit before tax
       PBT x (1 - tax rate) = Net profit  ->  EPS  ->  Dividend per share

2. TREND forecast (statistical) - fits a straight line to the LOG of past values
   (i.e. a constant yearly growth rate) and extends it, with an 80% range band.

Revenue here = revenue EXCLUDING bullion (gold-bar) sales, because bullion sales jump around
a lot and earn almost no profit.
"""

import math

import numpy as np
import pandas as pd

# Preset assumptions (all in %). Change these to change the Bear / Base / Bull buttons.
SCENARIOS = {
    "Bear": {"growth": 10.0, "fade": 1.0, "ebitda": 9.5, "tax": 26.0, "payout": 25.0},
    "Base": {"growth": 18.0, "fade": 1.0, "ebitda": 10.8, "tax": 25.5, "payout": 28.0},
    "Bull": {"growth": 25.0, "fade": 1.0, "ebitda": 12.0, "tax": 25.0, "payout": 30.0},
}
# Smaller cost lines as % of revenue (close to the FY26 actuals)
ADVANCED_DEFAULTS = {"dep": 1.1, "interest": 1.5, "other_income": 0.75}

SCENARIO_NOTES = {
    "Bear": "Demand slows (e.g. very high gold prices), growth ~10% and margins squeezed.",
    "Base": "Growth cools from recent 25-30% to ~18% as the business gets bigger; margins near FY26.",
    "Bull": "Recent momentum continues (~25% growth) with better margins from studded jewellery & watches.",
}

# t-values for an 80% two-sided prediction interval, by degrees of freedom
_T80 = {1: 3.078, 2: 1.886, 3: 1.638, 4: 1.533, 5: 1.476, 6: 1.440, 7: 1.415, 8: 1.397, 9: 1.383, 10: 1.372}


def future_years(last_fy, n):
    """'FY26', 3 -> ['FY27', 'FY28', 'FY29']"""
    start = int(last_fy[2:])
    return [f"FY{start + i:02d}" for i in range(1, n + 1)]


def scenario_forecast(base, years_ahead, growth, fade, ebitda, tax, payout,
                      dep=ADVANCED_DEFAULTS["dep"], interest=ADVANCED_DEFAULTS["interest"],
                      other_income=ADVANCED_DEFAULTS["other_income"], shares_cr=88.78, last_fy="FY26"):
    """
    base: dict with the last actual year's 'revenue' (core, ₹ cr).
    All rates are in % (e.g. growth=18 means 18% a year).
    Returns a DataFrame indexed by FY27, FY28 ...
    """
    rows = []
    rev = float(base["revenue"])
    for i, fy in enumerate(future_years(last_fy, years_ahead)):
        g = growth - fade * i
        if growth >= 0:            # slowing growth never turns into a decline on its own
            g = max(g, 0.0)
        rev = rev * (1 + g / 100)
        e = rev * ebitda / 100
        pbt = e + rev * other_income / 100 - rev * dep / 100 - rev * interest / 100
        pat = pbt * (1 - tax / 100)
        eps = pat / shares_cr
        rows.append({"year": fy, "growth": g, "revenue": rev, "ebitda": e, "pbt": pbt, "pat": pat,
                     "pat_margin": pat / rev * 100, "eps": eps, "dps": max(eps * payout / 100, 0.0)})
    return pd.DataFrame(rows).set_index("year")


def preset_forecast(name, base, years_ahead, shares_cr=88.78, last_fy="FY26"):
    p = SCENARIOS[name]
    return scenario_forecast(base, years_ahead, p["growth"], p["fade"], p["ebitda"], p["tax"], p["payout"],
                             shares_cr=shares_cr, last_fy=last_fy)


def trend_forecast(series, years_ahead, exclude=(), level_t=None):
    """
    Log-linear trend: log(value) = a + b * t  ->  constant growth of (e^b - 1).
    series: pandas Series indexed by 'FY20', 'FY21', ... (positive values)
    exclude: years left out of the fit (e.g. the COVID year FY21)
    Returns (history_fit DataFrame, forecast DataFrame, info dict)
    """
    s = series.astype(float)
    idx = list(s.index)
    t_all = np.arange(len(idx), dtype=float)
    use = [i for i, y in enumerate(idx) if y not in exclude and s.iloc[i] > 0]
    t = t_all[use]
    y = np.log(s.values[use])
    n = len(t)
    b, a = np.polyfit(t, y, 1)
    fitted = a + b * t
    resid = y - fitted
    dof = max(n - 2, 1)
    se = math.sqrt(float((resid ** 2).sum()) / dof) if n > 2 else 0.0
    tval = level_t or _T80.get(dof, 1.36)
    t_mean = t.mean()
    sxx = float(((t - t_mean) ** 2).sum()) or 1.0
    ss_tot = float(((y - y.mean()) ** 2).sum()) or 1.0
    r2 = 1 - float((resid ** 2).sum()) / ss_tot

    hist = pd.DataFrame({"actual": s.values, "trend": np.exp(a + b * t_all)}, index=idx)
    fut_years = future_years(idx[-1], years_ahead)
    t_f = np.arange(len(idx), len(idx) + years_ahead, dtype=float)
    mid = a + b * t_f
    half = tval * se * np.sqrt(1 + 1 / n + (t_f - t_mean) ** 2 / sxx)
    fc = pd.DataFrame({"forecast": np.exp(mid), "low": np.exp(mid - half), "high": np.exp(mid + half)},
                      index=fut_years)
    info = {"growth": (math.exp(b) - 1) * 100, "r2": r2, "n": n, "excluded": list(exclude)}
    return hist, fc, info


def sensitivity(base, years_ahead, growth_list, margin_list, preset="Base", shares_cr=88.78, last_fy="FY26"):
    """Net profit in the final forecast year for each (growth, margin) pair."""
    p = SCENARIOS[preset]
    grid = {}
    for m in margin_list:
        col = []
        for g in growth_list:
            df = scenario_forecast(base, years_ahead, g, p["fade"], m, p["tax"], p["payout"],
                                   shares_cr=shares_cr, last_fy=last_fy)
            col.append(df["pat"].iloc[-1])
        grid[m] = col
    return pd.DataFrame(grid, index=growth_list)
