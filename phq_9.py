# -*- coding: utf-8 -*-
import os
from datetime import datetime
from typing import Dict, List
from textwrap import dedent

import io
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
from PIL import Image, ImageDraw, ImageFont  # PNG 합성용
import platform, shutil  # ← ORCA 자동탐지용

import streamlit.components.v1 as components  # ← 창 닫기용

def _reset_to_survey():
    """앱 상태 초기화 후 설문 첫 화면으로 이동"""
    st.session_state.answers = {}
    st.session_state.functional = None
    st.session_state.summary = None
    for i in range(1, 10):
        st.session_state.pop(f"q{i}", None)
    st.session_state.pop("functional-impact", None)
    st.session_state.page = "survey"


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

# 색상 토큰 (라이트 테마 기본값 – CSS 변수로 재정의)
INK     = "#111827"   # 본문 텍스트
SUBTLE  = "#6B7280"   # 보조 텍스트
CARD_BG = "#FFFFFF"   # 카드 배경
APP_BG  = "#F3F4F6"   # 전체 배경
BORDER  = "#E5E7EB"   # 경계선
BRAND   = "#2563EB"   # 브랜드/포커스
ACCENT  = "#DC2626"   # 경고/강조

# ──────────────────────────────────────────────────────────────────────────────
# 전역 스타일
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

:root {{
  --bg:{APP_BG};
  --card:{CARD_BG};
  --ink:{INK};
  --subtle:{SUBTLE};
  --border:{BORDER};
  --brand:{BRAND};
  --accent:{ACCENT};
  --soft:#F8FAFC;
  --shell-bg:rgba(255,255,255,0.96);
  --inner-card:#FFFFFF;
  --chip-bg:#FFFFFF;
  --chip-border:#D4D4D8;
  --chip-text:#111827;
}}

@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:#020617;
    --card:#0B1220;
    --ink:#E5E7EB;
    --subtle:#9CA3AF;
    --border:#1F2937;
    --brand:#3B82F6;
    --accent:#F97373;
    --soft:#111827;
    --shell-bg:#0D1526;
    --inner-card:#101B2D;
    --chip-bg:#1F2937;
    --chip-border:#334155;
    --chip-text:#F9FAFB;
  }}
}}

[data-testid="stAppViewContainer"] {{
  color-scheme: light dark;
  background: var(--bg);
}}

html, body {{
  background: var(--bg);
  color: var(--ink);
  font-family: "Inter","Noto Sans KR",system-ui,-apple-system,Segoe UI,Roboto,Apple SD Gothic Neo,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}}

body, p, div, span, li, button, label {{
  font-family: "Inter","Noto Sans KR",system-ui,-apple-system,Segoe UI,Roboto,Apple SD Gothic Neo,Helvetica,Arial,sans-serif !important;
}}

[data-testid="block-container"] {{
  max-width: 1100px;
  padding: 0 1.75rem 3rem;
  margin: 0 auto;
}}

.page-frame {{
  max-width: 960px;
  margin: 16px auto;
}}

.section-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 28px 32px;
  box-shadow: 0 24px 48px rgba(15,23,42,0.1);
}}

.report-shell {{
  background: var(--shell-bg);
  border: 1px solid var(--border);
  border-radius: 32px;
  padding: 32px;
  box-shadow: 0 28px 58px rgba(15,23,42,0.15);
}}

.report-shell.compact {{
  padding: 24px 28px;
}}

.report-header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}}

.header-card {{
  display: flex;
  flex-direction: column;
  gap: 10px;
}}

.header-badge {{
  display: inline-flex;
  padding: 4px 14px;
  border-radius: 999px;
  background: rgba(37,99,235,0.12);
  color: var(--brand);
  font-weight: 700;
  font-size: 12px;
  border: 1px solid rgba(37,99,235,0.25);
  width: fit-content;
}}

.header-title {{
  font-size: 1.32rem;
  font-weight: 900;
  letter-spacing: -0.4px;
}}

.section-heading {{
  font-size: 1.08rem;
  font-weight: 800;
  letter-spacing: -0.3px;
  margin-bottom: 4px;
}}

.instruction-list {{
  margin: 14px 0 0;
  padding-left: 20px;
  line-height: 1.6;
  color: var(--ink);
}}

