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
    "NQ":  ("^NDX",     "나스닥 100",       "수축기 혈압", "pt",    "#D35400"),
    "SP":  ("^GSPC",    "S&P 500",         "이완기 혈압", "pt",    "#F0A500"),
    "TNX": ("^TNX",     "미국채 10년물",    "심박수",      "%",     "#8E44AD"),
    "DXY": ("DX-Y.NYB", "달러 인덱스",      "체온",        "DXY",   "#4A90D9"),
    "VIX": ("^VIX",     "VIX 변동성",       "호흡수",      "",      "#27AE60"),
    "WTI": ("CL=F",     "WTI 유가 선물",     "혈당",        "$/bbl", "#C0392B"),
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

    st.divider()

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
            line=dict(color="rgba(211,84,0,0.15)", width=0.9),
            showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=dates, y=nq_v, fill=None, mode="none",
            showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=dates, y=sp_v, fill="tonexty",
            fillcolor="rgba(211,84,0,0.08)", mode="none",
            showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=dates, y=nq_v,
            name="나스닥 100 (수축기 혈압)", mode="lines+markers",
            line=dict(color="#D35400", width=2.0),
            marker=dict(symbol="triangle-up", size=3, color="#D35400", maxdisplayed=400),
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
            gridcolor="rgba(211,84,0,0.10)",
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
            line=dict(color="#C0392B", width=2.0, dash="longdash"),
            marker=dict(symbol="star", size=3, color="#C0392B", maxdisplayed=400),
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
            line=dict(color="#D35400", width=2.0),
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
        ("WTI", "혈당 (WTI 유가)",       "#C0392B", "longdash", "y5",
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
            line=dict(color="rgba(211,84,0,0.13)", width=0.8),
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
        ("WTI","y5","#C0392B","longdash","star"),
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
            gridcolor="rgba(211,84,0,0.08)",
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
        ("나스닥 100", "#D35400", "수축기 혈압 (pt)", "100 ~ 35,000"),
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
        ("혈당",   "#C0392B", "WTI 유가 선물 ($/bbl)", "0 ~ 200"),
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
            ("혈압(나스닥)", "#D35400", "수축기 혈압 (pt)",      "100 ~ 35,000"),
            ("혈압(S&P)",   "#F0A500", "이완기 혈압 (pt)",      "100 ~ 35,000"),
            ("심박수",       "#8E44AD", "미국채 10년물 (%)",     "0 ~ 10"),
            ("체온",         "#4A90D9", "달러 인덱스",           "50 ~ 200"),
            ("호흡수",       "#27AE60", "VIX 변동성",            "5 ~ 100"),
            ("혈당",         "#C0392B", "WTI 유가 선물 ($/bbl)", "0 ~ 200"),
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
            ("나스닥 편차%", "#D35400", "수축기 혈압", "+/-% (0=MA)"),
            ("S&P 편차%",   "#F0A500", "이완기 혈압", "+/-% (0=MA)"),
            ("심박수",       "#8E44AD", "미국채 10년물", "0~10"),
            ("체온",         "#4A90D9", "달러 인덱스", "50~200"),
            ("호흡수",       "#27AE60", "VIX 변동성", "5~100"),
            ("혈당",         "#C0392B", "WTI 유가 선물", "0~200"),
            ("금 편차%",     "#FFD700", "전통자산 (금 선물)", "+/-% (0=MA)"),
            ("BTC 편차%÷4", "#FF69B4", "신흥자산 (비트코인)", "+/-% ÷4 보정"),
        ], chart_height=580)


# ══════════════════════════════════════════════════════
# 가설 검증 분석
# ══════════════════════════════════════════════════════
st.divider()
st.markdown("### 🔬 데이터 기반 가설 검증")
st.markdown(
    "<span style='color:#555;font-size:12px'>"
    "앱에 로드된 실제 데이터로 가설을 자동 검증합니다."
    "</span>",
    unsafe_allow_html=True,
)

