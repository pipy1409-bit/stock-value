import subprocess
subprocess.run(["pip", "install", "requests", "-q"])

FMP_API_KEY = "AtCSFDWZa7831zCT8kl1gMpsn5cSMfl4"

TICKER           = "VG"
YEARS            = 3
DISCOUNT_RATE    = 0.10
TERMINAL_GROWTH  = 0.03
PROJECTION_YEARS = 5

import json, requests
from datetime import datetime

BASE_URL = "https://financialmodelingprep.com/api/v3"

def fetch(endpoint, params=None):
    params = params or {}
    params["apikey"] = FMP_API_KEY
    try:
        resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("Error Message"):
            print(f"  ⚠️  API 오류: {data['Error Message']}")
            return None
        return data
    except requests.RequestException as e:
        print(f"  ❌ 네트워크 오류 [{endpoint}]: {e}")
        return None

def get_income_statements(ticker, limit=YEARS):
    data = fetch(f"income-statement/{ticker}", {"limit": limit})
    return data if data else []

def get_balance_sheets(ticker, limit=YEARS):
    data = fetch(f"balance-sheet-statement/{ticker}", {"limit": limit})
    return data if data else []

def get_cash_flows(ticker, limit=YEARS):
    data = fetch(f"cash-flow-statement/{ticker}", {"limit": limit})
    return data if data else []

def get_quote(ticker):
    data = fetch(f"quote/{ticker}")
    return data[0] if data else {}

def get_profile(ticker):
    data = fetch(f"profile/{ticker}")
    return data[0] if data else {}

def safe_div(n, d, default=None):
    try:
        return None if (not d or d == 0) else n / d
    except:
        return default

def calculate_ratios(income, balance, cash_flow, quote):
    if not income or not balance or not cash_flow:
        return {}
    i, b, c = income[0], balance[0], cash_flow[0]
    cp     = quote.get("price", 0)
    shares = i.get("weightedAverageShsOut") or b.get("commonStock", 1)
    ni     = i.get("netIncome", 0)
    equity = b.get("totalStockholdersEquity", 0)
    rev    = i.get("revenue", 1)
    ocf    = c.get("operatingCashFlow", 0)
    capex  = abs(c.get("capitalExpenditure", 0))
    fcf    = ocf - capex
    ebitda = i.get("ebitda", 0)
    mc     = quote.get("marketCap", 0)
    debt   = b.get("totalDebt", 0)
    cash   = b.get("cashAndCashEquivalents", 0)
    ev     = mc + debt - cash

    return {
        "current_price": cp,
        "market_cap":    mc,
        "shares":        shares,
        "revenue":       rev,
        "net_income":    ni,
        "ebitda":        ebitda,
        "fcf":           fcf,
        "eps":           safe_div(ni, shares),
        "bps":           safe_div(equity, shares),
        "pe":            safe_div(cp, safe_div(ni, shares)) if safe_div(ni, shares) and safe_div(ni, shares) > 0 else None,
        "pb":            safe_div(cp, safe_div(equity, shares)) if safe_div(equity, shares) and safe_div(equity, shares) > 0 else None,
        "ev_ebitda":     safe_div(ev, ebitda) if ebitda and ebitda > 0 else None,
        "roe":           safe_div(ni, equity),
        "roa":           safe_div(ni, b.get("totalAssets", 1)),
        "op_margin":     safe_div(i.get("operatingIncome", 0), rev),
        "net_margin":    safe_div(ni, rev),
        "debt_ratio":    safe_div(b.get("totalLiabilities", 0), equity),
        "fcf_margin":    safe_div(fcf, rev),
        "fiscal_year":   i.get("date", "N/A"),
    }