.instruction-list li {{
  margin-bottom: 8px;
}}

.small-muted {{
  color: var(--subtle);
  font-size: 0.92rem;
  letter-spacing: -0.1px;
}}

  .report-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 24px;
  }}

  .report-card {{
    background: var(--inner-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 18px 42px rgba(15,23,42,0.12);
  }}

  .summary-layout {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 28px;
    align-items: stretch;
    margin-top: 28px;
  }}

  .gauge-card {{
    background: var(--inner-card);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 32px 24px 36px;
    text-align: center;
    box-shadow: 0 18px 42px rgba(15,23,42,0.12);
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}

  .gauge-circle {{
    width: 220px;
    height: 220px;
    border-radius: 50%;
    margin: 0 auto 10px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 1px 4px rgba(15,23,42,0.15);
  }}

  .gauge-circle::after {{
    content: "";
    position: absolute;
    inset: 24px;
    border-radius: 50%;
    background: var(--shell-bg);
    box-shadow: inset 0 1px 2px rgba(15,23,42,0.08);
  }}

  .gauge-inner {{
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }}

  .gauge-number {{
    font-size: 3.2rem;
    font-weight: 900;
    line-height: 1;
    color: var(--ink);
  }}

  .gauge-denom {{
    font-size: 1rem;
    font-weight: 700;
    color: var(--subtle);
  }}

  .gauge-severity {{
    display: inline-flex;
    padding: 6px 20px;
    border-radius: 999px;
    font-weight: 800;
    border: 1.5px solid currentColor;
    font-size: 1rem;
  }}

  .narrative-card {{
    background: var(--inner-card);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 28px 30px;
    box-shadow: 0 18px 42px rgba(15,23,42,0.12);
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}

  .narrative-title {{
    font-weight: 800;
    font-size: 1rem;
  }}

  .functional-highlight {{
    border-top: 1px solid var(--border);
    padding-top: 16px;
  }}

  .functional-title {{
    font-size: 0.92rem;
    color: var(--subtle);
    font-weight: 700;
    margin-bottom: 6px;
  }}

  .functional-value {{
    font-size: 1.05rem;
  }}

.report-score-card {{
  display: flex;
  flex-direction: column;
  gap: 14px;
}}

.metric-label {{
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 1.2px;
  color: var(--subtle);
  text-transform: uppercase;
}}

.metric-value {{
  display: flex;
  align-items: baseline;
  gap: 12px;
}}

.metric-number {{
  font-size: 3.6rem;
  font-weight: 900;
  line-height: 1;
  color: var(--ink);
}}

.metric-denom {{
  font-size: 1.2rem;
  color: var(--subtle);
  font-weight: 600;
}}

.severity-tag {{
  display: inline-flex;
  align-items: center;
  padding: 6px 18px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.95rem;
  width: fit-content;
  border: 1.5px solid transparent;
}}

.report-card-title {{
  font-size: 0.84rem;
  letter-spacing: 1.3px;
  text-transform: uppercase;
  color: var(--subtle);
  margin-bottom: 10px;
  font-weight: 700;
}}

.report-shell p {{
  line-height: 1.65;
  margin: 0 0 12px;
}}

.question-section {{
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  margin-bottom: 0;
}}

.question-meta {{
  display: flex;
  flex-direction: column;
  gap: 6px;
}}

.question-label {{
  font-size: 12px;
  font-weight: 700;
  color: var(--subtle);
  letter-spacing: 0.2px;
  text-transform: uppercase;
}}

.question-text {{
  font-weight: 700;
  font-size: 1.02rem;
  line-height: 1.5;
}}

div[data-testid="stVerticalBlock"]:has(.question-meta),
div[data-testid="stVerticalBlock"]:has(.functional-meta) {{
  max-width: 960px;
  margin: 0 auto 12px;
  background: var(--inner-card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 22px 24px 12px;
  box-shadow: 0 16px 32px rgba(15,23,42,0.08);
}}

.functional-divider {{
  height: 1px;
  width: 100%;
  max-width: 960px;
  background: var(--border);
  margin: 10px auto 18px;
}}

.functional-label {{
  font-size: 12px;
  font-weight: 700;
  color: var(--subtle);
  letter-spacing: 0.1px;
  text-transform: uppercase;
}}

.functional-text {{
  font-weight: 650;
  font-size: 0.98rem;
  line-height: 1.5;
}}

.severity-legend {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
}}

.legend-chip {{
  display: flex;
  flex-direction: column;
  padding: 10px 14px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--inner-card);
  min-width: 140px;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
}}

.legend-chip strong {{
  font-size: 0.95rem;
}}

.legend-chip small {{
  color: var(--subtle);
  font-size: 0.8rem;
}}

.domain-panel {{
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 24px 28px;
  background: var(--inner-card);
  box-shadow: 0 18px 42px rgba(15,23,42,0.12);
}}

.domain-profile {{
  display: flex;
  flex-direction: column;
  gap: 22px;
}}

.domain-note {{
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(148,163,184,0.3);
  font-size: 0.82rem;
  color: var(--subtle);
  line-height: 1.45;
}}

.domain-row {{
  display: grid;
  grid-template-columns: 1.4fr 2.5fr 0.5fr;
  gap: 18px;
  align-items: center;
}}

.domain-title {{
  font-weight: 700;
  font-size: 1rem;
}}

.domain-desc {{
  font-size: 0.85rem;
  color: var(--subtle);
  margin-top: 4px;
}}

.domain-bar {{
  position: relative;
  height: 16px;
  background: rgba(148,163,184,0.25);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid rgba(148,163,184,0.4);
}}

.domain-fill {{
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  border-radius: 999px;
  background: var(--brand);
  box-shadow: inset 0 -2px 0 rgba(255,255,255,0.35);
}}

.domain-score {{
  justify-self: end;
  font-weight: 700;
}}

.warn {{
  background: rgba(254,215,170,0.35);
  border:1px solid rgba(251,191,36,0.6);
  color:#92400E;
  border-radius:18px;
  padding:16px 20px;
  max-width: 960px;
  margin: 18px auto 0;
  font-weight: 600;
}}

.safety {{
  background: rgba(248,113,113,0.12);
  border:1px solid rgba(252,165,165,0.6);
  border-radius:22px;
  padding:24px 28px;
  max-width:960px;
  margin: 24px auto 0;
  box-shadow: 0 20px 40px rgba(190,24,93,0.15);
}}

.safety .section-heading {{
  color: var(--accent);
}}

.footer-note {{
  color: var(--subtle);
  font-size: 12px;
  max-width: 960px;
  margin: 24px auto 0;
  line-height: 1.5;
  text-align: center;
}}

div[data-testid="stPlotlyChart"] {{
  max-width: 960px;
  margin: 12px auto 18px;
  background: var(--inner-card);
  border: 1px solid var(--border);
  border-radius: 26px;
  padding: 18px 18px 6px;
  box-shadow: 0 24px 48px rgba(15,23,42,0.12);
}}

div[data-testid="stPlotlyChart"] > div > div {{
  width: 100% !important;
}}

div[data-testid="stHorizontalBlock"] {{
  max-width: 960px;
  margin: 16px auto 0 !important;
}}

.button-anchor {{
  display:none;
}}

div[data-testid="stHorizontalBlock"]:has(.button-anchor) {{
  margin-top: 24px !important;
}}

[data-testid="stToolbar"], #MainMenu, header, footer {{
  display: none !important;
}}

