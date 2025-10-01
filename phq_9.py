# -*- coding: utf-8 -*-
import os
from datetime import datetime
from typing import Dict, List

import io
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
from PIL import Image, ImageDraw, ImageFont  # PNG 합성용
import platform, shutil  # ← ORCA 자동탐지용

# ──────────────────────────────────────────────────────────────────────────────
# 페이지 설정
st.set_page_config(page_title="PHQ-9 자기보고 검사", page_icon="📝", layout="centered")

# ──────────────────────────────────────────────────────────────────────────────
# ORCA 초기화 (필수: ORCA만 사용)
def _init_orca():
    """
    ORCA 실행파일을 환경변수 PLOTLY_ORCA 또는 PATH에서 찾고 plotly에 등록한다.
    리눅스/맥 헤드리스 환경은 xvfb 사용을 활성화한다.
    """
    orca_path = os.environ.get("PLOTLY_ORCA", "").strip() or shutil.which("orca")
    if orca_path:
        pio.orca.config.executable = orca_path
    # 리눅스/맥에서 헤드리스일 수 있으니 xvfb 사용
    if platform.system() != "Windows":
        try:
            pio.orca.config.use_xvfb = True
        except Exception:
            pass
    return orca_path

_ORCA_PATH = _init_orca()

# 색상 토큰 (라이트 테마)
INK     = "#0f172a"   # 본문 텍스트
SUBTLE  = "#475569"   # 보조 텍스트
CARD_BG = "#ffffff"   # 카드 배경
APP_BG  = "#f6f7fb"   # 전체 배경
BORDER  = "#e5e7eb"   # 경계선
BRAND   = "#2563eb"   # 브랜드/포커스
ACCENT  = "#e11d48"   # 경고/강조

# ── 전문 톤 팔레트(저채도 그레이·블루)
GAUGE_STEPS = {
    "min":  "#F5F7FA",  # 0–4
    "low":  "#EEF2F6",  # 5–9
    "mid":  "#E6ECF2",  # 10–14
    "high": "#DEE5EE",  # 15–19
    "vhi":  "#D6DEE9",  # 20–27
}

# 불릿 트랙(모든 카테고리 길이 동일) + 측정치 색
BULLET_TRACK = "#EEF2F6"
BULLET_MEASURE = "#1F3A8A"   # 진한 인디고(전문 톤)



# ──────────────────────────────────────────────────────────────────────────────
# 전역 스타일
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

/* 토큰 */
:root {{
  --ink:{INK}; --subtle:{SUBTLE}; --bg:{APP_BG}; --card:{CARD_BG};
  --border:{BORDER}; --brand:{BRAND}; --accent:{ACCENT};
}}

html, body, [data-testid="stAppViewContainer"] {{
  background: var(--bg);
  color: var(--ink);
  font-family: "Inter","Noto Sans KR",system-ui,-apple-system,Segoe UI,Roboto,Apple SD Gothic Neo,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
}}

.block-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px 18px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  margin: 10px 0 14px;
}}

.badge {{
  display:inline-block; background: rgba(37,99,235,0.10); color: var(--brand);
  border: 1px solid rgba(37,99,235,0.25); padding: 3px 10px; border-radius: 999px;
  font-size: 12px; font-weight: 700; letter-spacing:.2px;
}}

.chip {{
  display:inline-block; background: #f1f5f9; color:#0f172a; border:1px solid #e2e8f0;
  padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight:600;
}}

.small-muted {{ color: var(--subtle); font-size: 12.5px; }}
.section-title {{ font-size: 1.05rem; font-weight: 800; letter-spacing: -0.2px; }}

.k-list {{ margin: 6px 0 0 0; padding-left: 18px; color: var(--ink); }}
.k-list li {{ margin: 6px 0; }}

