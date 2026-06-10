"""
Market Vital Signs — Streamlit 웹앱
지옥변곡점이 시장을 보는 시선

설치:  pip3 install streamlit yfinance plotly pandas openpyxl
실행:  streamlit run app.py
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import io

# ══════════════════════════════════════════════════════
# 페이지 설정
# ══════════════════════════════════════════════════════
st.set_page_config(
    page_title="Market Vital Signs",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════
# 비밀번호 인증
# ══════════════════════════════════════════════════════
def check_password():
    """비밀번호 확인 — Streamlit secrets 또는 하드코딩 지원"""

    # Streamlit Cloud secrets 에 PASSWORD 설정된 경우 우선 사용
    # (로컬 실행 시 fallback으로 하드코딩 비밀번호 사용)
    try:
        correct_pw = st.secrets["PASSWORD"]
    except Exception:
        correct_pw = "jigok2024"   # ← 원하는 비밀번호로 변경

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # 로그인 화면
    col_c, col_f, col_c2 = st.columns([1, 2, 1])
    with col_f:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🩺 지옥변곡점이 시장을 보는 시선")
        st.markdown("<br>", unsafe_allow_html=True)
        pw = st.text_input("비밀번호를 입력하세요", type="password",
                           placeholder="Password")
        if st.button("입장", use_container_width=True):
            if pw == correct_pw:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
    return False

if not check_password():
    st.stop()

st.markdown("""
<style>
  .block-container { padding-top: 1.2rem; }
  .vital-card {
    background: #f0f2f6;
    border-radius: 8px;
    padding: 6px 8px;
    border: 1px solid #e0e0e0;
    text-align: center;
  }
  .vital-label  { font-size: 9px;  color: #555; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .vital-value  { font-size: 12px; color: #111; font-weight: 700; margin: 2px 0; white-space: nowrap; }
  .vital-delta-up   { font-size: 9px; color: #0a8a0a; }
  .vital-delta-down { font-size: 9px; color: #cc2222; }
  .vital-fin    { font-size: 8px; color: #555; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# 설정
# ══════════════════════════════════════════════════════
TICKERS = {
    "NQ":  ("NQ=F",     "나스닥100 선물",    "수축기 혈압", "pt",    "#E24B4A"),
    "SP":  ("ES=F",     "S&P500 선물",      "이완기 혈압", "pt",    "#F0A500"),
    "TNX": ("^TNX",     "미국채 10년물",    "심박수",      "%",     "#8E44AD"),
    "DXY": ("DX-Y.NYB", "달러 인덱스",      "체온",        "DXY",   "#4A90D9"),
    "VIX": ("^VIX",     "VIX 변동성",       "호흡수",      "",      "#27AE60"),
    "WTI": ("CL=F",     "WTI 유가 선물",     "혈당",        "$/bbl", "#1A3A6B"),
    "GLD": ("GC=F",     "금 선물",          "전통자산",    "$/oz",  "#FFD700"),
    "BTC": ("BTC-USD",  "비트코인",          "신흥자산",    "$",     "#FF69B4"),
}

SCALES = {
    "BP_L": 100,   "BP_H": 35000,
    "TNX_L": 0,    "TNX_H": 10,
    "DXY_L": 50,   "DXY_H": 200,
    "VIX_L": 5,    "VIX_H": 100,
    "WTI_L": 0,    "WTI_H": 200,
    "GLD_L": 200,  "GLD_H": 6000,
    "BTC_L": 0,    "BTC_H": 140000,
}

THRESHOLDS = {
    "NQ":  {"warn": 17000, "danger": 15000, "inv": False},
    "SP":  {"warn": 4800,  "danger": 4200,  "inv": False},
    "TNX": {"warn": 4.5,   "danger": 5.2,   "inv": True},
    "DXY": {"warn": 106,   "danger": 110,   "inv": True},
    "VIX": {"warn": 22,    "danger": 35,    "inv": True},
    "WTI": {"warn": 60,    "danger": 50,    "inv": False},
    "GLD": {"warn": 2500,  "danger": 3500,  "inv": True},
    "BTC": {"warn": 30000, "danger": 15000, "inv": False},
}

CRISIS = [
    ("1997-07-01", "1998-09-30", "아시아금융위기"),
    ("2000-03-01", "2002-10-31", "닷컴버블붕괴"),
    ("2007-10-01", "2009-03-31", "글로벌금융위기"),
    ("2010-04-01", "2010-07-31", "플래시크래시"),
    ("2011-07-01", "2011-10-31", "유럽재정위기"),
    ("2015-08-01", "2016-02-29", "차이나쇼크"),
    ("2018-09-01", "2018-12-31", "미중무역전쟁"),
    ("2020-02-01", "2020-04-30", "코로나19"),
    ("2022-01-01", "2022-10-31", "금리인상긴축"),
    ("2025-02-01", "2025-05-31", "트럼프관세충격"),
]

PERIOD_OPTIONS = {
    "1주": "5d", "2주": "10d", "1개월": "1mo",
    "3개월": "3mo", "6개월": "6mo",
    "1년": "1y", "3년": "3y", "5년": "5y",
    "10년": "10y", "20년": "20y",
    "1990년~": "1990", "1995년~": "1995", "2000년~": "2000",
    "2005년~": "2005", "2010년~": "2010", "최대": "max",
}

def grade(key, val):
    t = THRESHOLDS[key]
    if t["inv"]:
        if val >= t["danger"]: return "🔴 위험"
        if val >= t["warn"]:   return "🟡 주의"
    else:
        if val <= t["danger"]: return "🔴 위험"
        if val <= t["warn"]:   return "🟡 주의"
    return "🟢 정상"

def grade_color(key, val):
    g = grade(key, val)
    return "#E24B4A" if "위험" in g else "#E8890C" if "주의" in g else "#27AE60"


# ══════════════════════════════════════════════════════
# 데이터 캐시
# ══════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════

# WTI 현물/선물 데이터
# ══════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def load_wti_data(api_key: str):
    """EIA API로 WTI 현물(주간) + yfinance로 WTI 선물 로드"""
    import requests

    # WTI 현물 (EIA, RWTC)
    spot_df = None
    try:
        url = (
            "https://api.eia.gov/v2/petroleum/pri/spt/data/"
            "?frequency=daily&data[0]=value"
            "&facets[series][]=RWTC"
            "&sort[0][column]=period&sort[0][direction]=desc"
            f"&offset=0&length=5000&api_key={api_key}"
        )
        r = requests.get(url, timeout=10)
        data = r.json()
        rows = data["response"]["data"]
        df = pd.DataFrame(rows)[["period","value"]].copy()
        df["Date"] = pd.to_datetime(df["period"])
        df["Spot"] = pd.to_numeric(df["value"], errors="coerce")
        spot_df = df[["Date","Spot"]].dropna().set_index("Date").sort_index()
    except:
        pass

    # WTI 선물 (yfinance CL=F)
    fut_df = None
    try:
        raw = yf.download("CL=F", period="max", interval="1d",
                          progress=False, auto_adjust=True)
        if not raw.empty:
            if isinstance(raw.columns, pd.MultiIndex):
                s = raw[("Close","CL=F")].dropna()
            else:
                s = raw["Close"].dropna()
            fut_df = s.astype(float).to_frame("Futures")
            fut_df.index = pd.to_datetime(fut_df.index).tz_localize(None)
    except:
        pass

    return spot_df, fut_df


@st.cache_data(ttl=3600, show_spinner=False)
def load_sector_data(period_key: str):
    """섹터 ETF 200일 이동평균 대비 편차 시계열 로드"""
    SECTOR_TICKERS = {
        "QQQ":  "나스닥100",
        "SPY":  "S&P500",
        "DIA":  "다우존스",
        "IWM":  "러셀2000",
        "SOXX": "반도체",
        "XLK":  "기술",
        "XLC":  "통신",
        "XLY":  "임의소비재",
        "XLF":  "금융",
        "XLV":  "헬스케어",
        "XLE":  "에너지",
        "XLI":  "산업재",
        "XLB":  "소재",
        "XLU":  "유틸리티",
        "XLRE": "부동산",
        "XLP":  "필수소비재",
    }
    # 시각적으로 구분되는 16색 팔레트 (색상환 균등 분배)
    PALETTE = [
        "#E24B4A","#4A90D9","#27AE60","#F1C40F","#8E44AD","#E67E22",
        "#1ABC9C","#E74C3C","#3498DB","#2ECC71","#9B59B6","#F39C12",
        "#16A085","#D35400","#C0392B","#2980B9",
    ]
    series = {}
    for idx, (ticker, label) in enumerate(SECTOR_TICKERS.items()):
        color = PALETTE[idx % len(PALETTE)]
        try:
            use_start = period_key.isdigit()
            if use_start:
                df = yf.download(ticker, start=f"{period_key}-01-01",
                                 interval="1d", progress=False, auto_adjust=True)
            else:
                df = yf.download(ticker, period=period_key if period_key != "max" else "max",
                                 interval="1d", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex):
                s = df[("Close", ticker)].dropna()
            else:
                s = df["Close"].dropna()
            s = s.astype(float)
            ma200 = s.rolling(200, min_periods=50).mean()
            dev = ((s - ma200) / ma200 * 100).dropna()
            series[ticker] = {
                "label": label,
                "color": color,   # PALETTE에서 자동 배정
                "dev":   dev,
                "cur":   float(dev.iloc[-1]),
            }
        except:
            pass
    return series

def make_sector_fig(sector_data, period_label=""):
    """⑦ 섹터별 200일 편차% 시계열 라인 차트"""
    if not sector_data:
        return go.Figure()

    fig = go.Figure()

    for ticker, info in sector_data.items():
        dev = info["dev"]
        # period에 맞게 슬라이싱
        dev_plot = dev
        dates_s = [d.strftime("%Y-%m-%d") for d in dev_plot.index]
        cur = info["cur"]
        fig.add_trace(go.Scatter(
            x=dates_s, y=[round(v, 2) for v in dev.values.tolist()],
            name=f"{info['label']} ({ticker})  {cur:+.2f}%",
            mode="lines",
            line=dict(color=info["color"], width=1.8),
            hovertemplate=f"<b>{info['label']}</b>: %{{y:+.2f}}%<br>%{{x}}<extra></extra>",
        ))

    # 기준선
    fig.add_hline(y=20,  line_color="rgba(226,75,74,0.35)",
                  line_width=1, line_dash="dot",
                  annotation_text="+20% 과열",
                  annotation_font=dict(size=8, color="#E24B4A"),
                  annotation_position="right")
    fig.add_hline(y=-20, line_color="rgba(74,144,217,0.35)",
                  line_width=1, line_dash="dot",
                  annotation_text="-20% 침체",
                  annotation_font=dict(size=8, color="#4A90D9"),
                  annotation_position="right")
    fig.add_hline(y=0,   line_color="rgba(150,150,150,0.4)",
                  line_width=1)

    # 배경
    fig.add_hrect(y0=20,  y1=80,  fillcolor="rgba(226,75,74,0.04)",  line_width=0)
    fig.add_hrect(y0=-80, y1=-20, fillcolor="rgba(74,144,217,0.04)", line_width=0)

    # 날짜 범위
    all_dates = []
    for info in sector_data.values():
        all_dates.extend(info["dev"].index.tolist())
    if all_dates:
        d0 = min(all_dates).strftime("%Y-%m-%d")
        d1 = max(all_dates).strftime("%Y-%m-%d")
    else:
        d0, d1 = dates[0], dates[-1]

    fig.update_layout(
        title=f"⑦ 섹터별 200일 이동평균 대비 편차% 시계열  [{period_label}]",
        height=580, hovermode="x unified",
        plot_bgcolor="#fafafa", paper_bgcolor="white",
        margin=dict(l=55, r=10, t=50, b=80),
        legend=dict(orientation="h", x=0, y=-0.18,
                    font=dict(size=10, color="#111"),
                    bgcolor="rgba(255,255,255,0.85)"),
        yaxis=dict(
            title="200일 MA 대비 편차 (%)",
            title_font=dict(size=10, color="#555"),
            tickfont=dict(size=9, color="#111"),
            tickformat=".2f",
            ticksuffix="%",
            gridcolor="rgba(180,180,180,0.15)",
            zeroline=True, zerolinecolor="rgba(150,150,150,0.4)",
        ),
        xaxis=dict(
            tickfont=dict(size=9, color="#111"),
            gridcolor="rgba(180,180,180,0.18)",
            range=[d0, d1],
        ),
    )
    return fig


@st.cache_data(ttl=3600, show_spinner=False)
def load_bond_data(period_key: str):
    """채권 ETF 가격 + 200일 이동평균 대비 편차 시계열"""
    BOND_TICKERS = {
        "SHY":  ("단기채 1-3년",  "#4A90D9"),
        "IEF":  ("중기채 7-10년", "#27AE60"),
        "TLT":  ("장기채 20년+",  "#8E44AD"),
        "HYG":  ("하이일드 회사채","#E24B4A"),
        "JNK":  ("정크본드",       "#F1C40F"),
        "LQD":  ("투자등급 회사채","#E67E22"),
    }
    use_start = period_key.isdigit()
    series = {}
    for ticker, (label, color) in BOND_TICKERS.items():
        try:
            if use_start:
                df = yf.download(ticker, start=f"{period_key}-01-01",
                                 interval="1d", progress=False, auto_adjust=True)
            else:
                df = yf.download(ticker, period=period_key,
                                 interval="1d", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex):
                s = df[("Close", ticker)].dropna()
            else:
                s = df["Close"].dropna()
            s = s.astype(float)
            # 200일 MA는 항상 충분한 데이터로 계산 (ma용 전체 다운 후 슬라이싱)
            ma200 = s.rolling(200, min_periods=50).mean()
            dev   = ((s - ma200) / ma200 * 100).dropna()
            series[ticker] = {
                "label": label,
                "color": color,
                "price": s,
                "dev":   dev,
                "cur_price": float(s.iloc[-1]),
                "cur_dev":   float(dev.iloc[-1]),
            }
        except:
            pass
    return series

def make_bond_fig(bond_data, period_label=""):
    """⑧ 채권 ETF — 가격 시계열 + 200일 편차%"""
    if not bond_data:
        return go.Figure(), go.Figure()

    # 차트 A: 가격 정규화 (시작점 100 기준)
    fig_price = go.Figure()
    for ticker, info in bond_data.items():
        s = info["price"]
        normalized = (s / float(s.iloc[0]) * 100)
        dates_s = [d.strftime("%Y-%m-%d") for d in s.index]
        fig_price.add_trace(go.Scatter(
            x=dates_s, y=normalized.values.tolist(),
            name=f"{ticker} {info['label']}",
            mode="lines",
            line=dict(color=info["color"], width=1.8),
            hovertemplate=f"<b>{ticker}</b>: %{{y:.1f}}<br>%{{x}}<extra></extra>",
        ))
    fig_price.add_hline(y=100, line_color="rgba(150,150,150,0.4)",
                        line_width=1, line_dash="dot")
    fig_price.update_layout(
        title=f"⑧-A 채권 ETF 가격 (시작점=100 정규화)  [{period_label}]",
        height=420, hovermode="x unified",
        plot_bgcolor="#fafafa", paper_bgcolor="white",
        margin=dict(l=55, r=10, t=50, b=60),
        legend=dict(orientation="h", x=0, y=-0.18,
                    font=dict(size=10, color="#111"),
                    bgcolor="rgba(255,255,255,0.85)"),
        yaxis=dict(
            title="정규화 가격 (시작=100)",
            tickfont=dict(size=9, color="#111"),
            gridcolor="rgba(180,180,180,0.15)",
        ),
        xaxis=dict(tickfont=dict(size=9, color="#111"),
                   gridcolor="rgba(180,180,180,0.18)"),
    )

    # 차트 B: 200일 편차%
    fig_dev = go.Figure()
    for ticker, info in bond_data.items():
        dev = info["dev"]
        dates_s = [d.strftime("%Y-%m-%d") for d in dev.index]
        fig_dev.add_trace(go.Scatter(
            x=dates_s, y=[round(v, 2) for v in dev.values.tolist()],
            name=f"{ticker} ({info['cur_dev']:+.2f}%)",
            mode="lines",
            line=dict(color=info["color"], width=1.8),
            hovertemplate=f"<b>{ticker}</b>: %{{y:+.2f}}%<br>%{{x}}<extra></extra>",
        ))
    fig_dev.add_hline(y=0,   line_color="rgba(150,150,150,0.4)", line_width=1)
    fig_dev.add_hline(y=10,  line_color="rgba(226,75,74,0.3)",
                      line_width=0.8, line_dash="dot",
                      annotation_text="+10%", annotation_font=dict(size=8))
    fig_dev.add_hline(y=-10, line_color="rgba(74,144,217,0.3)",
                      line_width=0.8, line_dash="dot",
                      annotation_text="-10%", annotation_font=dict(size=8))
    fig_dev.update_layout(
        title=f"⑧-B 채권 ETF 200일 이동평균 대비 편차%  [{period_label}]",
        height=420, hovermode="x unified",
        plot_bgcolor="#fafafa", paper_bgcolor="white",
        margin=dict(l=55, r=10, t=50, b=60),
        legend=dict(orientation="h", x=0, y=-0.18,
                    font=dict(size=10, color="#111"),
                    bgcolor="rgba(255,255,255,0.85)"),
        yaxis=dict(
            title="편차 (%)", tickformat=".2f", ticksuffix="%",
            tickfont=dict(size=9, color="#111"),
            gridcolor="rgba(180,180,180,0.15)",
            zeroline=True, zerolinecolor="rgba(150,150,150,0.4)",
        ),
        xaxis=dict(tickfont=dict(size=9, color="#111"),
                   gridcolor="rgba(180,180,180,0.18)"),
    )
    return fig_price, fig_dev

def make_wti_fig(spot_df, fut_df, dates):
    """⑥ WTI 현물(EIA) vs 선물(CL=F) vs 괴리"""
    fig = go.Figure()
    dates_idx = pd.to_datetime(dates)

    spread_note = "EIA API 키 필요"

    # WTI 선물 (CL=F)
    if fut_df is not None:
        fut_reindexed = fut_df["Futures"].reindex(dates_idx).ffill()
        fig.add_trace(go.Scatter(
            x=dates, y=fut_reindexed.values.tolist(),
            name="WTI 선물 (CL=F)",
            mode="lines",
            line=dict(color="#1A3A6B", width=2.0),
            hovertemplate="<b>WTI 선물</b>: $%{y:.2f}<br>%{x}<extra></extra>",
        ))
    else:
        fut_reindexed = None

    # WTI 현물 (EIA 주간)
    if spot_df is not None:
        spot_reindexed = spot_df["Spot"].reindex(dates_idx).ffill(limit=7)
        fig.add_trace(go.Scatter(
            x=dates, y=spot_reindexed.values.tolist(),
            name="WTI 현물 (EIA Cushing)",
            mode="lines",
            line=dict(color="#E67E22", width=2.0),
            hovertemplate="<b>WTI 현물</b>: $%{y:.2f}<br>%{x}<extra></extra>",
        ))

        if fut_reindexed is not None:
            spread = spot_reindexed - fut_reindexed
            fig.add_trace(go.Scatter(
                x=dates, y=spread.values.tolist(),
                name="괴리 (현물 - 선물)",
                mode="lines",
                line=dict(color="#8E44AD", width=1.5, dash="dash"),
                yaxis="y2",
                hovertemplate="<b>괴리</b>: $%{y:.2f}<br>%{x}<extra></extra>",
            ))
            fig.add_hline(y=0, line_color="rgba(150,150,150,0.4)",
                          line_width=1, line_dash="dot", yref="y2")

            cur_spot   = float(spot_reindexed.dropna().iloc[-1])
            cur_fut    = float(fut_reindexed.dropna().iloc[-1])
            cur_spread = cur_spot - cur_fut
            spread_note = (
                f"현물 ${cur_spot:.1f} / 선물 ${cur_fut:.1f} / "
                f"괴리 ${cur_spread:+.1f}"
            )

    fig.update_layout(
        title=f"⑥ WTI 유가 — 현물(EIA) vs 선물(CL=F) vs 괴리  ({spread_note})",
        height=480, hovermode="x unified",
        plot_bgcolor="#fafafa", paper_bgcolor="white",
        margin=dict(l=55, r=80, t=50, b=60),
        legend=dict(orientation="h", x=0, y=-0.15,
                    font=dict(size=10, color="#111")),
        yaxis=dict(
            title="가격 ($/bbl)", tickprefix="$",
            tickfont=dict(color="#111", size=9),
            gridcolor="rgba(180,180,180,0.15)",
        ),
        yaxis2=dict(
            title="괴리 ($)", tickprefix="$",
            title_font=dict(color="#8E44AD", size=10),
            tickfont=dict(color="#8E44AD", size=9),
            overlaying="y", side="right", showgrid=False,
            zeroline=True, zerolinecolor="rgba(142,68,173,0.3)",
        ),
        xaxis=dict(
            tickfont=dict(size=9, color="#111"),
            gridcolor="rgba(180,180,180,0.18)",
            range=[dates[0], dates[-1]],
        ),
    )
    return fig

@st.cache_data(ttl=300, show_spinner=False)
def load_data(period: str):
    def extract_close(df):
        if isinstance(df.columns, pd.MultiIndex):
            cols = [c for c in df.columns if c[0] == "Close"]
            s = df[cols[0]].squeeze()
        else:
            s = df["Close"].squeeze()
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        return s.dropna().astype(float)

    # 연도 문자열(예: "1990")이면 start 날짜 방식으로 처리
    use_start = period.isdigit()

    data = {}
    for key, (sym, *_) in TICKERS.items():
        try:
            # 1. 일별 히스토리 로드
            if use_start:
                df = yf.download(sym, start=f"{period}-01-01",
                                 interval="1d", progress=False, auto_adjust=True)
            else:
                df = yf.download(sym, period=period, interval="1d",
                                 progress=False, auto_adjust=True)
            if df.empty:
                continue
            s = extract_close(df).dropna()
            if len(s) == 0:
                continue

            # 2. 1분봉으로 당일 최신가 가져오기
            try:
                df1m = yf.download(sym, period="1d", interval="1m",
                                   progress=False, auto_adjust=True)
                if not df1m.empty:
                    s1m = extract_close(df1m).dropna()
                    if len(s1m) > 0:
                        latest_price = float(s1m.iloc[-1])
                        # 일별 Series 마지막 날짜
                        last_date = s.index[-1]
                        if hasattr(last_date, 'date'):
                            last_date = last_date.date()
                        import datetime
                        today_date = datetime.date.today()
                        # 오늘 데이터가 없으면 오늘 날짜로 추가
                        today_ts = pd.Timestamp(today_date)
                        if pd.Timestamp(last_date) < today_ts:
                            s = pd.concat([s,
                                pd.Series([latest_price],
                                          index=[today_ts],
                                          name=s.name)])
                        else:
                            # 오늘 데이터가 이미 있으면 덮어쓰기
                            s.iloc[-1] = latest_price
            except:
                pass

            data[key] = s
        except:
            pass

    if not data:
        return None, None

    # 합집합(union) 인덱스 — 데이터 없는 구간은 NaN으로 남김
    union_idx = None
    for s in data.values():
        union_idx = s.index if union_idx is None else union_idx.union(s.index)

    # 각 시리즈를 union 인덱스에 맞춰 reindex (없는 구간 NaN 유지, ffill 제한)
    aligned = {}
    for k, s in data.items():
        reindexed = s.reindex(union_idx)
        # ffill은 최대 5일만 (주말·공휴일 보정용), 그 이상은 NaN 유지
        reindexed = reindexed.ffill(limit=5)
        aligned[k] = reindexed.astype(float)

    dates = [d.strftime("%Y-%m-%d") for d in union_idx]
    return aligned, dates


def add_crisis(fig, dates):
    for start, end, label in CRISIS:
        if start > dates[-1] or end < dates[0]: continue
        x0 = max(start, dates[0])
        x1 = min(end,   dates[-1])
        fig.add_vrect(
            x0=x0, x1=x1,
            fillcolor="rgba(210,70,70,0.07)",
            line_width=0.4, line_color="rgba(210,70,70,0.18)",
            annotation_text=label,
            annotation_position="top left",
            annotation_font=dict(size=7, color="#c0c0c0"),
        )



# ══════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🩺 Market Vital Signs")
    st.markdown("**지옥변곡점이 시장을 보는 시선**")
    st.divider()

    period_label = st.selectbox(
        "📅 데이터 기간",
        list(PERIOD_OPTIONS.keys()),
        index=9,  # 20년 기본 (0-based)
    )
    period = PERIOD_OPTIONS[period_label]

    show_crisis = st.toggle("경제위기 구간 표시", value=True)
    show_fig3   = st.toggle("④ 통합 차트 표시",   value=True)
    show_fig5   = st.toggle("⑤ 보정 차트 표시",   value=True)
    show_fig6   = st.toggle("⑥ WTI 현물/선물 표시",   value=True)
    show_fig7   = st.toggle("⑦ 섹터별 이격 표시",    value=True)
    show_fig8   = st.toggle("⑧ 채권 ETF 표시",         value=True)

    st.divider()

    st.divider()
    # EIA API 키 (로컬 전용 — GitHub 업로드 금지)
    eia_key = "6JxDUEiHc0mBFhmdiPFlqc9Ct2ggTJuVvkY3yXOu"
    try:
        _secret = st.secrets["EIA_API_KEY"]
        if _secret:
            eia_key = _secret
    except:
        pass

    st.divider()
    st.markdown("**🔗 유용한 링크**")
    st.markdown("[🤖 Is AI Profitable Yet?](https://isaiprofitable.com)")
    st.markdown("[😨 Fear & Greed Index](https://edition.cnn.com/markets/fear-and-greed)")
    st.markdown("[🚢 힌덴부르크 오멘 (@Hindenburg0men)](https://x.com/Hindenburg0men)")

    if st.button("🔄 데이터 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"<span style='color:#111;font-size:12px'>마지막 갱신: {datetime.now().strftime('%H:%M:%S')}</span>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# 데이터 로딩
# ══════════════════════════════════════════════════════
with st.spinner("📡 Yahoo Finance에서 데이터 수신 중..."):
    A, dates = load_data(period)

if A is None:
    st.error("❌ 데이터를 불러오지 못했습니다. 인터넷 연결을 확인하고 새로고침 해주세요.")
    st.stop()

STEP = max(1, len(dates) // 800)


# ══════════════════════════════════════════════════════
# 헤더 & 진단 배너
# ══════════════════════════════════════════════════════
st.markdown(f"# 🩺 Market Vital Signs Dashboard")
st.markdown(f"<span style='color:#111;font-size:13px'>EPA-2025-0112  |  {dates[0]} ~ {dates[-1]}  |  {len(dates):,}일 ({len(dates)/252:.0f}년)</span>", unsafe_allow_html=True)




# ══════════════════════════════════════════════════════
# 지표 카드 (6개)
# ══════════════════════════════════════════════════════
# 데이터 있는 지표만 필터링
available_keys = [k for k in TICKERS if k in A]
cols = st.columns(len(available_keys))
for col_i, key in enumerate(available_keys):
    sym, fin, bio, unit, color = TICKERS[key]
    # 마지막 유효한 2개 데이터 포인트 비교 (0% 방지)
    s_valid = A[key].dropna()
    # MultiIndex 등으로 Series가 아닌 경우 대비
    def to_scalar(v):
        if hasattr(v, "values"):
            return float(v.values.flat[0])
        return float(v)
    val  = to_scalar(s_valid.iloc[-1])
    prev = to_scalar(s_valid.iloc[-2]) if len(s_valid) >= 2 else val
    pct  = round((val - prev) / prev * 100, 2) if prev != 0 else 0
    g    = grade(key, val)
    gc   = grade_color(key, val)
    delta_cls = "vital-delta-up" if pct >= 0 else "vital-delta-down"
    arrow = "▲" if pct >= 0 else "▼"
    unit_str = f" {unit}" if unit else ""
    with cols[col_i]:
        eod_note = ""
        st.markdown(f"""
<div class="vital-card">
  <div class="vital-label">{bio}</div>
  <div class="vital-fin">{fin}</div>
  <div class="vital-value">{val:,.2f}{unit_str}</div>
  <div class="{delta_cls}">{arrow} {abs(pct):.2f}%</div>
  {eod_note}
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# Figure 빌더 함수
# ══════════════════════════════════════════════════════
def make_bp_fig():
    fig = go.Figure()
    if show_crisis: add_crisis(fig, dates)
    if "NQ" in A and "SP" in A:
        nq_v = A["NQ"].values.tolist()
        sp_v = A["SP"].values.tolist()
        bx, by = [], []
        for i in range(0, len(dates), STEP):
            bx += [dates[i], dates[i], None]
            by += [sp_v[i], nq_v[i], None]
        fig.add_trace(go.Scatter(x=bx, y=by, mode="lines",
            line=dict(color="rgba(226,75,74,0.15)", width=0.9),
            showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=dates, y=nq_v, fill=None, mode="none",
            showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=dates, y=sp_v, fill="tonexty",
            fillcolor="rgba(226,75,74,0.08)", mode="none",
            showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=dates, y=nq_v,
            name="나스닥 100 (수축기 혈압)", mode="lines+markers",
            line=dict(color="#D35400", width=2.0),
            marker=dict(symbol="triangle-up", size=3, color="#E24B4A", maxdisplayed=400),
            hovertemplate="<b>나스닥</b>: %{y:,.0f} pt<br>%{x}<extra></extra>"))
        fig.add_trace(go.Scatter(x=dates, y=sp_v,
            name="S&P 500 (이완기 혈압)", mode="lines+markers",
            line=dict(color="#F0A500", width=2.0),
            marker=dict(symbol="triangle-down", size=3, color="#F0A500", maxdisplayed=400),
            hovertemplate="<b>S&P 500</b>: %{y:,.0f} pt<br>%{x}<extra></extra>"))
    fig.update_layout(
        title="① 혈압",
        height=420, hovermode="x unified",
        plot_bgcolor="#fafafa", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=45, b=40),
        legend=dict(orientation="h", x=0, y=-0.15, font=dict(size=10, color="#111")),
        yaxis=dict(title=None,
            showticklabels=False, showline=False, showgrid=True,
            gridcolor="rgba(226,75,74,0.10)",
            range=[SCALES["BP_L"], SCALES["BP_H"]], zeroline=False),
        xaxis=dict(tickfont=dict(size=9, color="#111"), gridcolor="rgba(180,180,180,0.18)",
            range=[dates[0], dates[-1]]),
    )
    return fig

def make_vital_fig():
    fig = go.Figure()
    if show_crisis: add_crisis(fig, dates)
    if "TNX" in A:
        fig.add_trace(go.Scatter(x=dates, y=A["TNX"].values.tolist(),
            name="심박수 — 미국채 10년물 (보라, 0~10%)", mode="lines+markers",
            line=dict(color="#8E44AD", width=1.8, dash="dot"),
            marker=dict(symbol="x", size=3, color="#8E44AD", maxdisplayed=400),
            yaxis="y",
            hovertemplate="<b>미국채 10년물</b>: %{y:.2f}%<br>%{x}<extra></extra>"))
    if "DXY" in A:
        fig.add_trace(go.Scatter(x=dates, y=A["DXY"].values.tolist(),
            name="체온 — 달러 인덱스 (파란, 50~200)", mode="lines+markers",
            line=dict(color="#4A90D9", width=1.8, dash="dashdot"),
            marker=dict(symbol="cross", size=3, color="#4A90D9", maxdisplayed=400),
            yaxis="y2",
            hovertemplate="<b>달러 인덱스</b>: %{y:.2f}<br>%{x}<extra></extra>"))
    if "VIX" in A:
        fig.add_trace(go.Scatter(x=dates, y=A["VIX"].values.tolist(),
            name="호흡수 — VIX (초록, 5~100)", mode="lines+markers",
            line=dict(color="#27AE60", width=1.8),
            marker=dict(symbol="diamond", size=3, color="#27AE60", maxdisplayed=400),
            yaxis="y3",
            hovertemplate="<b>VIX</b>: %{y:.1f}<br>%{x}<extra></extra>"))
    if "WTI" in A:
        fig.add_trace(go.Scatter(x=dates, y=A["WTI"].values.tolist(),
            name="혈당 — WTI 유가 선물", mode="lines+markers",
            line=dict(color="#1A3A6B", width=2.0, dash="longdash"),
            marker=dict(symbol="star", size=3, color="#1A3A6B", maxdisplayed=400),
            yaxis="y4",
            hovertemplate="<b>WTI 유가 선물</b>: $%{y:.1f}<br>%{x}<extra></extra>"))
    fig.update_layout(
        title="② 바이탈 지표",
        height=520, hovermode="x unified",
        plot_bgcolor="#fafafa", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=45, b=80),
        legend=dict(orientation="h", x=0, y=-0.18, font=dict(size=10, color="#111")),
        yaxis=dict(title=None,
            showticklabels=False, showline=False, showgrid=True,
            gridcolor="rgba(142,68,173,0.08)",
            range=[SCALES["TNX_L"], SCALES["TNX_H"]], zeroline=False),
        yaxis2=dict(title=None,
            showticklabels=False, showline=False, showgrid=False,
            range=[SCALES["DXY_L"], SCALES["DXY_H"]],
            overlaying="y", side="right"),
        yaxis3=dict(title=None,
            showticklabels=False, showline=False, showgrid=False,
            range=[SCALES["VIX_L"], SCALES["VIX_H"]],
            overlaying="y", side="right"),
        yaxis4=dict(title=None,
            showticklabels=False, showline=False, showgrid=False,
            range=[SCALES["WTI_L"], SCALES["WTI_H"]],
            overlaying="y", side="right"),
        xaxis=dict(tickfont=dict(size=9, color="#111"), gridcolor="rgba(180,180,180,0.18)",
            range=[dates[0], dates[-1]]),
    )
    return fig


def make_asset_fig():
    """③ 전통자산(금) + 신흥자산(BTC) 전용 차트"""
    fig = go.Figure()
    if show_crisis: add_crisis(fig, dates)

    if "GLD" in A:
        fig.add_trace(go.Scatter(
            x=dates, y=A["GLD"].values.tolist(),
            name="전통자산 — 금 선물 ($/oz)",
            mode="lines+markers",
            line=dict(color="#FFD700", width=2.2),
            marker=dict(symbol="hexagon", size=3, color="#FFD700", maxdisplayed=400),
            yaxis="y",
            hovertemplate="<b>금 선물</b>: $%{y:,.0f}/oz<br>%{x}<extra></extra>",
        ))

    if "BTC" in A:
        fig.add_trace(go.Scatter(
            x=dates, y=A["BTC"].values.tolist(),
            name="신흥자산 — 비트코인 ($)",
            mode="lines+markers",
            line=dict(color="#FF69B4", width=2.2, dash="dash"),
            marker=dict(symbol="circle", size=3, color="#FF69B4", maxdisplayed=400),
            yaxis="y2",
            hovertemplate="<b>비트코인</b>: $%{y:,.0f}<br>%{x}<extra></extra>",
        ))

    fig.update_layout(
        title="③ 자산 차트",
        height=460, hovermode="x unified",
        plot_bgcolor="#fafafa", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=45, b=60),
        legend=dict(orientation="h", x=0, y=-0.18, font=dict(size=10, color="#111")),
        yaxis=dict(
            title=None,
            showticklabels=False, showline=False, showgrid=True,
            gridcolor="rgba(255,215,0,0.15)",
            range=[SCALES["GLD_L"], SCALES["GLD_H"]], zeroline=False,
        ),
        yaxis2=dict(
            title=None,
            showticklabels=False, showline=False, showgrid=False,
            range=[SCALES["BTC_L"], SCALES["BTC_H"]],
            overlaying="y", side="right",
        ),
        xaxis=dict(
            tickfont=dict(size=9, color="#111"),
            gridcolor="rgba(180,180,180,0.18)",
            range=[dates[0], dates[-1]],
        ),
    )
    return fig


def calc_deviation(series, window=200):
    """이동평균 대비 편차 % 계산. 값 없는 구간은 NaN 유지."""
    s = series.copy()
    ma = s.rolling(window, min_periods=max(20, window//4)).mean()
    dev = ((s - ma) / ma * 100).round(2)
    return dev

def make_deviation_fig():
    """⑤ 보정 차트
    혈압(나스닥/S&P): 200일 이동평균 대비 편차 % — 좌축
    나머지 지표: 원값 — 각자 우측 오버레이 축
    """
    fig = go.Figure()
    if show_crisis: add_crisis(fig, dates)

    # ── 혈압 편차 % (좌축) ─────────────────────────────────
    # 기준선
    fig.add_hline(y=0, line_color="rgba(150,150,150,0.55)",
                  line_width=1.2, line_dash="dash",
                  annotation_text="혈압 이동평균 기준 (0%)",
                  annotation_font=dict(size=8, color="#888"),
                  annotation_position="left")
    for y_val, label, clr in [
        (+20, "과열 +20%", "rgba(226,75,74,0.35)"),
        (-20, "침체 -20%", "rgba(74,144,217,0.35)"),
    ]:
        fig.add_hline(y=y_val, line_color=clr,
                      line_width=0.8, line_dash="dot",
                      annotation_text=label,
                      annotation_font=dict(size=8, color="#aaa"),
                      annotation_position="left")

    # 과열/침체 배경
    fig.add_hrect(y0=20,  y1=80,  fillcolor="rgba(226,75,74,0.04)",  line_width=0)
    fig.add_hrect(y0=-80, y1=-20, fillcolor="rgba(74,144,217,0.04)", line_width=0)

    if "NQ" in A:
        dev_nq = calc_deviation(A["NQ"])
        fig.add_trace(go.Scatter(
            x=dates, y=dev_nq.values.tolist(),
            name="나스닥 편차% (수축기 혈압)",
            mode="lines",
            line=dict(color="#E24B4A", width=2.0),
            yaxis="y",
            hovertemplate="<b>나스닥 편차</b>: %{y:+.1f}%<br>%{x}<extra></extra>",
        ))
    if "SP" in A:
        dev_sp = calc_deviation(A["SP"])
        fig.add_trace(go.Scatter(
            x=dates, y=dev_sp.values.tolist(),
            name="S&P 500 편차% (이완기 혈압)",
            mode="lines",
            line=dict(color="#F0A500", width=2.0, dash="dash"),
            yaxis="y",
            hovertemplate="<b>S&P 500 편차</b>: %{y:+.1f}%<br>%{x}<extra></extra>",
        ))

    # ── 나머지 지표 원값 (우측 오버레이) ──────────────────────
    OTHER = [
        ("TNX", "심박수 (미국채 10년물)", "#8E44AD", "dot",      "y2",
         SCALES["TNX_L"], SCALES["TNX_H"]),
        ("DXY", "체온 (달러 인덱스)",    "#4A90D9", "dashdot",  "y3",
         SCALES["DXY_L"], SCALES["DXY_H"]),
        ("VIX", "호흡수 (VIX)",          "#27AE60", "solid",    "y4",
         SCALES["VIX_L"], SCALES["VIX_H"]),
        ("WTI", "혈당 (WTI 유가)",       "#1A3A6B", "longdash", "y5",
         SCALES["WTI_L"], SCALES["WTI_H"]),
    ]
    for key, label, color, dash, yax, ymin, ymax in OTHER:
        if key not in A: continue
        fig.add_trace(go.Scatter(
            x=dates, y=A[key].values.tolist(),
            name=label,
            mode="lines",
            line=dict(color=color, width=1.5, dash=dash),
            yaxis=yax,
            hovertemplate=f"<b>{label}</b>: %{{y:,.2f}}<br>%{{x}}<extra></extra>",
        ))

    # 금/BTC 편차% (좌축에 혈압과 같은 축으로 오버레이)
    if "GLD" in A:
        dev_gld = calc_deviation(A["GLD"])
        fig.add_trace(go.Scatter(
            x=dates, y=dev_gld.values.tolist(),
            name="금 편차% (전통자산)",
            mode="lines",
            line=dict(color="#FFD700", width=1.8, dash="dot"),
            yaxis="y",
            hovertemplate="<b>금 편차</b>: %{y:+.1f}%<br>%{x}<extra></extra>",
        ))
    if "BTC" in A:
        dev_btc = calc_deviation(A["BTC"]) / 4   # 변동성 과대로 1/4 스케일 적용
        fig.add_trace(go.Scatter(
            x=dates, y=dev_btc.values.tolist(),
            name="비트코인 편차%÷4 (신흥자산)",
            mode="lines",
            line=dict(color="#FF69B4", width=1.8, dash="dashdot"),
            yaxis="y",
            hovertemplate="<b>비트코인 편차÷4</b>: %{y:+.1f}%<br>(실제: %{customdata:+.1f}%)<br>%{x}<extra></extra>",
            customdata=(calc_deviation(A["BTC"])).values.tolist(),
        ))

    fig.update_layout(
        title="⑤ 보정 차트 — 혈압: 200일 이동평균 편차% / 나머지: 원값",
        height=580, hovermode="x unified",
        plot_bgcolor="#fafafa", paper_bgcolor="white",
        margin=dict(l=55, r=10, t=50, b=90),
        legend=dict(orientation="h", x=0, y=-0.16,
                    font=dict(size=10, color="#111"),
                    bgcolor="rgba(255,255,255,0.85)"),
        # 좌축: 혈압 편차 %
        yaxis=dict(
            title="혈압 편차 (%)",
            title_font=dict(color="#D35400", size=10),
            tickfont=dict(color="#D35400", size=9),
            ticksuffix="%",
            range=[-60, 80],
            zeroline=True, zerolinecolor="rgba(150,150,150,0.4)",
            gridcolor="rgba(180,180,180,0.12)",
        ),
        # 우측 원값 축들 (tick 숨김 — 범례로 구분)
        yaxis2=dict(title=None, showticklabels=False, showline=False, showgrid=False,
                    range=[SCALES["TNX_L"], SCALES["TNX_H"]],
                    overlaying="y", side="right"),
        yaxis3=dict(title=None, showticklabels=False, showline=False, showgrid=False,
                    range=[SCALES["DXY_L"], SCALES["DXY_H"]],
                    overlaying="y", side="right"),
        yaxis4=dict(title=None, showticklabels=False, showline=False, showgrid=False,
                    range=[SCALES["VIX_L"], SCALES["VIX_H"]],
                    overlaying="y", side="right"),
        yaxis5=dict(title=None, showticklabels=False, showline=False, showgrid=False,
                    range=[SCALES["WTI_L"], SCALES["WTI_H"]],
                    overlaying="y", side="right"),
        xaxis=dict(tickfont=dict(size=9, color="#111"),
                   gridcolor="rgba(180,180,180,0.18)",
                   range=[dates[0], dates[-1]]),
    )
    return fig

def make_combined_fig():
    fig = go.Figure()
    if show_crisis: add_crisis(fig, dates)
    # BP
    if "NQ" in A and "SP" in A:
        nq_v = A["NQ"].values.tolist()
        sp_v = A["SP"].values.tolist()
        bx, by = [], []
        for i in range(0, len(dates), STEP):
            bx += [dates[i], dates[i], None]
            by += [sp_v[i], nq_v[i], None]
        fig.add_trace(go.Scatter(x=bx, y=by, mode="lines",
            line=dict(color="rgba(226,75,74,0.13)", width=0.8),
            showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=dates, y=nq_v,
            name="나스닥 (수축기 혈압)", mode="lines",
            line=dict(color="#D35400", width=1.8), yaxis="y",
            hovertemplate="<b>나스닥</b>: %{y:,.0f}<br>%{x}<extra></extra>"))
        fig.add_trace(go.Scatter(x=dates, y=sp_v,
            name="S&P 500 (이완기 혈압)", mode="lines",
            line=dict(color="#F0A500", width=1.8), yaxis="y",
            hovertemplate="<b>S&P 500</b>: %{y:,.0f}<br>%{x}<extra></extra>"))
    # Vitals
    for key, yax, color, dash, sym in [
        ("TNX","y2","#8E44AD","dot","x"),
        ("DXY","y3","#4A90D9","dashdot","cross"),
        ("VIX","y4","#27AE60","solid","diamond"),
        ("WTI","y5","#1A3A6B","longdash","star"),
        ("GLD","y6","#FFD700","solid","hexagon"),
        ("BTC","y7","#FF69B4","dash","circle"),
    ]:
        if key not in A: continue
        _, fin, bio, unit, _ = TICKERS[key]
        fig.add_trace(go.Scatter(x=dates, y=A[key].values.tolist(),
            name=f"{bio} ({fin})", mode="lines",
            line=dict(color=color, width=1.6, dash=dash),
            yaxis=yax,
            hovertemplate=f"<b>{bio}</b>: %{{y:,.2f}} {unit}<br>%{{x}}<extra></extra>"))
    fig.update_layout(
        title="④ 통합 차트",
        height=780, hovermode="x unified",
        plot_bgcolor="#fafafa", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=45, b=60),
        legend=dict(
            orientation="h", x=0, y=-0.08,
            font=dict(size=10, color="#111"),
            traceorder="normal",
            bgcolor="rgba(255,255,255,0.85)",
            itemwidth=60,
        ),
        yaxis=dict(title=None,
            showticklabels=False, showline=False, showgrid=True,
            gridcolor="rgba(226,75,74,0.08)",
            range=[SCALES["BP_L"], SCALES["BP_H"]], zeroline=False),
        yaxis2=dict(title=None,
            showticklabels=False, showline=False, showgrid=False,
            range=[SCALES["TNX_L"], SCALES["TNX_H"]],
            overlaying="y", side="right"),
        yaxis3=dict(title=None,
            showticklabels=False, showline=False, showgrid=False,
            range=[SCALES["DXY_L"], SCALES["DXY_H"]],
            overlaying="y", side="right"),
        yaxis4=dict(title=None,
            showticklabels=False, showline=False, showgrid=False,
            range=[SCALES["VIX_L"], SCALES["VIX_H"]],
            overlaying="y", side="right"),
        yaxis5=dict(title=None,
            showticklabels=False, showline=False, showgrid=False,
            range=[SCALES["WTI_L"], SCALES["WTI_H"]],
            overlaying="y", side="right"),
        yaxis6=dict(title=None,
            showticklabels=False, showline=False, showgrid=False,
            range=[SCALES["GLD_L"], SCALES["GLD_H"]],
            overlaying="y", side="right"),
        yaxis7=dict(title=None,
            showticklabels=False, showline=False, showgrid=False,
            range=[SCALES["BTC_L"], SCALES["BTC_H"]],
            overlaying="y", side="right"),
        xaxis=dict(tickfont=dict(size=9, color="#111"),
            gridcolor="rgba(180,180,180,0.18)",
            range=[dates[0], dates[-1]]),
    )
    return fig


# ══════════════════════════════════════════════════════
# 차트 렌더링 (차트 + 우측 축 범례 나란히)
# ══════════════════════════════════════════════════════
st.divider()

def render_legend(items, chart_height=460):
    n = len(items)
    item_h = max(40, (chart_height - 40) // max(n, 1))
    parts = []
    for label, color, desc, rng in items:
        parts.append(
            "<div style='display:flex;flex-direction:column;justify-content:center;"
            "height:" + str(item_h) + "px;padding:2px 0;"
            "border-bottom:0.5px solid rgba(255,255,255,0.2);'>"
            "<span style='color:" + color + ";font-size:13px;font-weight:700;white-space:nowrap;'>"
            "&#9679; " + label + "</span>"
            "<span style='color:#ffffff;font-size:11px;font-weight:500;margin-top:1px;white-space:nowrap;'>"
            + desc + "</span>"
            "<span style='color:#cccccc;font-size:10px;white-space:nowrap;'>"
            + rng + "</span>"
            "</div>"
        )
    html = (
        "<div style='display:flex;flex-direction:column;height:"
        + str(chart_height) + "px;overflow:hidden;padding-top:8px;'>"
        + "".join(parts)
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# 신호 모니터링 대시보드
# ══════════════════════════════════════════════════════
st.divider()
st.markdown("### 🚨 신호 모니터링 대시보드")

# 신호용 데이터 — 토글 상태와 무관하게 항상 로드
with st.spinner("신호 데이터 로딩 중..."):
    _signal_sector = load_sector_data(period)
    _signal_bond   = load_bond_data(period)

def calc_dev_single(s, w=200):
    ma = s.rolling(w, min_periods=50).mean()
    return ((s - ma) / ma * 100)

# 신호 계산
signals = []

# 1. VIX
if "VIX" in A:
    vix_now = float(A["VIX"].iloc[-1])
    vix_signal = "🔴 경고" if vix_now >= 25 else "🟡 주의" if vix_now >= 20 else "🟢 정상"
    vix_hit = vix_now >= 20
    signals.append(("VIX", f"{vix_now:.1f}", "≥20 주의 / ≥25 경고", vix_signal, vix_hit))

# 2. 나스닥 편차 꺾임
if "NQ" in A:
    nq_dev = calc_dev_single(A["NQ"])
    nq_now = float(nq_dev.iloc[-1])
    nq_peak20 = float(nq_dev.iloc[-20:].max())
    nq_drop = nq_peak20 - nq_now
    nq_signal = "🔴 경고" if nq_drop >= 5 else "🟡 주의" if nq_drop >= 2 else "🟢 정상"
    nq_hit = nq_drop >= 5
    signals.append(("나스닥 편차 꺾임", f"{nq_now:+.1f}% (20일고점 대비 -{nq_drop:.1f}%p)",
                    "20일 고점 대비 -5%p 이탈", nq_signal, nq_hit))

# 3. 금 편차
if "GLD" in A:
    gld_dev = calc_dev_single(A["GLD"])
    gld_now = float(gld_dev.iloc[-1])
    gld_signal = "🔴 경고" if gld_now >= 15 else "🟡 주의" if gld_now >= 10 else "🟢 정상"
    gld_hit = gld_now >= 10
    signals.append(("금 편차%", f"{gld_now:+.1f}%", "≥+10% 기관 헷지 신호", gld_signal, gld_hit))

# 4. HYG 편차 (채권 데이터 있으면)
try:
    if "HYG" in _signal_bond:
        hyg_dev = float(_signal_bond["HYG"]["cur_dev"])
        hyg_signal = "🔴 경고" if hyg_dev <= -10 else "🟡 주의" if hyg_dev <= -5 else "🟢 정상"
        hyg_hit = hyg_dev <= -5
        signals.append(("HYG 신용 스프레드", f"{hyg_dev:+.1f}%",
                        "≤-5% 주의 / ≤-10% 경고", hyg_signal, hyg_hit))
except:
    pass

# 5. WTI 현물 재반등
if "WTI" in A:
    wti_now = float(A["WTI"].iloc[-1])
    wti_dev = float(calc_dev_single(A["WTI"]).iloc[-1])
    wti_signal = "🔴 경고" if wti_dev >= 30 else "🟡 주의" if wti_dev >= 15 else "🟢 정상"
    wti_hit = wti_dev >= 15
    signals.append(("WTI 유가 편차%", f"{wti_dev:+.1f}% (${wti_now:.1f})",
                    "≥+15% 주의 / ≥+30% 경고", wti_signal, wti_hit))

# 6. XLP 방어 로테이션 (섹터 데이터 있으면)
try:
    if "XLP" in _signal_sector:
        xlp_dev = _signal_sector["XLP"]["dev"]
        xlp_now = float(xlp_dev.iloc[-1])
        xlp_mom = float(xlp_dev.diff(20).iloc[-1])
        xlp_hit = xlp_now > 5 and xlp_mom > 2
        xlp_signal = "🟡 주의" if xlp_hit else "🟢 정상"
        signals.append(("XLP 방어 로테이션", f"편차 {xlp_now:+.1f}% 모멘텀 {xlp_mom:+.1f}%p",
                        "편차>5%+모멘텀 양전환", xlp_signal, xlp_hit))
except:
    pass

# 7. SOXX vs QQQ 괴리
try:
    if "SOXX" in _signal_sector and "QQQ" in _signal_sector:
        soxx_now = float(_signal_sector["SOXX"]["dev"].iloc[-1])
        qqq_now  = float(_signal_sector["QQQ"]["dev"].iloc[-1])
        gap = soxx_now - qqq_now
        gap_signal = "🟡 주의" if gap > 30 else "🟢 정상"
        gap_hit = gap > 30
        signals.append(("SOXX-QQQ 이격 괴리", f"SOXX{soxx_now:+.0f}% QQQ{qqq_now:+.0f}% (괴리{gap:+.0f}%p)",
                        "괴리 >30%p 극단적 집중", gap_signal, gap_hit))
except:
    pass

# 8. IWM-QQQ breadth
try:
    if "IWM" in _signal_sector and "QQQ" in _signal_sector:
        iwm_now = float(_signal_sector["IWM"]["dev"].iloc[-1])
        qqq_now = float(_signal_sector["QQQ"]["dev"].iloc[-1])
        breadth_gap = qqq_now - iwm_now
        breadth_signal = "🟡 주의" if breadth_gap > 15 else "🟢 정상"
        breadth_hit = breadth_gap > 15
        signals.append(("Market Breadth (QQQ-IWM)", f"괴리 {breadth_gap:+.1f}%p",
                        ">15%p Breadth 악화", breadth_signal, breadth_hit))
except:
    pass

# 신호 카운트
hit_count = sum(1 for s in signals if s[4])
total = len(signals)

# 전체 상태 배너
if hit_count == 0:
    st.success(f"✅ 신호 없음 — {total}개 지표 모두 정상")
elif hit_count <= 2:
    st.warning(f"⚠️ {hit_count}/{total}개 신호 감지 — 모니터링 강화")
else:
    st.error(f"🚨 {hit_count}/{total}개 신호 동시 감지 — 주요 타이밍 구간")

# 신호 카드
st.markdown("<br>", unsafe_allow_html=True)
cols = st.columns(min(len(signals), 4))
for i, (name, value, threshold, signal, hit) in enumerate(signals):
    with cols[i % 4]:
        bg = "#fff0f0" if "경고" in signal else "#fffbe6" if "주의" in signal else "#f0fff4"
        border = "#E24B4A" if "경고" in signal else "#F1C40F" if "주의" in signal else "#27AE60"
        st.markdown(
            f"<div style='background:{bg};border:1.5px solid {border};"
            f"border-radius:8px;padding:8px 10px;margin-bottom:6px'>"
            f"<div style='font-size:10px;color:#555;font-weight:600'>{name}</div>"
            f"<div style='font-size:12px;color:#111;font-weight:700;margin:3px 0'>{value}</div>"
            f"<div style='font-size:9px;color:#888'>{threshold}</div>"
            f"<div style='font-size:11px;margin-top:4px'>{signal}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


# ① 혈압
c1, c2 = st.columns([6, 1])
with c1:
    st.plotly_chart(make_bp_fig(), use_container_width=True)
with c2:
    st.markdown("##### ① 혈압")
    render_legend([
        ("나스닥 100", "#E24B4A", "수축기 혈압 (pt)", "100 ~ 35,000"),
        ("S&P 500",   "#F0A500", "이완기 혈압 (pt)", "100 ~ 35,000"),
    ], chart_height=420)

# ② 바이탈
c1, c2 = st.columns([6, 1])
with c1:
    st.plotly_chart(make_vital_fig(), use_container_width=True)
with c2:
    st.markdown("##### ② 바이탈")
    render_legend([
        ("심박수", "#8E44AD", "미국채 10년물 (%)",     "0 ~ 10"),
        ("체온",   "#4A90D9", "달러 인덱스",           "50 ~ 200"),
        ("호흡수", "#27AE60", "VIX 변동성",            "5 ~ 100"),
        ("혈당",   "#1A3A6B", "WTI 유가 선물 ($/bbl)", "0 ~ 200"),
    ], chart_height=520)

# ③ 자산 (금 + BTC)
c1, c2 = st.columns([6, 1])
with c1:
    st.plotly_chart(make_asset_fig(), use_container_width=True)
with c2:
    st.markdown("##### ③ 자산")
    render_legend([
        ("전통자산 (금)",  "#FFD700", "금 선물 ($/oz)", "200 ~ 6,000"),
        ("신흥자산 (BTC)", "#FF69B4", "비트코인 ($)",   "0 ~ 140,000"),
    ], chart_height=460)

# ④ 통합
if show_fig3:
    c1, c2 = st.columns([6, 1])
    with c1:
        st.plotly_chart(make_combined_fig(), use_container_width=True)
    with c2:
        st.markdown("##### ④ 통합")
        render_legend([
            ("혈압(나스닥)", "#E24B4A", "수축기 혈압 (pt)",      "100 ~ 35,000"),
            ("혈압(S&P)",   "#F0A500", "이완기 혈압 (pt)",      "100 ~ 35,000"),
            ("심박수",       "#8E44AD", "미국채 10년물 (%)",     "0 ~ 10"),
            ("체온",         "#4A90D9", "달러 인덱스",           "50 ~ 200"),
            ("호흡수",       "#27AE60", "VIX 변동성",            "5 ~ 100"),
            ("혈당",         "#1A3A6B", "WTI 유가 선물 ($/bbl)", "0 ~ 200"),
            ("전통자산",     "#FFD700", "금 선물 ($/oz)",         "200 ~ 6,000"),
            ("신흥자산",     "#FF69B4", "비트코인 ($)",           "0 ~ 140,000"),
        ], chart_height=780)

# ⑤ 보정 차트 (이동평균 대비 편차)
if show_fig5:
    st.divider()
    c1, c2 = st.columns([6, 1])
    with c1:
        st.plotly_chart(make_deviation_fig(), use_container_width=True)
    with c2:
        st.markdown("##### ⑤ 보정")
        render_legend([
            ("나스닥 편차%", "#E24B4A", "수축기 혈압", "+/-% (0=MA)"),
            ("S&P 편차%",   "#F0A500", "이완기 혈압", "+/-% (0=MA)"),
            ("심박수",       "#8E44AD", "미국채 10년물", "0~10"),
            ("체온",         "#4A90D9", "달러 인덱스", "50~200"),
            ("호흡수",       "#27AE60", "VIX 변동성", "5~100"),
            ("혈당",         "#1A3A6B", "WTI 유가 선물", "0~200"),
            ("금 편차%",     "#FFD700", "전통자산 (금 선물)", "+/-% (0=MA)"),
            ("BTC 편차%÷4", "#FF69B4", "신흥자산 (비트코인)", "+/-% ÷4 보정"),
        ], chart_height=580)


# ⑥ WTI 현물/선물/괴리
if show_fig6:
    st.divider()
    with st.spinner("WTI 데이터 로딩 중..."):
        wti_spot_df, wti_fut_df = load_wti_data(eia_key) if eia_key else (None, None)
        # EIA 키 없어도 선물은 yfinance로
        if wti_fut_df is None:
            try:
                raw = yf.download("CL=F", period="max", interval="1d",
                                  progress=False, auto_adjust=True)
                if not raw.empty:
                    if isinstance(raw.columns, pd.MultiIndex):
                        s = raw[("Close","CL=F")].dropna()
                    else:
                        s = raw["Close"].dropna()
                    wti_fut_df = s.astype(float).to_frame("Futures")
                    wti_fut_df.index = pd.to_datetime(wti_fut_df.index).tz_localize(None)
            except:
                pass
    c1, c2 = st.columns([6, 1])
    with c1:
        st.plotly_chart(make_wti_fig(wti_spot_df, wti_fut_df, dates),
                       use_container_width=True, key="wti_chart")
    with c2:
        st.markdown("##### ⑥ WTI")
        render_legend([
            ("선물 (CL=F)", "#1A3A6B", "WTI 선물", "$/bbl"),
            ("현물 (EIA)",  "#E67E22", "WTI 현물 (주간)", "$/bbl"),
            ("괴리",        "#8E44AD", "현물 - 선물",   "$ 차이"),
        ], chart_height=480)

# ⑦ 섹터별 편차
if show_fig7:
    st.divider()
    with st.spinner("섹터 데이터 로딩 중..."):
        sector_data = load_sector_data(period)
    if sector_data:
        c1, c2 = st.columns([6, 1])
        with c1:
            st.plotly_chart(make_sector_fig(sector_data, period_label),
                           use_container_width=True)
        with c2:
            st.markdown("##### ⑦ 섹터")
            st.markdown(
                "<small style='color:#aaa;font-size:9px;line-height:1.6'>"
                "QQQ 나스닥100<br>SPY S&P500<br>DIA 다우존스<br>"
                "IWM 러셀2000<br>SOXX 반도체<br>XLK 기술<br>"
                "XLC 통신<br>XLY 임의소비재<br>XLF 금융<br>"
                "XLV 헬스케어<br>XLE 에너지<br>XLI 산업재<br>"
                "XLB 소재<br>XLU 유틸리티<br>XLRE 부동산<br>"
                "XLP 필수소비재"
                "</small>",
                unsafe_allow_html=True,
            )
    else:
        st.warning("섹터 데이터를 불러오지 못했습니다.")

# ⑧ 채권 ETF
if show_fig8:
    st.divider()
    with st.spinner("채권 ETF 데이터 로딩 중..."):
        bond_data = load_bond_data(period)
    if bond_data:
        # 현재 상태 카드
        bcols = st.columns(len(bond_data))
        for i, (ticker, info) in enumerate(bond_data.items()):
            with bcols[i]:
                cur_p = info["cur_price"]
                cur_d = info["cur_dev"]
                color = "#E24B4A" if cur_d < -10 else "#E67E22" if cur_d < -5 else                         "#27AE60" if cur_d > 5 else "#555"
                st.markdown(
                    f"<div style='background:#f8f8f8;border-radius:8px;padding:6px;"
                    f"text-align:center;border:0.5px solid #ddd'>"
                    f"<div style='font-size:10px;color:#555'>{ticker}</div>"
                    f"<div style='font-size:9px;color:#888'>{info['label']}</div>"
                    f"<div style='font-size:13px;font-weight:700;color:#111'>${cur_p:.2f}</div>"
                    f"<div style='font-size:10px;color:{color}'>{cur_d:+.1f}%</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        st.markdown("<br>", unsafe_allow_html=True)

        fig_p, fig_d = make_bond_fig(bond_data, period_label)
        c1, c2 = st.columns([6, 1])
        with c1:
            st.plotly_chart(fig_p, use_container_width=True, key="bond_price")
            st.plotly_chart(fig_d, use_container_width=True, key="bond_dev")
        with c2:
            st.markdown("##### ⑧ 채권")
            render_legend([
                ("SHY", "#4A90D9", "단기채 1-3년",    "가격"),
                ("IEF", "#27AE60", "중기채 7-10년",   "가격"),
                ("TLT", "#8E44AD", "장기채 20년+",    "가격"),
                ("HYG", "#E24B4A", "하이일드 회사채", "가격"),
                ("JNK", "#F1C40F", "정크본드",         "가격"),
                ("LQD", "#E67E22", "투자등급 회사채", "가격"),
            ], chart_height=900)
    else:
        st.warning("채권 ETF 데이터를 불러오지 못했습니다.")

# ══════════════════════════════════════════════════════
# 데이터 다운로드# ══════════════════════════════════════════════════════
# 데이터 다운로드# ══════════════════════════════════════════════════════
# 데이터 다운로드
# ══════════════════════════════════════════════════════
st.divider()
st.markdown("### 💾 데이터 다운로드")

# ── 모든 데이터 통합 ─────────────────────────────────────────
# 1) 바이탈 8개 지표
combined = pd.DataFrame({k: A[k] for k in A})
combined.index.name = "Date"

# 2) 섹터 ETF 편차% (⑦)
try:
    if "sector_data" in dir() and sector_data:
        for ticker, info in sector_data.items():
            col_name = f"섹터_{ticker}_{info['label']}_편차%"
            combined[col_name] = info["dev"].reindex(combined.index)
except:
    pass

# 3) 채권 ETF 가격 + 편차% (⑧)
try:
    if "bond_data" in dir() and bond_data:
        for ticker, info in bond_data.items():
            combined[f"채권_{ticker}_{info['label']}_가격"] = (
                info["price"].reindex(combined.index)
            )
            combined[f"채권_{ticker}_{info['label']}_편차%"] = (
                info["dev"].reindex(combined.index)
            )
except:
    pass

# 4) WTI 현물/선물/괴리 (⑥)
try:
    if "wti_spot_df" in dir() and wti_spot_df is not None:
        combined["WTI_현물_EIA"] = wti_spot_df["Spot"].reindex(combined.index)
    if "wti_fut_df" in dir() and wti_fut_df is not None:
        combined["WTI_선물_CLF"] = wti_fut_df["Futures"].reindex(combined.index)
    if "wti_spot_df" in dir() and wti_spot_df is not None and        "wti_fut_df" in dir() and wti_fut_df is not None:
        combined["WTI_괴리(현물-선물)"] = (
            wti_spot_df["Spot"].reindex(combined.index) -
            wti_fut_df["Futures"].reindex(combined.index)
        )
except:
    pass

combined.sort_index(ascending=False, inplace=True)

col1, col2 = st.columns(2)

with col1:
    csv_bytes = combined.to_csv().encode("utf-8-sig")
    st.download_button(
        label="📄 전체 CSV (바이탈+섹터+채권+WTI)",
        data=csv_bytes,
        file_name=f"market_vitals_full_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col2:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # 시트1: 전체 통합 (모든 컬럼)
        combined.to_excel(writer, sheet_name="전체_통합")
        # 시트2: 바이탈 지표별
        for key, (sym, fin, bio, unit, color) in TICKERS.items():
            if key not in A: continue
            df_out = A[key].to_frame("Close")
            df_out["전일대비"]  = df_out["Close"].diff()
            df_out["변화율(%)"] = df_out["Close"].pct_change() * 100
            df_out["52주최고"]  = df_out["Close"].rolling(252).max()
            df_out["52주최저"]  = df_out["Close"].rolling(252).min()
            df_out.to_excel(writer, sheet_name=f"{bio}_{fin}"[:31])
        # 시트3: 섹터 편차%
        try:
            if "sector_data" in dir() and sector_data:
                sec_df = pd.DataFrame({
                    f"{t}_{info['label']}": info["dev"]
                    for t, info in sector_data.items()
                })
                sec_df.index.name = "Date"
                sec_df.sort_index(ascending=False).to_excel(writer, sheet_name="섹터_편차%")
        except:
            pass
        # 시트4: 채권 ETF
        try:
            if "bond_data" in dir() and bond_data:
                bond_price_df = pd.DataFrame({
                    f"{t}_{info['label']}_가격": info["price"]
                    for t, info in bond_data.items()
                })
                bond_dev_df = pd.DataFrame({
                    f"{t}_{info['label']}_편차%": info["dev"]
                    for t, info in bond_data.items()
                })
                bond_price_df.index.name = "Date"
                bond_dev_df.index.name   = "Date"
                bond_price_df.sort_index(ascending=False).to_excel(writer, sheet_name="채권_가격")
                bond_dev_df.sort_index(ascending=False).to_excel(writer,  sheet_name="채권_편차%")
        except:
            pass
        # 시트5: WTI 현물/선물/괴리
        try:
            wti_rows = {}
            if "wti_spot_df" in dir() and wti_spot_df is not None:
                wti_rows["WTI_현물_EIA"] = wti_spot_df["Spot"]
            if "wti_fut_df" in dir() and wti_fut_df is not None:
                wti_rows["WTI_선물_CLF"] = wti_fut_df["Futures"]
            if "WTI_현물_EIA" in wti_rows and "WTI_선물_CLF" in wti_rows:
                wti_rows["괴리(현물-선물)"] = (
                    wti_rows["WTI_현물_EIA"] - wti_rows["WTI_선물_CLF"]
                )
            if wti_rows:
                wti_out = pd.DataFrame(wti_rows)
                wti_out.index.name = "Date"
                wti_out.sort_index(ascending=False).to_excel(
                    writer, sheet_name="WTI_현물선물괴리")
        except:
            pass
    buf.seek(0)
    st.download_button(
        label="📊 전체 Excel (시트 구분)",
        data=buf,
        file_name=f"market_vitals_full_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

# ══════════════════════════════════════════════════════
# 원본 데이터 테이블
# ══════════════════════════════════════════════════════
with st.expander("📋 원본 데이터 테이블 보기"):
    display_df = combined.copy()
    display_df.index = display_df.index.strftime("%Y-%m-%d")
    st.dataframe(
        display_df.sort_index(ascending=False).head(100),
        use_container_width=True,
        height=300,
    )
    st.markdown(f"<span style='color:#111;font-size:12px'>최근 100행 표시 (전체 {len(combined):,}행)</span>", unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"<span style='color:#111;font-size:12px'>지옥변곡점이 시장을 보는 시선 | 데이터: Yahoo Finance | 마지막 갱신: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>", unsafe_allow_html=True)