/* ───── 라디오 칩 ───── */
.stRadio {{
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
  margin: 6px 0 10px;
}}

.stRadio > div[role="radiogroup"] {{
  display: flex !important;
  gap: 8px !important;
  flex-wrap: wrap !important;
  align-items: center !important;
}}

.stRadio [role="radio"] {{
  display: inline-flex !important;
  align-items: center !important;
  padding: 10px 22px !important;
  border-radius: 999px !important;
  background: var(--chip-bg) !important;
  border: 1px solid var(--chip-border) !important;
  cursor: pointer !important;
  transition: all .15s ease;
  font-weight:600 !important;
  opacity: 1 !important;
  color: var(--chip-text) !important;
}}

.stRadio [role="radio"] * {{
  color: var(--chip-text) !important;
  -webkit-text-fill-color: var(--chip-text) !important;
  opacity: 1 !important;
}}

.stRadio [role="radio"] > div:first-child {{
  display:none !important;
}}

.stRadio [role="radio"]:hover {{
  border-color: var(--brand) !important;
  box-shadow: 0 3px 10px rgba(37,99,235,0.18);
}}

.stRadio [role="radio"][aria-checked="true"] {{
  background: var(--brand) !important;
  border-color: var(--brand) !important;
  color: #ffffff !important;
  box-shadow: 0 8px 18px rgba(37,99,235,0.35);
}}

