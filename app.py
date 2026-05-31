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
    "NQ":  ("^NDX",     "나스닥 100",       "수축기 혈압", "pt",    "#E24B4A"),
    "SP":  ("^GSPC",    "S&P 500",         "이완기 혈압", "pt",    "#F0A500"),
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
# EIA WTI 현물 데이터
# ══════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def load_eia_spot(api_key: str):
    """EIA API로 WTI 현물가 로드"""
    import requests
    url = (
        "https://api.eia.gov/v2/petroleum/pri/spt/data/"
        "?frequency=daily&data[0]=value"
        "&facets[series][]=RWTC"
        "&sort[0][column]=period&sort[0][direction]=desc"
        f"&offset=0&length=5000&api_key={api_key}"
    )
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        rows = data["response"]["data"]
        df = pd.DataFrame(rows)[["period","value"]].copy()
        df["Date"]  = pd.to_datetime(df["period"])
        df["Spot"]  = pd.to_numeric(df["value"], errors="coerce")
        df = df[["Date","Spot"]].dropna().set_index("Date").sort_index()
        return df
    except Exception as e:
        return None


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
            x=dates_s, y=dev.values.tolist(),
            name=f"{info['label']} ({ticker})  {cur:+.1f}%",
            mode="lines",
            line=dict(color=info["color"], width=1.8),
            hovertemplate=f"<b>{info['label']}</b>: %{{y:+.1f}}%<br>%{{x}}<extra></extra>",
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

def make_wti_fig(spot_df, futures_s, dates):
    """WTI 현물 / 선물 / 괴리 차트"""
    fig = go.Figure()

    # 선물 (yfinance, 기존 A["WTI"])
    fig.add_trace(go.Scatter(
        x=dates, y=futures_s.values.tolist(),
        name="WTI 선물 (CL=F)",
        mode="lines",
        line=dict(color="#1A3A6B", width=2.0),
        hovertemplate="<b>WTI 선물</b>: $%{y:.2f}<br>%{x}<extra></extra>",
    ))

    if spot_df is not None:
        # 현물과 선물 공통 인덱스
        spot_reindexed = spot_df["Spot"].reindex(
            pd.to_datetime(dates)
        ).ffill()

        fig.add_trace(go.Scatter(
            x=dates, y=spot_reindexed.values.tolist(),
            name="WTI 현물 (EIA Cushing)",
            mode="lines",
            line=dict(color="#E67E22", width=2.0),
            hovertemplate="<b>WTI 현물</b>: $%{y:.2f}<br>%{x}<extra></extra>",
        ))

        # 괴리 (현물 - 선물)
        spread = spot_reindexed - futures_s.reindex(pd.to_datetime(dates)).ffill()
        fig.add_trace(go.Scatter(
            x=dates, y=spread.values.tolist(),
            name="괴리 (현물 - 선물)",
            mode="lines",
            line=dict(color="#8E44AD", width=1.5, dash="dash"),
            yaxis="y2",
            hovertemplate="<b>괴리</b>: $%{y:.2f}<br>%{x}<extra></extra>",
        ))

        # 0 기준선
        fig.add_hline(y=0, line_color="rgba(150,150,150,0.4)",
                      line_width=1, line_dash="dot", yref="y2")

        # 현재 괴리 표시
        cur_spread = float(spread.dropna().iloc[-1]) if len(spread.dropna()) > 0 else 0
        cur_spot   = float(spot_reindexed.dropna().iloc[-1]) if len(spot_reindexed.dropna()) > 0 else 0
        cur_fut    = float(futures_s.iloc[-1])
        spread_note = (
            f"현물 ${cur_spot:.1f} / 선물 ${cur_fut:.1f} / "
            f"괴리 ${cur_spread:+.1f}"
        )
    else:
        spread_note = "EIA API 키 필요"

    fig.update_layout(
        title=f"⑥ WTI 유가 — 현물 vs 선물 vs 괴리  ({spread_note})",
        height=480, hovermode="x unified",
        plot_bgcolor="#fafafa", paper_bgcolor="white",
        margin=dict(l=55, r=80, t=50, b=60),
        legend=dict(orientation="h", x=0, y=-0.15,
                    font=dict(size=10, color="#111")),
        yaxis=dict(
            title="가격 ($/bbl)",
            title_font=dict(color="#C0392B", size=10),
            tickfont=dict(color="#111", size=9),
            gridcolor="rgba(180,180,180,0.15)",
            tickprefix="$",
        ),
        yaxis2=dict(
            title="괴리 ($)",
            title_font=dict(color="#8E44AD", size=10),
            tickfont=dict(color="#8E44AD", size=9),
            overlaying="y", side="right",
            showgrid=False,
            tickprefix="$",
            zeroline=True,
            zerolinecolor="rgba(142,68,173,0.3)",
        ),
        xaxis=dict(
            tickfont=dict(size=9, color="#111"),
            gridcolor="rgba(180,180,180,0.18)",
            range=[dates[0], dates[-1]],
        ),
    )
    return fig