.metric-box {{ display:grid; grid-template-columns: repeat(3,1fr); gap:10px; }}
.metric {{
  border:1px solid var(--border); border-radius: 12px; padding: 14px 14px; background:#f8fafc;
}}
.metric .label {{ color: var(--subtle); font-weight:700; font-size: 12px; }}
.metric .value {{ color: var(--ink); font-weight: 800; font-size: 20px; margin-top: 6px; }}

.item-card {{
  background:#fff; border:1px solid var(--border); border-radius:12px; padding:14px; margin:10px 0 4px;
}}
.item-no {{
  background: #eef2ff; color:#3730a3; border:1px solid #c7d2fe;
  width:28px; height:28px; border-radius: 9px; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:13px;
}}
.item-domain {{ color: var(--subtle); font-size: 12px; margin-top: 2px; }}

.warn {{
  background:#fff7ed; border:1px solid #fed7aa; color:#9a3412; border-radius:12px; padding:12px 14px; margin-top:6px;
}}

.safety {{
  background:#fff1f4; border:1px solid #fecdd3; border-radius:12px; padding:14px;
}}

[data-testid="stToolbar"], #MainMenu, header, footer {{ display: none !important; }}

/* ───── 라디오(가로 칩 스타일) ───── */
.stRadio > div[role="radiogroup"] {{
  display: flex !important;
  gap: 8px !important;
  flex-wrap: wrap !important;
  align-items: center !important;
}}
.stRadio [role="radio"] {{
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 8px 12px !important;
  border-radius: 999px !important;
  background: #f1f5f9 !important;
  border: 1px solid #e2e8f0 !important;
  cursor: pointer !important;
  transition: transform .02s ease-out, background .2s ease;
}}
.stRadio [role="radio"]:hover {{ transform: translateY(-1px); }}
.stRadio [role="radio"] > div:first-child {{ display:none !important; }} /* 기본 점 아이콘 숨김 */

/* 텍스트 항상 선명하게 */
.stRadio [role="radio"] [data-testid="stMarkdownContainer"] *,
.stRadio [role="radio"] span, .stRadio [role="radio"] p {{
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; opacity:1 !important;
}}
/* 선택 상태: 브랜드 배경 + 흰 글자 */
.stRadio [role="radio"][aria-checked="true"] {{
  background: var(--brand) !important; border-color: var(--brand) !important;
}}
.stRadio [role="radio"][aria-checked="true"] * {{
  color:#ffffff !important; -webkit-text-fill-color:#ffffff !important;
}}