.stRadio [role="radio"][aria-checked="true"] * {{
  color:#ffffff !important;
  -webkit-text-fill-color:#ffffff !important;
  opacity: 1 !important;
}}

/* 버튼 */
.stButton {{
  max-width: 960px;
  margin: 0 auto 14px;
}}

.stButton > button {{
  width: 100%;
}}

.stButton > button[data-testid="baseButton-primary"],
.stButton > button[kind="primary"] {{
  background: var(--brand) !important;
  color: #fff !important;
  border: 1.5px solid var(--brand) !important;
  border-radius: 12px !important;
  font-weight: 800 !important;
  letter-spacing: -0.2px;
  min-height: 48px;
  box-shadow: 0 12px 24px rgba(37,99,235,0.28) !important;
}}

.stButton > button:not([data-testid="baseButton-primary"]) {{
  background: var(--inner-card) !important;
  color: var(--brand) !important;
  border: 1.5px solid var(--brand) !important;
  border-radius: 12px !important;
  font-weight: 800 !important;
  min-height: 48px;
  box-shadow: 0 6px 16px rgba(15,23,42,0.1) !important;
}}

@media (max-width: 640px) {{
  [data-testid="block-container"] {{
    padding: 0 1rem 2rem;
  }}
  .report-shell {{
    padding: 24px;
  }}
  .gauge-circle {{
    width: 180px;
    height: 180px;
  }}
  .domain-row {{
    grid-template-columns: 1fr;
  }}
  .domain-score {{
    justify-self: start;
  }}
}}
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
    st.session_state.summary = None  # (total, sev, functional, scores, ts, unanswered)

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
# 유틸: 중증도 라벨
def phq_severity(total: int) -> str:
    return ("정상" if total<=4 else
            "경미" if total<=9 else
            "중등도" if total<=14 else
            "중증" if total<=19 else
            "심각")

# ──────────────────────────────────────────────────────────────────────────────
# PHQ-9 도메인 인덱스(1-based)
COG_AFF = [1, 2, 6, 7, 9]   # 인지·정서(5문항)
SOMATIC = [3, 4, 5, 8]      # 신체/생리(4문항)

# ──────────────────────────────────────────────────────────────────────────────
SEVERITY_SEGMENTS = [
    {"label": "정상", "display": "0–4",  "start": 0,  "end": 5,  "color": "#CDEED6"},
    {"label": "경미", "display": "5–9",  "start": 5,  "end": 10, "color": "#F8F1C7"},
    {"label": "중등도", "display": "10–14","start": 10, "end": 15, "color": "#FFE0B2"},
    {"label": "중증", "display": "15–19","start": 15, "end": 20, "color": "#FBC0A8"},
    {"label": "심각", "display": "20–27","start": 20, "end": 27, "color": "#F6A6A6"},
]

SEVERITY_PILL = {
    "정상": ("#DBEAFE", "#1E3A8A"),
    "경미": ("#FEF3C7", "#92400E"),
    "중등도": ("#FFE4E6", "#9F1239"),
    "중증": ("#FED7AA", "#9A3412"),
    "심각": ("#FECACA", "#7F1D1D"),
}

SEVERITY_ARC_COLOR = {
    "정상": "#16a34a",
    "경미": "#f59e0b",
    "중등도": "#f97316",
    "중증": "#f43f5e",
    "심각": "#b91c1c",
}

SEVERITY_GUIDANCE = {
    "정상": "현재 보고된 주관적 우울 증상은 정상 범위에 해당하며, 기본적인 자기 관리와 모니터링을 이어가시면 됩니다.",
    "경미": "경미 수준의 우울감이 보고되었습니다. 생활리듬 조정과 상담 자원 안내 등 예방적 개입을 고려할 수 있습니다.",
    "중등도": "임상적으로 의미 있는 중등도 수준으로, 정신건강 전문인의 평가와 치료적 개입을 권장합니다.",
    "중증": "중증 수준의 우울 증상이 보고되어, 신속한 전문 평가와 적극적인 치료 계획 수립이 필요합니다.",
    "심각": "심각 수준의 우울 증상이 보고되었습니다. 안전 평가를 포함한 즉각적인 전문 개입이 권고됩니다.",
}