@st.cache_data(ttl=3600)
def run_analysis(period_key: str):
    """로드된 데이터로 가설 검증 — period 변경 시 재계산"""
    import numpy as np

    def calc_dev(s, w=200):
        ma = s.rolling(w, min_periods=50).mean()
        return ((s - ma) / ma * 100)

    results = {}

    # ── 현재 편차 상태 ────────────────────────────────────────
    current = {}
    LABELS = {
        "NQ":"나스닥","SP":"S&P 500","TNX":"미국채금리","DXY":"달러인덱스",
        "VIX":"VIX","WTI":"WTI유가","GLD":"금","BTC":"비트코인(÷4)",
    }
    for k in ["NQ","SP","GLD","BTC","TNX","DXY","VIX","WTI"]:
        if k not in A: continue
        dev = calc_dev(A[k])
        btc_scale = 4 if k == "BTC" else 1
        current[k] = {
            "label": LABELS.get(k, k),
            "dev":   float(dev.iloc[-1]) / btc_scale,
            "dev_raw": float(dev.iloc[-1]),
            "val":   float(A[k].iloc[-1]),
        }
    results["current"] = current

    # ── 가설 1: 나스닥 과열/침체 → 이후 6개월 ────────────────
    nq_dev = calc_dev(A["NQ"]).dropna()
    nq_raw = A["NQ"].reindex(nq_dev.index)
    over20, under20 = [], []
    for i in range(len(nq_dev) - 126):
        d = float(nq_dev.iloc[i])
        fwd = (float(nq_raw.iloc[i+126]) / float(nq_raw.iloc[i]) - 1) * 100
        if d > 20:  over20.append(fwd)
        elif d < -20: under20.append(fwd)
    results["h1"] = {
        "over":  {"mean": float(np.mean(over20))  if over20  else 0,
                  "winrate": sum(r>0 for r in over20)/len(over20)*100  if over20  else 0,
                  "n": len(over20)},
        "under": {"mean": float(np.mean(under20)) if under20 else 0,
                  "winrate": sum(r>0 for r in under20)/len(under20)*100 if under20 else 0,
                  "n": len(under20)},
    }

    # ── 가설 2: VIX > 30 → 이후 3개월 나스닥 ────────────────
    vix_s = A["VIX"]
    nq_s  = A["NQ"]
    idx   = vix_s.index.intersection(nq_s.index)
    vix_s = vix_s.reindex(idx)
    nq_s  = nq_s.reindex(idx)
    fwd3  = []
    for i in range(len(idx) - 63):
        if float(vix_s.iloc[i]) > 30:
            fwd3.append((float(nq_s.iloc[i+63]) / float(nq_s.iloc[i]) - 1) * 100)
    results["h2"] = {
        "mean":    float(np.mean(fwd3)) if fwd3 else 0,
        "winrate": sum(r>0 for r in fwd3)/len(fwd3)*100 if fwd3 else 0,
        "n":       len(fwd3),
    }

    # ── 가설 3: 금리 구간별 나스닥 6개월 수익률 ──────────────
    tnx_s = A["TNX"].reindex(idx)
    buckets = [(0,2,"0~2%"),(2,3,"2~3%"),(3,4,"3~4%"),(4,5,"4~5%"),(5,99,"5%+")]
    h3 = []
    for lo, hi, label in buckets:
        fwds = []
        for i in range(len(idx) - 126):
            t = float(tnx_s.iloc[i])
            if lo <= t < hi:
                fwds.append((float(nq_s.iloc[i+126]) / float(nq_s.iloc[i]) - 1) * 100)
        if fwds:
            h3.append({"label": label,
                       "mean":    round(float(np.mean(fwds)), 1),
                       "winrate": round(sum(f>0 for f in fwds)/len(fwds)*100, 0),
                       "n":       len(fwds)})
    results["h3"] = h3

    # ── 가설 4: 달러 편차% vs 나스닥 상관 ────────────────────
    dxy_dev = calc_dev(A["DXY"]) if "DXY" in A else None
    nq_dev2 = calc_dev(A["NQ"])
    if dxy_dev is not None:
        common2 = dxy_dev.dropna().index.intersection(nq_dev2.dropna().index)
        r = float(dxy_dev.reindex(common2).corr(nq_dev2.reindex(common2)))
        results["h4_r"] = round(r, 3)
    else:
        results["h4_r"] = None

    # ── 가설 5: 금 편차 vs BTC 편차 시차 상관 ────────────────
    if "GLD" in A and "BTC" in A:
        gld_dev = calc_dev(A["GLD"])
        btc_dev = calc_dev(A["BTC"])
        # BTC 2015년 이후만
        idx_ab = gld_dev.dropna().index.intersection(btc_dev.dropna().index)
        idx_ab = idx_ab[idx_ab >= pd.Timestamp("2015-01-01")]
        lags, corrs = [], []
        for lag in [0, 30, 60, 90, -30, -60]:
            btc_shifted = btc_dev.reindex(idx_ab).shift(lag)
            gld_aligned = gld_dev.reindex(idx_ab)
            valid = btc_shifted.dropna().index.intersection(gld_aligned.dropna().index)
            if len(valid) > 100:
                r = float(btc_shifted.reindex(valid).corr(gld_aligned.reindex(valid)))
                lags.append(lag)
                corrs.append(round(r, 3))
        best_lag = lags[corrs.index(max(corrs, key=abs))] if corrs else 0
        best_r   = max(corrs, key=abs) if corrs else 0
        results["h5"] = {"best_lag": best_lag, "best_r": best_r, "lags": lags, "corrs": corrs}
    else:
        results["h5"] = None

    return results