/* ───── 버튼 스타일 (Primary/Secondary) ───── */
.stButton > button[data-testid="baseButton-primary"],
.stButton > button[kind="primary"]{{
  background: var(--brand) !important;
  color: #fff !important;
  border: 1.5px solid var(--brand) !important;
  border-radius: 12px !important;
  font-weight: 800 !important;
  box-shadow: 0 1px 2px rgba(0,0,0,.04) !important;
}}
.stButton > button[data-testid="baseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover{{ filter: brightness(1.03) !important; }}

.stButton > button:not([data-testid="baseButton-primary"]) {{
  background: #fff !important;
  color: var(--brand) !important;
  border: 1.5px solid var(--brand) !important;
  border-radius: 12px !important;
  font-weight: 800 !important;
  box-shadow: 0 1px 2px rgba(0,0,0,.04) !important;
}}
.stButton > button:not([data-testid="baseButton-primary"]):hover {{
  background: rgba(37,99,235,0.08) !important;
}}
.stButton > button * {{ color: inherit !important; }}

/* ───── 가독성 핫픽스: 카드 밖(라디오/캡션) ───── */
.stRadio, .stRadio * {{
  color: var(--ink) !important;
  -webkit-text-fill-color: var(--ink) !important;
  opacity: 1 !important;
  mix-blend-mode: normal !important;
  text-shadow: none !important;
}}
.block-card ~ div .stRadio, .block-card ~ div .stRadio * {{
  color: var(--ink) !important;
  -webkit-text-fill-color: var(--ink) !important;
}}
[data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] * {{ color-scheme: light; }}

/* 타이트 헤더 전용 여백 */
.block-card.tight-head {{ 
  margin: 8px 0 6px !important; 
  padding: 14px 18px 10px !important; 
}}
/* 첫 질문 카드 위쪽 간격 더 줄이기 */
.item-card {{ margin: 2px 0 4px !important; }}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# 상태 관리
if "page" not in st.session_state:
    st.session_state.page = "survey"   # 'survey' | 'result'
if "answers" not in st.session_state:
    st.session_state.answers: Dict[int, str] = {}
if "functional" not in st.session_state:
    st.session_state.functional: str | None = None
if "summary" not in st.session_state:
    st.session_state.summary = None  # (total, sev, tr, functional, scores, ts, unanswered)

# ──────────────────────────────────────────────────────────────────────────────
# 문항/선택지
QUESTIONS = [
    {"no":1,"ko":"일상적인 활동(예: 취미나 일상 일과 등)에 흥미나 즐거움을 거의 느끼지 못한다.","domain":"흥미/즐거움 상실"},
    {"no":2,"ko":"기분이 가라앉거나, 우울하거나, 희망이 없다고 느낀다.","domain":"우울한 기분"},
    {"no":3,"ko":"잠들기 어렵거나 자주 깨는 등 수면에 문제가 있었거나, 반대로 너무 많이 잠을 잔다.","domain":"수면 문제"},
    {"no":4,"ko":"평소보다 피곤함을 더 자주 느꼈거나, 기운이 거의 없다.","domain":"피로/에너지 부족"},
    {"no":5,"ko":"식욕이 줄었거나 반대로 평소보다 더 많이 먹는다.","domain":"식욕 변화"},
    {"no":6,"ko":"자신을 부정적으로 느끼거나, 스스로 실패자라고 생각한다.","domain":"죄책감/무가치감"},
    {"no":7,"ko":"일상생활 및 같은 일에 집중하는 것이 어렵다.","domain":"집중력 저하"},
    {"no":8,"ko":"다른 사람들이 눈치챌 정도로 매우 느리게 말하고 움직이거나, 반대로 평소보다 초조하고 안절부절 못한다.","domain":"느려짐/초조함"},
    {"no":9,"ko":"죽는 게 낫겠다는 생각하거나, 어떤 식으로든 자신을 해치고 싶은 생각이 든다.","domain":"자살/자해 생각"},
]
LABELS = ["전혀 아님 (0)", "며칠 동안 (1)", "절반 이상 (2)", "거의 매일 (3)"]
LABEL2SCORE = {LABELS[0]:0, LABELS[1]:1, LABELS[2]:2, LABELS[3]:3}

# ──────────────────────────────────────────────────────────────────────────────
# 유틸: 중증도/반응 라벨
def phq_severity(total: int) -> str:
    return ("최소" if total<=4 else
            "경도" if total<=9 else
            "중등도" if total<=14 else
            "중등도-중증" if total<=19 else
            "중증")

def treatment_response_label(total: int) -> str:
    if total < 5: return "관해(remission)"
    if total < 10: return "부분 반응(partial response)"
    return "해당 없음"

# ──────────────────────────────────────────────────────────────────────────────
# PHQ-9 도메인 인덱스(1-based)
COG_AFF = [1, 2, 6, 7, 9]   # 인지·정서(5문항)
SOMATIC = [3, 4, 5, 8]      # 신체/생리(4문항)

# ──────────────────────────────────────────────────────────────────────────────
def build_severity_gauge(total: int) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total,
        number={'suffix': " / 27", 'font': {'size': 22}},
        gauge={
            'axis': {'range': [0, 27], 'tickwidth': 0, 'tickcolor': '#e5e7eb'},
            'bar': {'color': BULLET_MEASURE, 'thickness': 0.18},
            'steps': [
                {'range': [0, 5],  'color': GAUGE_STEPS["min"]},
                {'range': [5, 10], 'color': GAUGE_STEPS["low"]},
                {'range': [10, 15],'color': GAUGE_STEPS["mid"]},
                {'range': [15, 20],'color': GAUGE_STEPS["high"]},
                {'range': [20, 27],'color': GAUGE_STEPS["vhi"]},
            ],
            'threshold': {
                'line': {'color': ACCENT, 'width': 3},
                'thickness': 0.9, 'value': total
            }
        },
        title={'text': "총점 및 중증도 대역", 'font': {'size': 15}}
    ))
    # ← 폭 고정
    fig.update_layout(
        width=720, height=230,
        margin=dict(l=20, r=20, t=80, b=10),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(color=INK, family="Inter, 'Noto Sans KR', Arial, sans-serif"),
        showlegend=False
    )
    return fig