DOMAIN_META = [
    {
        "name": "신체/생리 증상",
        "desc": "(수면, 피곤함, 식욕, 정신운동 문제)",
        "items": SOMATIC,
        "max": 12,
    },
    {
        "name": "인지/정서 증상",
        "desc": "(흥미저하, 우울감, 죄책감, 집중력, 자살사고)",
        "items": COG_AFF,
        "max": 15,
    },
]


def build_total_severity_bar(total: int) -> go.Figure:
    total = max(0, min(total, 27))
    fig = go.Figure()
    annotations = []

    for seg in SEVERITY_SEGMENTS:
        width = seg["end"] - seg["start"]
        fig.add_trace(
            go.Bar(
                x=[width],
                y=["총점"],
                base=seg["start"],
                orientation="h",
                marker=dict(color=seg["color"], line=dict(width=0)),
                hovertemplate=f"{seg['label']} · {seg['display']}점<extra></extra>",
                showlegend=False,
            )
        )
        midpoint = seg["start"] + width / 2
        annotations.append(
            dict(
                x=midpoint,
                y=-0.12,
                xref="x",
                yref="paper",
                text=f"<b>{seg['label']}</b><br><span style='font-size:11px;'>{seg['display']}점</span>",
                showarrow=False,
                align="center",
                font=dict(size=12, color=INK),
            )
        )

    fig.add_shape(
        type="line",
        x0=total,
        x1=total,
        y0=-0.05,
        y1=1.05,
        xref="x",
        yref="paper",
        line=dict(color=BRAND, width=3),
    )
    annotations.append(
        dict(
            x=total,
            y=1.08,
            xref="x",
            yref="paper",
            text=f"{total}점",
            showarrow=False,
            font=dict(size=14, color=BRAND, family="Inter, 'Noto Sans KR', sans-serif"),
            bgcolor="#e0ecff",
            bordercolor=BRAND,
            borderwidth=1,
            borderpad=6,
        )
    )

    fig.update_layout(
        barmode="stack",
        xaxis=dict(
            range=[0, 27],
            showgrid=False,
            zeroline=False,
            tickvals=[0, 5, 10, 15, 20, 27],
            ticks="outside",
            tickfont=dict(size=11),
        ),
        yaxis=dict(showticklabels=False),
        margin=dict(l=30, r=30, t=50, b=60),
        height=260,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color=INK, family="Inter, 'Noto Sans KR', Arial, sans-serif"),
        annotations=annotations,
    )
    return fig


def render_severity_legend():
    spans = "".join(
        f"<div class='legend-chip'><strong>{seg['label']}</strong><small>{seg['display']}점</small></div>"
        for seg in SEVERITY_SEGMENTS
    )
    st.markdown(
        f"""
<div class="page-frame">
  <div class="report-shell compact">
    <div class="severity-legend">{spans}</div>
  </div>
</div>""",
        unsafe_allow_html=True,
    )


def build_domain_profile_html(scores: List[int]) -> str:
    if len(scores) < 9:
        scores = (scores + [0] * 9)[:9]

    rows = []
    for meta in DOMAIN_META:
        score = sum(scores[i - 1] for i in meta["items"])
        ratio = (score / meta["max"]) if meta["max"] else 0
        rows.append(
            dedent(
                f"""
                <div class="domain-row">
                  <div>
                    <div class="domain-title">{meta['name']}</div>
                    <div class="domain-desc">{meta['desc']}</div>
                  </div>
                  <div class="domain-bar">
                    <div class="domain-fill" style="width:{ratio*100:.1f}%"></div>
                  </div>
                  <div class="domain-score">{score} / {meta['max']}</div>
                </div>
                """
            )
        )
    return dedent(
        f"""
        <div class="domain-panel">
          <div class="domain-profile">
            {''.join(rows)}
          </div>
          <div class="domain-note small-muted">※ 각 영역의 점수는 높을수록 해당 영역의 우울 관련 증상이 더 많이 보고되었음을 의미합니다.</div>
        </div>
        """
    )