@st.cache_data(ttl=3600, show_spinner=False)
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
            if use_start:
                df = yf.download(sym, start=f"{period}-01-01",
                                 interval="1d", progress=False, auto_adjust=True)
            else:
                df = yf.download(sym, period=period, interval="1d",
                                 progress=False, auto_adjust=True)
            if not df.empty:
                data[key] = extract_close(df)
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
    show_fig6   = st.toggle("⑥ WTI 현물/선물 표시", value=True)
    show_fig7   = st.toggle("⑦ 섹터별 이격 표시",    value=True)

    st.divider()

    st.divider()
    st.markdown("**🛢 EIA API 키**")
    try:
        eia_key = st.secrets["EIA_API_KEY"]
        st.caption("Secrets에서 로드됨")
    except:
        eia_key = st.text_input("EIA API Key", type="password",
                                placeholder="eia.gov에서 무료 발급")

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
    val  = float(A[key].iloc[-1])
    prev = float(A[key].iloc[-2]) if len(A[key]) > 1 else val
    pct  = (val - prev) / prev * 100 if prev else 0
    g    = grade(key, val)
    gc   = grade_color(key, val)
    delta_cls = "vital-delta-up" if pct >= 0 else "vital-delta-down"
    arrow = "▲" if pct >= 0 else "▼"
    unit_str = f" {unit}" if unit else ""
    with cols[col_i]:
        st.markdown(f"""
<div class="vital-card">
  <div class="vital-label">{bio}</div>
  <div class="vital-fin">{fin}</div>
  <div class="vital-value">{val:,.2f}{unit_str}</div>
  <div class="{delta_cls}">{arrow} {abs(pct):.2f}%</div>
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
    spot_df = load_eia_spot(eia_key) if eia_key else None
    if "WTI" in A:
        wti_futures = A["WTI"]
        c1, c2 = st.columns([6, 1])
        with c1:
            st.plotly_chart(make_wti_fig(spot_df, wti_futures, dates),
                           use_container_width=True)
        with c2:
            st.markdown("##### ⑥ WTI")
            render_legend([
                ("선물 (CL=F)", "#1A3A6B", "WTI 1개월 선물",    "$/bbl"),
                ("현물 (EIA)",  "#E67E22", "Cushing OK 현물",   "$/bbl"),
                ("괴리",        "#8E44AD", "현물 - 선물",        "$ 차이"),
            ], chart_height=480)
    else:
        st.warning("WTI 데이터 없음")

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

# ══════════════════════════════════════════════════════
# 데이터 다운로드# ══════════════════════════════════════════════════════
# 데이터 다운로드
# ══════════════════════════════════════════════════════
st.divider()
st.markdown("### 💾 데이터 다운로드")

combined = pd.DataFrame({
    k: A[k] for k in A
})
combined.index.name = "Date"

col1, col2 = st.columns(2)

with col1:
    csv_bytes = combined.to_csv().encode("utf-8-sig")
    st.download_button(
        label="📄 CSV 다운로드",
        data=csv_bytes,
        file_name=f"market_vitals_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col2:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        combined.to_excel(writer, sheet_name="전체_통합")
        for key, (sym, fin, bio, unit, color) in TICKERS.items():
            if key not in A: continue
            df_out = A[key].to_frame("Close")
            df_out["전일대비"] = df_out["Close"].diff()
            df_out["변화율(%)"] = df_out["Close"].pct_change() * 100
            df_out["52주최고"] = df_out["Close"].rolling(252).max()
            df_out["52주최저"] = df_out["Close"].rolling(252).min()
            df_out.to_excel(writer, sheet_name=f"{bio}_{fin}"[:31])
    buf.seek(0)
    st.download_button(
        label="📊 Excel 다운로드",
        data=buf,
        file_name=f"market_vitals_{datetime.now().strftime('%Y%m%d')}.xlsx",
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