def render_gauge_legend():
    st.markdown(f"""
    <div style="display:flex; gap:14px; align-items:center; margin:6px 6px 12px 6px; font-size:12px; color:{SUBTLE}; flex-wrap:wrap;">
      <span style="display:inline-flex; align-items:center; gap:6px;">
        <i style="width:14px; height:10px; background:{GAUGE_STEPS['min']}; border:1px solid #e5e7eb; display:inline-block;"></i> 0–4(최소)
      </span>
      <span style="display:inline-flex; align-items:center; gap:6px;">
        <i style="width:14px; height:10px; background:{GAUGE_STEPS['low']}; border:1px solid #e5e7eb; display:inline-block;"></i> 5–9(경도)
      </span>
      <span style="display:inline-flex; align-items:center; gap:6px;">
        <i style="width:14px; height:10px; background:{GAUGE_STEPS['mid']}; border:1px solid #e5e7eb; display:inline-block;"></i> 10–14(중등도)
      </span>
      <span style="display:inline-flex; align-items:center; gap:6px;">
        <i style="width:14px; height:10px; background:{GAUGE_STEPS['high']}; border:1px solid #e5e7eb; display:inline-block;"></i> 15–19(중등–중증)
      </span>
      <span style="display:inline-flex; align-items:center; gap:6px;">
        <i style="width:14px; height:10px; background:{GAUGE_STEPS['vhi']}; border:1px solid #e5e7eb; display:inline-block;"></i> 20–27(중증)
      </span>
    </div>
    """, unsafe_allow_html=True)



# ──────────────────────────────────────────────────────────────────────────────
# 새 시각화 ②: 가로형 불릿 2개(인지·정서 vs 신체/생리)
BULLET_BANDS = {
    "low":   "#eef2ff",
    "mid":   "#e2e8f0",
    "high":  "#fde68a"
}

def build_bullet_pair_uniform(scores: List[int]) -> go.Figure:
    # 안전 보정
    if len(scores) < 9:
        scores = (scores + [0]*9)[:9]

    # 원점수와 최대치
    cog = sum(scores[i-1] for i in COG_AFF); max_cog = 15  # 5문항
    som = sum(scores[i-1] for i in SOMATIC); max_som = 12  # 4문항

    cats = ["인지·정서", "신체/생리"]
    ratios = [cog/max_cog if max_cog else 0, som/max_som if max_som else 0]
    labels_right = [f"{cog} / {max_cog}", f"{som} / {max_som}"]

    fig = go.Figure()

    # 트랙(길이 1로 동일)
    for cat in cats:
        fig.add_trace(go.Bar(
            x=[1.0], y=[cat], orientation='h',
            marker=dict(color=BULLET_TRACK),
            hoverinfo='skip', showlegend=False
        ))

    # 측정치(비율)
    fig.add_trace(go.Bar(
        x=ratios, y=cats, orientation='h',
        marker=dict(color=BULLET_MEASURE),
        width=0.35, name="점수(비율)",
        hovertemplate="%{y}: %{x:.0%}",
        text=[f"{r*100:.0f}%" for r in ratios],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=11, color="#ffffff")
    ))

    # 오른쪽 끝에 절대점수 주석(예: 12 / 15)
    for i, (r, lab) in enumerate(zip(ratios, labels_right)):
        fig.add_annotation(
            x=1.02, y=i, xref="x", yref="y",
            text=lab, showarrow=False,
            font=dict(size=12, color=INK), xanchor="left", yanchor="middle"
        )

    fig.update_layout(
        barmode='overlay',
        xaxis=dict(range=[0, 1.08], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, tickfont=dict(color=INK)),
        # ⬇⬇⬇ 레전드를 아래로 내리고 보더/배경 추가
        legend=dict(
            orientation='h',
            yanchor='top', y=-0.22,  # 그래프 아래로 이동
            xanchor='left', x=0,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#e5e7eb', borderwidth=1,
            font=dict(size=12, color=INK)
        ),
        # ⬇⬇⬇ 레전드가 들어갈 하단 여백
        margin=dict(l=10, r=30, t=8, b=46),
        height=150,
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(color=INK, family="Inter, 'Noto Sans KR', Arial, sans-serif")
    )

    fig.update_traces(marker_line_width=0)
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# 서버 사이드 결과 PNG 생성 (ORCA 전용)
# def _find_font_path() -> str | None:
#     candidates = [
#         "C:/Windows/Fonts/malgun.ttf",
#         "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
#         "/System/Library/Fonts/AppleSDGothicNeo.ttc",
#     ]
#     for p in candidates:
#         if os.path.exists(p):
#             return p
#     return None