# 분석 실행 (period 바뀌면 재계산)
with st.spinner("🔬 데이터 분석 중..."):
    RES = run_analysis(period_label)

# ── 현재 상태 카드 ────────────────────────────────────────────
st.markdown("#### 📊 현재 지표 편차 상태 (200일 이동평균 기준)")
cur = RES["current"]
c_cols = st.columns(len(cur))
for idx_c, (k, v) in enumerate(cur.items()):
    dev = v["dev"]
    color = "#E24B4A" if dev > 20 else "#4A90D9" if dev < -20 else             "#E8890C" if dev > 10 else "#6BB5E8" if dev < -10 else "#27AE60"
    status = "🔴 과열" if dev > 20 else "🔵 침체" if dev < -20 else              "🟡 주의" if dev > 10 else "🟦 약세" if dev < -10 else "🟢 정상"
    with c_cols[idx_c]:
        st.markdown(
            "<div style='background:#f8f8f8;border-radius:8px;padding:8px;text-align:center;"
            "border:0.5px solid #ddd'>"
            f"<div style='font-size:10px;color:#555'>{v['label']}</div>"
            f"<div style='font-size:16px;font-weight:700;color:{color}'>{dev:+.1f}%</div>"
            f"<div style='font-size:9px;color:#888'>{status}</div>"
            "</div>",
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── 가설 카드들 ────────────────────────────────────────────────
h1 = RES["h1"]
h2 = RES["h2"]
h3 = RES["h3"]
h4r = RES["h4_r"]
h5 = RES["h5"]

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("#### 가설 1 — 나스닥 과열/침체 → 6개월 후")
    ov = h1["over"]
    un = h1["under"]
    st.markdown(
        f"**편차 >+20% (과열)** 이후 6개월  "
        f"→ 평균 **{ov['mean']:+.1f}%** | 승률 **{ov['winrate']:.0f}%** | n={ov['n']}"  


        f"**편차 <-20% (침체)** 이후 6개월  "
        f"→ 평균 **{un['mean']:+.1f}%** | 승률 **{un['winrate']:.0f}%** | n={un['n']}"
    )
    verdict1 = "✅ 과열 후 수익률 낮고, 침체 후 반등 경향 확인"         if ov["mean"] < un["mean"] else "⚠ 패턴 불명확"
    st.caption(verdict1)

    st.markdown("#### 가설 2 — VIX > 30 → 3개월 후 나스닥")
    st.markdown(
        f"VIX 30 초과 시점 이후 3개월  "
        f"→ 평균 **{h2['mean']:+.1f}%** | 승률 **{h2['winrate']:.0f}%** | n={h2['n']}"
    )
    verdict2 = "✅ 공포 극점 = 매수 기회 확인" if h2["winrate"] > 60 else "⚠ 패턴 불명확"
    st.caption(verdict2)

with col_b:
    st.markdown("#### 가설 3 — 금리 구간별 나스닥 6개월 수익률")
    if h3:
        import pandas as pd
        df_h3 = pd.DataFrame(h3).rename(columns={
            "label":"금리 구간","mean":"평균수익률(%)","winrate":"승률(%)","n":"관측수"
        })
        st.dataframe(df_h3.set_index("금리 구간"), use_container_width=True, height=220)

    if h4r is not None:
        st.markdown("#### 가설 4 — 달러 강세 ↔ 나스닥")
        color_r = "#E24B4A" if h4r < -0.3 else "#27AE60" if h4r > 0.3 else "#888"
        st.markdown(
            f"달러편차% vs 나스닥편차% 상관계수: "
            f"<span style='color:{color_r};font-weight:700'>r = {h4r}</span>",
            unsafe_allow_html=True,
        )
        st.caption("✅ 역상관 확인 (달러 강세 = 나스닥 약세)" if h4r < -0.2 else "⚠ 상관 약함")

if h5:
    st.markdown("#### 가설 5 — 금 vs 비트코인 편차% 시차 상관")
    best_l, best_r = h5["best_lag"], h5["best_r"]
    direction = f"BTC가 금보다 {abs(best_l)}일 먼저 움직임" if best_l > 0         else f"금이 BTC보다 {abs(best_l)}일 먼저 움직임" if best_l < 0         else "동시 움직임"
    st.markdown(
        f"최대 상관: lag=**{best_l}일**, r=**{best_r:+.3f}**  \n"
        f"→ {direction}"
    )
    st.caption("✅ 선행 관계 확인" if abs(best_r) > 0.3 else "⚠ 상관 약함")

# ══════════════════════════════════════════════════════
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