def compose_narrative(total: int, severity: str, functional: str | None, item9: int) -> str:
    base = f"총점 {total}점(27점 만점)으로, [{severity}] 수준의 우울 증상이 보고되었습니다. {SEVERITY_GUIDANCE[severity]}"
    functional_text = (
        f" 응답자 보고에 따르면, 이러한 증상으로 인한 일·집안일·대인관계의 어려움은 ‘{functional}’ 수준입니다."
        if functional else ""
    )
    safety_text = (
        " 특히, 자해/자살 관련 사고(9번 문항)가 보고되어 이에 대한 즉각적인 관심과 평가가 매우 중요합니다."
        if item9 > 0 else ""
    )
    return base + functional_text + safety_text


# ──────────────────────────────────────────────────────────────────────────────
# UI 헬퍼
def render_question_item(question: Dict[str, str | int]) -> None:
    st.markdown(
        dedent(
            f"""
            <div class="question-meta">
              <div class="question-label">문항 {question['no']}</div>
              <div class="question-text">{question['ko']}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
    st.session_state.answers[question["no"]] = st.radio(
        label=f"문항 {question['no']}",
        options=LABELS,
        index=None,
        horizontal=True,
        label_visibility="collapsed",
        key=f"q{question['no']}",
    )


def render_functional_block() -> None:
    st.markdown('<div class="functional-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        dedent(
            """
            <div class="functional-meta">
              <div class="functional-label">기능 손상</div>
              <div class="functional-text">이 문제들 때문에 일·집안일·대인관계에 얼마나 어려움이 있었습니까?</div>
              <div class="small-muted" style="margin-top:4px;">가장 가까운 수준을 선택해 주세요.</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
    st.session_state.functional = st.radio(
        "기능 손상",
        options=["전혀 어렵지 않음", "어렵지 않음", "어려움", "매우 어려움"],
        index=None,
        horizontal=True,
        label_visibility="collapsed",
        key="functional-impact",
    )


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
#     """summary = (total, sev, functional, scores, ts, unanswered)"""
#     total, sev, functional, scores, ts, unanswered = summary

#     # ── 차트 PNG (ORCA)
#     # 게이지: 컴팩트(230px)
#     gauge_fig = build_severity_gauge(total)
#     gauge_png = pio.to_image(gauge_fig, format="png", width=820, height=230, engine="orca")
#     gauge_img = Image.open(io.BytesIO(gauge_png))

#     # 불릿 2개: 가로형(180px)
#     bullet_fig = build_bullet_pair_uniform(scores)  # ← Figure 단일 반환
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
#     metrics = [("총점", f"{total} / 27"), ("중증도", sev)]
#     if functional:
#         metrics.append(("기능 손상", functional))
#
#     box_h = 96
#     box_w = (W - P*2 - 20) // max(len(metrics), 1)
#     for i, (lab, val) in enumerate(metrics):
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
st.markdown(
    dedent(
        """
        <div class="page-frame">
          <div class="section-card header-card">
            <div class="header-badge">PHQ-9</div>
            <div class="header-title">우울 증상 자기보고 검사</div>
            <p class="small-muted">지난 2주 동안 경험한 증상 빈도를 0~3점 척도로 기록하는 표준화된 자기보고 도구입니다.</p>
          </div>
        </div>
        """
    ),
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# 설문 페이지
if st.session_state.page == "survey":
    st.markdown(
        dedent(
            """
            <div class="page-frame">
              <div class="section-card instruction-card">
                <div class="section-heading">지시문</div>
                <ul class="instruction-list">
                  <li>각 문항에 대해 지난 2주 동안의 빈도를 <b>전혀 아님(0)</b> · <b>며칠 동안(1)</b> · <b>절반 이상(2)</b> · <b>거의 매일(3)</b> 가운데 가장 가까운 값으로 선택합니다.</li>
                  <li>모든 문항과 기능 손상 질문을 완료한 뒤 ‘결과 보기’를 누르면 총점, 중증도, 영역별 분석을 바로 확인할 수 있습니다.</li>
                </ul>
              </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        dedent(
            """
            <div class="page-frame">
              <div class="section-card question-section">
                <div class="section-heading">질문지 (지난 2주)</div>
                <div class="small-muted">표준 PHQ-9 · 모든 문항은 동일한 0–3점 척도를 사용합니다.</div>
              </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    for q in QUESTIONS:
        render_question_item(q)

    render_functional_block()

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
        ts    = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.summary = (total, sev, st.session_state.functional, scores, ts, unanswered)
        st.session_state.page = "result"; st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# 결과 페이지
if st.session_state.page == "result":
    if not st.session_state.summary:
        st.warning("먼저 설문을 완료해 주세요."); st.stop()

    total, sev, functional, scores, ts, unanswered = st.session_state.summary
    item9_score = scores[8] if len(scores) >= 9 else 0

    if st.button("← 응답 수정하기", use_container_width=True):
        st.session_state.page = "survey"; st.rerun()

    narrative = compose_narrative(total, sev, functional, item9_score)
    arc_color = SEVERITY_ARC_COLOR.get(sev, BRAND)
    gauge_percent = (max(0, min(total, 27)) / 27) * 100
    functional_value = functional if functional else "미응답"
    st.markdown(
        dedent(
            f"""
            <div class="page-frame">
              <div class="report-shell">
                <div class="report-header">
                  <div>
                    <div class="section-heading">I. 종합 소견</div>
                    <div class="small-muted">검사 일시: {ts}</div>
                  </div>
                </div>
                <div class="summary-layout">
                  <div class="gauge-card">
                    <div class="metric-label">총점</div>
                    <div class="gauge-circle" style="background: conic-gradient({arc_color} {gauge_percent:.2f}%, rgba(148,163,184,0.25) {gauge_percent:.2f}%, rgba(148,163,184,0.25) 100%);">
                      <div class="gauge-inner">
                        <div class="gauge-number">{total}</div>
                        <div class="gauge-denom">/ 27</div>
                      </div>
                    </div>
                    <div class="gauge-severity" style="color:{arc_color};">{sev}</div>
                  </div>
                  <div class="narrative-card">
                    <div class="narrative-title">주요 소견</div>
                    <p>{narrative}</p>
                    <div class="functional-highlight">
                      <div class="functional-title">일상 기능 손상 (10번 문항)</div>
                      <div class="functional-value"><strong>{functional_value}</strong></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    if unanswered > 0:
        st.markdown(f'<div class="warn">⚠️ 미응답 {unanswered}개 문항은 0점으로 계산되었습니다.</div>', unsafe_allow_html=True)

    domain_html = build_domain_profile_html(scores)
    st.markdown(
        dedent(
            f"""
            <div class="page-frame">
              <div class="report-shell">
                <div class="section-heading" style="margin-bottom:12px;">II. 증상 영역별 프로파일</div>
                {domain_html.strip()}
              </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    if item9_score > 0:
        st.markdown(
            dedent(
                """
                <div class="safety">
                  <div class="section-heading">안전 안내 (문항 9 관련)</div>
                  <div class="small-muted">자살·자해 생각이 있을 때 즉시 도움 받기</div>
                  <div>한국: <b>1393 자살예방상담(24시간)</b>, <b>정신건강상담 1577-0199</b> · 긴급 시 <b>112/119</b>.</div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    button_zone = st.container()
    with button_zone:
        st.markdown('<div class="page-frame">', unsafe_allow_html=True)
        st.markdown('<div class="button-anchor"></div>', unsafe_allow_html=True)
        left, right = st.columns([1, 1], gap="large")
        with left:
            if st.button("새 검사 시작", type="primary"):
                _reset_to_survey()
                st.rerun()
        with right:
            if st.button("닫기"):
                components.html("<script>window.close();</script>", height=0)
                st.info("창이 닫히지 않으면 브라우저 탭을 직접 닫거나 ‘새 검사 시작’을 눌러 주세요.", icon="ℹ️")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        dedent(
            """
            <div class="footer-note">
              PHQ-9는 공공 도메인(Pfizer 별도 허가 불필요).<br>
              Kroenke, Spitzer, & Williams (2001) JGIM · Spitzer, Kroenke, & Williams (1999) JAMA.
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

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