# _FONT_PATH = _find_font_path()

# def _font(size: int):
#     try:
#         if _FONT_PATH:
#             return ImageFont.truetype(_FONT_PATH, size)
#     except Exception:
#         pass
#     return ImageFont.load_default()

# def make_result_png(summary) -> bytes:
#     """summary = (total, sev, tr, functional, scores, ts, unanswered)"""
#     total, sev, tr, functional, scores, ts, unanswered = summary

#     # ── 차트 PNG (ORCA)
#     # 게이지: 컴팩트(230px)
#     gauge_fig = build_severity_gauge(total)
#     gauge_png = pio.to_image(gauge_fig, format="png", width=820, height=230, engine="orca")
#     gauge_img = Image.open(io.BytesIO(gauge_png))

#     # 불릿 2개: 가로형(180px)
#     bullet_fig = build_bullet_pair(scores)  # ← Figure 단일 반환
#     bullet_png = pio.to_image(bullet_fig, format="png", width=820, height=180, engine="orca")
#     bullet_img = Image.open(io.BytesIO(bullet_png))

#     # ── 캔버스 구성
#     W = 1200                # 결과지 전체 폭 (타이트)
#     P = 40                  # 좌우 여백
#     cur_y = P
#     canvas = Image.new("RGB", (W, 1200), "white")
#     d = ImageDraw.Draw(canvas)

#     # 폰트
#     font24 = _font(24); font28 = _font(28); font32 = _font(32); font40 = _font(40)

#     # 헤더
#     d.text((P, cur_y), "PHQ-9 결과 요약", fill=INK, font=font40); cur_y += 52
#     d.text((P, cur_y), f"검사 일시: {ts}", fill=SUBTLE, font=font24); cur_y += 28

#     # 메트릭(3열)
#     cur_y += 8
#     box_h = 96; box_w = (W - P*2 - 20) // 3
#     for i, (lab, val) in enumerate([("총점", f"{total} / 27"),
#                                     ("중증도", sev),
#                                     ("치료 반응", tr)]):
#         x0 = P + i*(box_w+10); y0 = cur_y
#         d.rectangle([x0, y0, x0+box_w, y0+box_h], outline=BORDER, fill="#f8fafc", width=2)
#         d.text((x0+14, y0+12), lab, fill=SUBTLE, font=font24)
#         d.text((x0+14, y0+48), val, fill=INK, font=font32)
#     cur_y += box_h + 18