def estimate_fcf_growth(cash_flows):
    if len(cash_flows) < 2:
        return 0.05
    fcfs = [(c.get("operatingCashFlow",0) - abs(c.get("capitalExpenditure",0)))
            for c in cash_flows[::-1]]
    s, e = fcfs[0], fcfs[-1]
    if s <= 0 or e <= 0:
        return 0.05
    cagr = (e / s) ** (1 / (len(fcfs)-1)) - 1
    return max(-0.10, min(0.30, cagr))

def dcf_valuation(cash_flows, balance, quote,
                  discount_rate=DISCOUNT_RATE,
                  terminal_growth=TERMINAL_GROWTH,
                  projection_years=PROJECTION_YEARS):
    if not cash_flows or not balance:
        return {}
    c0, b0   = cash_flows[0], balance[0]
    base_fcf = c0.get("operatingCashFlow",0) - abs(c0.get("capitalExpenditure",0))
    g        = estimate_fcf_growth(cash_flows)
    shares   = quote.get("sharesOutstanding", 1) or 1
    debt     = b0.get("totalDebt", 0)
    cash     = b0.get("cashAndCashEquivalents", 0)

    proj, pvs = [], []
    for t in range(1, projection_years + 1):
        blend  = t / projection_years
        g_t    = g * (1 - blend) + terminal_growth * blend
        fcf_t  = base_fcf * ((1 + g_t) ** t)
        pv_t   = fcf_t / ((1 + discount_rate) ** t)
        proj.append(round(fcf_t))
        pvs.append(round(pv_t))

    tv    = proj[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    pv_tv = tv / ((1 + discount_rate) ** projection_years)
    ev    = sum(pvs) + pv_tv
    eq    = ev - debt + cash
    iv    = safe_div(eq, shares)

    return {
        "base_fcf": base_fcf, "fcf_growth_rate": g,
        "projected_fcfs": proj, "pv_fcfs": pvs,
        "terminal_value": round(tv), "pv_terminal": round(pv_tv),
        "enterprise_value": round(ev), "equity_value": round(eq),
        "intrinsic_value": round(iv, 2) if iv else None,
        "discount_rate": discount_rate, "terminal_growth": terminal_growth,
    }

def scenario_analysis(cash_flows, balance, quote):
    scenarios = {
        "강세 (Bull)": {"discount_rate": 0.08, "terminal_growth": 0.04},
        "기본 (Base)": {"discount_rate": 0.10, "terminal_growth": 0.03},
        "약세 (Bear)": {"discount_rate": 0.12, "terminal_growth": 0.02},
    }
    return {name: dcf_valuation(cash_flows, balance, quote, **p).get("intrinsic_value")
            for name, p in scenarios.items()}

def investment_recommendation(ratios, dcf, profile):
    score, reasons, warnings = 0, [], []
    cp       = ratios.get("current_price", 0)
    intrinsic = dcf.get("intrinsic_value")

    if intrinsic and cp > 0:
        upside = (intrinsic - cp) / cp
        if upside > 0.30:   score += 35; reasons.append(f"DCF 대비 {upside:.1%} 저평가")
        elif upside > 0.10: score += 20; reasons.append(f"DCF 대비 {upside:.1%} 소폭 저평가")
        elif upside > -0.10:score += 10; reasons.append("DCF 대비 적정 수준")
        else: warnings.append(f"DCF 대비 {abs(upside):.1%} 고평가")

    roe = ratios.get("roe") or 0
    if roe > 0.20:   score += 25; reasons.append(f"우수한 ROE {roe:.1%}")
    elif roe > 0.10: score += 15; reasons.append(f"양호한 ROE {roe:.1%}")
    elif roe > 0:    score += 5
    else: warnings.append(f"마이너스 ROE ({roe:.1%})")

    pe = ratios.get("pe")
    if pe and 0 < pe < 15:   score += 20; reasons.append(f"낮은 P/E {pe:.1f}배")
    elif pe and pe < 25:     score += 10; reasons.append(f"적정 P/E {pe:.1f}배")
    elif pe and pe >= 25:    warnings.append(f"높은 P/E {pe:.1f}배")

    fm = ratios.get("fcf_margin") or 0
    if fm > 0.15:   score += 20; reasons.append(f"강력한 FCF 마진 {fm:.1%}")
    elif fm > 0.05: score += 12; reasons.append(f"양호한 FCF 마진 {fm:.1%}")
    elif fm > 0:    score += 5
    else: warnings.append("FCF 마이너스 — 현금 소진 주의")

    dr = ratios.get("debt_ratio") or 0
    if dr > 3.0:   score -= 10; warnings.append(f"과도한 부채비율 {dr:.1f}배")
    elif dr > 1.5: score -= 5;  warnings.append(f"높은 부채비율 {dr:.1f}배")

    if score >= 65:   action, conv = "✅ 매수 (BUY)",            "고확신" if score >= 80 else "중확신"
    elif score >= 40: action, conv = "🟡 보유 (HOLD)",           "중립"
    else:             action, conv = "🔴 매도 / 관망 (SELL)",    "저확신"

    upside_pct = round((intrinsic - cp) / cp * 100, 1) if (intrinsic and cp) else None
    return {
        "score": score, "action": action, "conviction": conv,
        "target_price": round(intrinsic, 2) if intrinsic else None,
        "upside_pct": upside_pct,
        "reasons": reasons, "warnings": warnings,
    }

def fmt_m(n):  return f"${n/1e6:,.1f}M" if n else "N/A"
def fmt_pct(n): return f"{n:.1%}" if n is not None else "N/A"
def fmt_x(n):   return f"{n:.1f}x" if n is not None else "N/A"

def print_report(ticker, profile, ratios, dcf, scenarios, rec, income, cash_flow):
    company = profile.get("companyName", ticker)
    now     = datetime.now().strftime("%Y-%m-%d %H:%M")
    W = 68
    print("\n" + "="*W)
    print(f"  📊  {company} ({ticker})  종합 분석 리포트".center(W))
    print(f"  생성: {now}".center(W))
    print("="*W)
    print(f"  섹터: {profile.get('sector','N/A')}  |  거래소: {profile.get('exchangeShortName','N/A')}")
    print("-"*W)

    print(f"\n[1] 최근 {YEARS}년 실적 추이")
    print(f"  {'연도':^6}  {'매출':>12}  {'순이익':>12}  {'FCF':>12}  {'순이익률':>8}")
    print(f"  {'─'*6}  {'─'*12}  {'─'*12}  {'─'*12}  {'─'*8}")
    pairs = list(zip(income[::-1], cash_flow[::-1]))
    for i_row, c_row in pairs:
        rev = i_row.get("revenue",0)
        ni  = i_row.get("netIncome",0)
        fcf = c_row.get("operatingCashFlow",0) - abs(c_row.get("capitalExpenditure",0))
        nm  = safe_div(ni, rev, 0)*100 if rev else 0
        yr  = i_row.get("date","?")[:4]
        print(f"  {yr:^6}  {fmt_m(rev):>12}  {fmt_m(ni):>12}  {fmt_m(fcf):>12}  {nm:>7.1f}%")

    print(f"\n[2] 핵심 재무비율")
    for name, val in [
        ("현재 주가",    f"${ratios.get('current_price',0):,.2f}"),
        ("시가총액",     fmt_m(ratios.get("market_cap"))),
        ("P/E",          fmt_x(ratios.get("pe"))),
        ("P/B",          fmt_x(ratios.get("pb"))),
        ("EV/EBITDA",    fmt_x(ratios.get("ev_ebitda"))),
        ("ROE",          fmt_pct(ratios.get("roe"))),
        ("ROA",          fmt_pct(ratios.get("roa"))),
        ("영업이익률",   fmt_pct(ratios.get("op_margin"))),
        ("순이익률",     fmt_pct(ratios.get("net_margin"))),
        ("FCF 마진",     fmt_pct(ratios.get("fcf_margin"))),
        ("부채비율",     fmt_x(ratios.get("debt_ratio"))),
    ]:
        print(f"  {name:<12}: {val}")

    print(f"\n[3] DCF 가치평가  (할인율 {DISCOUNT_RATE:.0%} | 터미널 성장률 {TERMINAL_GROWTH:.0%})")
    print(f"  기준 FCF: {fmt_m(dcf.get('base_fcf'))}  |  추정 성장률: {dcf.get('fcf_growth_rate',0):.1%}")
    print(f"\n  {'연도':^4}  {'예상 FCF':>14}  {'현재가치(PV)':>14}")
    for t, (pf, pv) in enumerate(zip(dcf.get("projected_fcfs",[]), dcf.get("pv_fcfs",[])), 1):
        print(f"  Y+{t:<3}  {fmt_m(pf):>14}  {fmt_m(pv):>14}")
    print(f"  터미널           {fmt_m(dcf.get('pv_terminal')):>14}")
    print(f"  {'─'*40}")
    iv = dcf.get("intrinsic_value")
    cp = ratios.get("current_price", 0)
    print(f"  기업가치(EV)     {fmt_m(dcf.get('enterprise_value')):>14}")
    if iv:
        upside = (iv - cp) / cp * 100 if cp else 0
        arrow  = "▲" if upside > 0 else "▼"
        print(f"\n  🎯 DCF 내재가치: ${iv:,.2f}  ({arrow} {abs(upside):.1f}%  {'저평가' if upside>0 else '고평가'})")

    print(f"\n[4] 시나리오별 내재가치")
    for sname, sval in scenarios.items():
        if sval and cp:
            u = (sval - cp) / cp * 100
            arrow = "▲" if u > 0 else "▼"
            print(f"  {sname:<16}: ${sval:,.2f}  ({arrow}{abs(u):.0f}%)")
        else:
            print(f"  {sname:<16}: N/A")

    print(f"\n{'='*W}")
    print("  [ 최종 투자 추천 ]".center(W))
    print(f"{'='*W}")
    print(f"  판정    :  {rec['action']}")
    print(f"  확신도  :  {rec['conviction']}  (스코어 {rec['score']}/100)")
    tp = rec.get("target_price")
    up = rec.get("upside_pct")
    if tp:
        sign = "+" if (up or 0) > 0 else ""
        print(f"  목표가  :  ${tp:,.2f}  (현재가 대비 {sign}{up:.1f}%)" if up is not None else f"  목표가: ${tp:,.2f}")
    if rec.get("reasons"):
        print("\n  ✅ 매수 근거")
        for r in rec["reasons"]: print(f"     • {r}")
    if rec.get("warnings"):
        print("\n  ⚠️  리스크")
        for w in rec["warnings"]: print(f"     • {w}")

    print(f"\n{'─'*W}")
    print("  ※ 본 리포트는 정보 제공 목적이며 투자 권고가 아닙니다.")
    print(f"{'='*W}\n")

print(f"🔍  {TICKER} 분석 시작...")
income    = get_income_statements(TICKER, YEARS)
balance   = get_balance_sheets(TICKER, YEARS)
cash_flow = get_cash_flows(TICKER, YEARS)
quote     = get_quote(TICKER)
profile   = get_profile(TICKER)

if not income:
    print("❌ 데이터를 가져오지 못했습니다. 티커 심볼과 API 키를 확인하세요.")
else:
    print(f"✅ 데이터 수집 완료 ({len(income)}년치)")
    ratios    = calculate_ratios(income, balance, cash_flow, quote)
    dcf       = dcf_valuation(cash_flow, balance, quote)
    scenarios = scenario_analysis(cash_flow, balance, quote)
    rec       = investment_recommendation(ratios, dcf, profile)
    print_report(TICKER, profile, ratios, dcf, scenarios, rec, income, cash_flow)