#     # 부가 정보
#     if functional:
#         d.text((P, cur_y), f"기능 손상: {functional}", fill=SUBTLE, font=font24); cur_y += 30
#     if unanswered > 0:
#         d.rectangle([P, cur_y, W-P, cur_y+58], outline="#ffe594", fill="#fff7d6")
#         d.text((P+12, cur_y+16), f"⚠ 미응답 {unanswered}개 문항은 0점으로 계산됨", fill="#8a6d00", font=font24)
#         cur_y += 70

#     # 차트 배치
#     canvas.paste(gauge_img, (P, cur_y)); cur_y += gauge_img.height + 10
#     canvas.paste(bullet_img, (P, cur_y)); cur_y += bullet_img.height + 12

#     # 안전 안내
#     if scores[8] > 0:
#         d.rectangle([P, cur_y, W-P, cur_y+110], outline=ACCENT, fill="#fff1f4", width=2)
#         d.text((P+14, cur_y+10), "안전 안내 (문항 9 관련)", fill="#9f1239", font=font28)
#         d.text((P+14, cur_y+44), "자살·자해 생각이 있을 때 즉시 도움 받기", fill=SUBTLE, font=font24)
#         d.text((P+14, cur_y+74), "한국: 1393(24시간), 1577-0199 · 긴급 시 112/119.", fill=INK, font=font24)
#         cur_y += 126

#     # 저작권
#     d.text((P, cur_y),
#            "PHQ-9는 공공 도메인(Pfizer 별도 허가 불필요).\n"
#            "Kroenke, Spitzer, & Williams (2001) JGIM · Spitzer, Kroenke, & Williams (1999) JAMA.",
#            fill=SUBTLE, font=font24, align="left")
#     cur_y += 60

#     # 캔버스 트리밍 & 반환
#     cropped = canvas.crop((0, 0, W, min(cur_y + 16, canvas.height)))
#     out = io.BytesIO(); cropped.save(out, format="PNG"); out.seek(0)
#     return out.getvalue()

# ──────────────────────────────────────────────────────────────────────────────
# 상단 헤더
st.markdown("""
<div class="block-card" style="position:sticky; top:0; z-index:5;">
  <span class="badge">PHQ-9</span>
  <span style="font-weight:900; font-size:1.15rem; margin-left:8px;">우울 증상 자기보고 검사</span>
  <div class="small-muted" style="margin-top:4px;">지난 2주 동안의 증상 빈도(0~3점)를 선택합니다.</div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# 설문 페이지
if st.session_state.page == "survey":
    st.markdown("""
    <div class="block-card">
      <div class="section-title">지시문</div>
      <ul class="k-list">
        <li>각 문항에 대해 <b>전혀 아님(0)</b> / <b>며칠 동안(1)</b> / <b>절반 이상(2)</b> / <b>거의 매일(3)</b> 중에서 선택하세요.</li>
        <li>마지막 항목은 이 문제들로 인해 <b>일·집안일·대인관계</b>에 얼마나 어려움이 있었는지 표시합니다.</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="block-card tight-head"><div class="section-title">질문지 (지난 2주)</div>', unsafe_allow_html=True)
    st.caption("표준 PHQ-9 · 빈도 0–3점 척도")

    for q in QUESTIONS:
        st.markdown(
            f"""
            <div class="item-card">
              <div style="display:flex; gap:10px; align-items:flex-start;">
                <div class="item-no">{q['no']}</div>
                <div style="flex:1;">
                  <div style="font-weight:600; line-height:1.55; color:#0f172a;">{q['ko']}</div>
                  <div class="item-domain">{q['domain']}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True
        )
        st.session_state.answers[q["no"]] = st.radio(
            label=" ", options=LABELS, index=None, horizontal=True,
            label_visibility="collapsed", key=f"q{q['no']}"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.session_state.functional = st.radio(
        "추가 질문(기능 손상) — “이 문제들 때문에 일·집안일·대인관계가 얼마나 어려웠습니까?”",
        options=["전혀 어렵지 않음", "어렵지 않음", "어려움", "매우 어려움"],
        index=None, horizontal=True
    )

    if st.button("결과 보기", type="primary", use_container_width=True):
        scores, unanswered = [], 0
        for i in range(1,10):
            lab = st.session_state.answers.get(i)
            if lab is None:
                unanswered += 1; scores.append(0)
            else:
                scores.append(LABEL2SCORE[lab])
        total = sum(scores)
        sev   = phq_severity(total)
        tr    = treatment_response_label(total)
        ts    = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.summary = (total, sev, tr, st.session_state.functional, scores, ts, unanswered)
        st.session_state.page = "result"; st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# 결과 페이지
if st.session_state.page == "result":
    if not st.session_state.summary:
        st.warning("먼저 설문을 완료해 주세요."); st.stop()

    total, sev, tr, functional, scores, ts, unanswered = st.session_state.summary

    if st.button("← 응답 수정하기", use_container_width=True):
        st.session_state.page = "survey"; st.rerun()

    st.markdown(
        f"""
        <div class="block-card">
          <div class="section-title" style="font-size:1.25rem;">PHQ-9 결과 요약</div>
          <div class="small-muted">검사 일시: {ts}</div>
          <div style="height:8px;"></div>
          <div class="metric-box">
            <div class="metric"><div class="label">총점</div>
              <div class="value">{total} <span class="small-muted">/ 27</span></div></div>
            <div class="metric"><div class="label">중증도</div>
              <div class="value">{sev}</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if functional:
         st.caption(f"기능 손상: {functional}")
    if unanswered > 0:
        st.markdown(f'<div class="warn">⚠️ 미응답 {unanswered}개 문항은 0점으로 계산되었습니다.</div>', unsafe_allow_html=True)

    # 상단 메트릭과 균형 잡힌 컴팩트 게이지
    # 게이지(폭 고정) – container_width=False
    # 게이지: 폭 고정 + 레전드
    st.plotly_chart(build_severity_gauge(total), use_container_width=False, config={"displayModeBar": False})
    render_gauge_legend()

    # 불릿: 동일 길이 트랙(정규화 버전)
    st.plotly_chart(build_bullet_pair_uniform(scores), use_container_width=True, config={"displayModeBar": False})



    # 안전 안내
    if scores[8] > 0:
        st.markdown("""
        <div class="safety">
          <div class="section-title" style="color:#9f1239; margin-bottom:6px;">안전 안내 (문항 9 관련)</div>
          <div class="small-muted">자살·자해 생각이 있을 때 즉시 도움 받기</div>
          <div>한국: <b>1393 자살예방상담(24시간)</b>, <b>정신건강상담 1577-0199</b> · 긴급 시 <b>112/119</b>.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="small-muted" style="margin-top:8px;">
      PHQ-9는 공공 도메인(Pfizer 별도 허가 불필요).<br>
      Kroenke, Spitzer, & Williams (2001) JGIM · Spitzer, Kroenke, & Williams (1999) JAMA.
    </div>
    """, unsafe_allow_html=True)

    # ───────── 결과 PNG 다운로드(비활성화 예시) ─────────
    if False:
        st.markdown('<div class="block-card"><div class="section-title">결과 저장</div>', unsafe_allow_html=True)
        try:
            if not _ORCA_PATH:
                raise RuntimeError("ORCA 실행파일을 찾지 못했습니다. 서버 환경변수 PLOTLY_ORCA 또는 PATH에 orca를 등록해 주세요.")
            png_bytes = make_result_png(st.session_state.summary)
            st.download_button(
                label="🖼 결과지 PNG 다운로드 (ORCA)",
                data=png_bytes,
                file_name=f"PHQ9_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                mime="image/png",
                use_container_width=True
            )
            st.caption(f"엔진: **ORCA** · 경로: `{_ORCA_PATH}`")
        except Exception as e:
            st.warning("서버에서 ORCA 엔진을 찾지 못해 PNG를 생성할 수 없습니다.")
            st.error(str(e))
        st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# 끝
