# -*- coding: utf-8 -*-
import os
from datetime import datetime
from typing import Dict, List

# 상단 import들
import streamlit as st
import plotly.graph_objects as go
from streamlit.components.v1 import html as st_html

# ──────────────────────────────────────────────────────────────────────────────
# 페이지 설정
st.set_page_config(page_title="PHQ-9 자기보고 검사", page_icon="📝", layout="centered")

# 색상 토큰 (라이트 테마)
INK     = "#0f172a"   # 본문 텍스트
SUBTLE  = "#475569"   # 보조 텍스트
CARD_BG = "#ffffff"   # 카드 배경
APP_BG  = "#f6f7fb"   # 전체 배경
BORDER  = "#e5e7eb"   # 경계선
BRAND   = "#2563eb"   # 브랜드/포커스
ACCENT  = "#e11d48"   # 경고/강조

# ──────────────────────────────────────────────────────────────────────────────
# 전역 스타일 (단일 블록)
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

:root {{
  --ink:{INK}; --subtle:{SUBTLE}; --bg:{APP_BG}; --card:{CARD_BG};
  --border:{BORDER}; --brand:{BRAND}; --accent:{ACCENT};
}}

html, body, [data-testid="stAppViewContainer"] {{
  background: var(--bg);
  color: var(--ink);
  font-family: "Inter","Noto Sans KR",system-ui,-apple-system,Segoe UI,Roboto,Apple SD Gothic Neo,Helvetica,Arial,sans-serif;
}}

[data-testid="stAppViewContainer"] .main .block-container {{
  max-width: 980px;
  padding-top: 14px;
}}

.block-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 18px 18px 14px 18px;
  margin-bottom: 16px;
  box-shadow: 0 6px 18px rgba(15,23,42,.04);
}}

.badge {{
  display:inline-block; padding:6px 12px; border-radius:14px;
  background:#e8f0ff; color:#1d4ed8; border:1px solid #c7d2fe;
  font-weight:800; font-size:.92rem; letter-spacing:-.2px;
}}

.chip {{
  display:inline-block; padding:6px 12px; border-radius:999px;
  background:#f8fafc; color:var(--ink); border:1px solid var(--border);
  font-size:.9rem;
}}

.section-title {{ font-weight:900; font-size:1.08rem; margin:2px 0 10px; color:var(--ink); }}
.small-muted   {{ color:var(--subtle); font-size:.92rem; }}

.divider {{
  height: 1px; background: linear-gradient(90deg, transparent, #e8ecf3, transparent);
  margin: 14px 0;
}}

ul.k-list {{ margin:0; padding-left:1.2rem; color:var(--ink); }}
ul.k-list li {{ margin: .2rem 0; }}

/* 문항 카드 & 라디오 */
.item-card {{
  border:1.5px solid var(--border);
  border-radius:16px;
  padding:14px 12px;
  margin-bottom:12px;
  background:#fff;
  box-shadow: 0 1px 5px rgba(15,23,42,.03);
}}
.item-no {{ min-width:2.2em; font-weight:900; font-size:1.05rem; color:var(--ink); }}
.item-domain {{
  display:inline-block; padding:4px 10px; border-radius:999px; border:1px solid #cbd5e1;
  background:#f1f5f9; color:var(--ink); font-size:.84rem; margin-top:6px;
}}

div[role="radiogroup"] label, div[role="radiogroup"] span {{
  color: var(--ink) !important;
  opacity: 1 !important;
}}
.stRadio > div {{ gap: 10px; }}
.stRadio [role="radio"] {{ padding: 6px 8px; border-radius:10px; }}
.stRadio [role="radio"]:hover {{ background:#f3f6fb; }}

/* 경고/안전/메트릭 */
.warn {{
  background:#fff7d6; color:#8a6d00; border:1px solid #ffe594;
  border-radius:10px; padding:12px; margin:10px 0;
}}
.safety {{
  border:2px solid var(--accent); background:#fff1f4; border-radius:12px; padding:14px;
}}
.metric-box {{ display:flex; gap:10px; flex-wrap:wrap; }}
.metric {{
  flex:1 1 200px; border:1px dashed var(--border); border-radius:14px; padding:14px; background:#f8fafc;
}}
.metric .label {{ color:var(--subtle); font-weight:600; }}
.metric .value {{ font-size:1.9rem; font-weight:900; color:var(--ink); line-height:1.1; }}

/* 차트 라운드 */
.js-plotly-plot, .plotly, .main-svg {{ border-radius:12px; }}

/* 버튼 - 글자색 확실히 흰색으로 고정 */
.stButton > button {{
  background: var(--brand); color:#fff !important; border:none; border-radius:12px;
  padding: 12px 16px; font-weight:800; letter-spacing:.1px;
  box-shadow:0 6px 16px rgba(37,99,235,.25);
}}
.stButton > button:hover {{ filter: brightness(1.05); }}

button#save-btn:hover {{ filter: brightness(1.05); }}

/* 전역 타이포 가독성 */
html, body, [data-testid="stMarkdownContainer"], p, li, label, span, h1,h2,h3,h4,h5,h6 {{
  color: var(--ink) !important;
}}
.stCaption, [data-testid="stMarkdownContainer"] em {{ color: var(--subtle) !important; }}

/* 프린트 최적화 */
@media print {{
  body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  [data-testid="stSidebar"], #save-area {{ display:none !important; }}
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

def build_plot(scores: List[int]) -> go.Figure:
    x = [f"Q{i}" for i in range(1, 10)]
    y = scores
    line = go.Scatter(
        x=x, y=y, mode="lines+markers",
        line=dict(shape="spline", width=3),
        marker=dict(size=10, line=dict(width=1, color="#ffffff")),
        hovertemplate="%{x}<br>점수 %{y}<extra></extra>",
        name="점수"
    )
    area = go.Scatter(
        x=x, y=y, mode="lines",
        line=dict(shape="spline", width=0),
        fill="tozeroy", opacity=0.20,
        hoverinfo="skip", showlegend=False
    )
    labels = go.Scatter(
        x=x, y=[min(3, v)+0.08 for v in y], mode="text",
        text=[str(v) for v in y], textposition="top center",
        textfont=dict(size=12), showlegend=False, hoverinfo="skip"
    )
    fig = go.Figure([area, line, labels])
    fig.update_layout(
        title="문항별 점수",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin=dict(l=40, r=20, t=60, b=40),
        xaxis=dict(title="문항", showgrid=False, zeroline=False, tickfont=dict(size=12)),
        yaxis=dict(title="점수(0–3)", range=[0, 3.2], dtick=1, gridcolor="#eaeef6", zeroline=False),
        font=dict(color=INK, size=14),
    )
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# 상단 헤더
st.markdown("""
<div class="block-card" style="position:sticky; top:0; z-index:5;">
  <span class="badge">PHQ-9</span>
  <span style="font-weight:900; font-size:1.15rem; margin-left:8px;">우울 증상 자기보고 검사</span>
  <span style="float:right;"><span class="chip">초기 응답 미선택</span></span>
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

    st.markdown('<div class="block-card"><div class="section-title">질문지 (지난 2주)</div>', unsafe_allow_html=True)
    st.caption("표준 PHQ-9 · 빈도 0–3점 척도")
    for q in QUESTIONS:
        st.markdown(
            f"""
            <div class="item-card">
              <div style="display:flex; gap:10px; align-items:flex-start;">
                <div class="item-no">{q['no']}</div>
                <div style="flex:1;">
                  <div style="font-weight:600; line-height:1.55;">{q['ko']}</div>
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
                unanswered += 1
                scores.append(0)
            else:
                scores.append(LABEL2SCORE[lab])
        total = sum(scores)
        sev   = phq_severity(total)
        tr    = treatment_response_label(total)
        ts    = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.summary = (total, sev, tr, st.session_state.functional, scores, ts, unanswered)
        st.session_state.page = "result"
        st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# 결과 페이지
if st.session_state.page == "result":
    if not st.session_state.summary:
        st.warning("먼저 설문을 완료해 주세요.")
        st.stop()

    total, sev, tr, functional, scores, ts, unanswered = st.session_state.summary

    if st.button("← 응답 수정하기", use_container_width=True):
        st.session_state.page = "survey"
        st.rerun()

    # ====== 캡처 시작 마커 ======
    st.markdown('<div id="cap-start"></div>', unsafe_allow_html=True)

    # 결과 내용
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
            <div class="metric"><div class="label">치료 반응</div>
              <div class="value">{tr}</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if functional:
        st.caption(f"기능 손상: {functional}")
    if unanswered > 0:
        st.markdown(f'<div class="warn">⚠️ 미응답 {unanswered}개 문항은 0점으로 계산되었습니다.</div>', unsafe_allow_html=True)

    fig = build_plot(scores)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

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

    # ====== 캡처 종료 마커 ======
    st.markdown('<div id="cap-end"></div>', unsafe_allow_html=True)

    # 결과 저장 버튼(캡처 제외)
    st.markdown("""
    <div class="block-card" id="save-area">
      <div class="section-title">결과 저장</div>
      <div class="small-muted">아래 버튼을 누르면 <b>위에 보이는 결과 영역</b>만 이미지(PNG)로 저장됩니다.</div>
      <div style="margin-top:10px;">
        <button data-skip-capture id="save-btn" style="
          background: #2563eb; color: #fff; border: none; border-radius: 10px;
          padding: 10px 16px; font-weight:700; cursor:pointer; box-shadow:0 4px 12px rgba(37,99,235,.25);
        ">📸 결과 화면 이미지로 저장</button>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# 캡처 스크립트 (마커 사이 영역을 좌표로 캡처)
# ↓↓↓ 이 블록만 통째로 교체 ↓↓↓
st_html(
    """
<script>
(async function(){
  const P = parent, PD = parent.document;
  const btn = PD.getElementById("save-btn");
  if (!btn) return;

  // html2canvas 로드
  async function ensure(src, globalName){
    if (P[globalName]) return;
    await new Promise((res, rej)=>{
      const s = PD.createElement("script");
      s.src = src; s.onload = res; s.onerror = rej;
      PD.head.appendChild(s);
    });
  }
  await ensure("https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js","html2canvas");

  // Plotly div → PNG dataURL
  async function plotlyDivToPng(plotDiv, widthPx){
    if (!plotDiv || !P.Plotly) return null;
    try{
      const w = Math.max(600, Math.floor(widthPx));
      const h = Math.max(300, Math.floor(w * 0.5));
      return await P.Plotly.toImage(plotDiv, {format:"png", width:w*2, height:h*2, scale:1});
    }catch(e){ console.warn("Plotly.toImage 실패:", e); return null; }
  }

  function download(url, prefix){
    const a = PD.createElement("a");
    const ts = new Date().toISOString().slice(0,16).replace(/[:-]/g,"").replace("T","_");
    a.href = url; a.download = `${prefix}_${ts}.png`;
    PD.body.appendChild(a); a.click(); a.remove();
  }

  btn.onclick = async () => {
    const start = PD.getElementById("cap-start");
    const end   = PD.getElementById("cap-end");
    if (!start || !end){ alert("캡처 영역 마커를 찾을 수 없습니다."); return; }

    // 메인 컨테이너
    const container = PD.querySelector('[data-testid="stAppViewContainer"] .main .block-container') || PD.body;

    // 좌표
    const crect = container.getBoundingClientRect();
    const srect = start.getBoundingClientRect();
    const erect = end.getBoundingClientRect();

    // 넉넉한 여백 (잘림 방지)
    const padLeftRight = 16;   // 좌우 여백
    const padTop       = 32;   // 위 여백
    const padBottom    = 32;   // 아래 여백

    // 클리핑 계산: 세로는 cap-start의 'top'부터 cap-end의 'bottom'까지
    const clipX = Math.max(0, Math.floor(crect.left) + P.scrollX - padLeftRight);
    const clipW = Math.ceil(crect.width) + padLeftRight*2;

    const topY    = Math.min(srect.top, srect.bottom);   // 마커가 0px 높이라도 안전
    const bottomY = Math.max(erect.top, erect.bottom);

    let clipY = Math.max(0, Math.floor(topY) + P.scrollY - padTop);
    let clipH = Math.ceil(bottomY - topY) + padTop + padBottom;

    if (clipH <= 0){ alert("캡처할 내용이 없습니다."); return; }

    // 영역 안의 Plotly만 임시 PNG로 치환
    const plots = Array.from(container.querySelectorAll('.js-plotly-plot'));
    const replacements = [];
    for (const plot of plots){
      const r = plot.getBoundingClientRect();
      const midY = (r.top + r.bottom)/2;
      if (midY >= topY && midY <= bottomY){
        try{
          const png = await plotlyDivToPng(plot, r.width);
          if (png){
            const img = PD.createElement("img");
            img.src = png;
            img.style.width = "100%";
            img.style.height = "auto";
            img.style.borderRadius = "12px";
            plot.parentNode.replaceChild(img, plot);
            replacements.push({img, plot});
          }
        }catch(e){ console.warn("Plotly 치환 실패:", e); }
      }
    }

    // 캡처 실행
    try{
      try{ await PD.fonts.ready; }catch(e){}
      const canvas = await P.html2canvas(PD.body, {
        backgroundColor:"#ffffff",
        useCORS:true,
        scale:2,
        x: clipX, y: clipY, width: clipW, height: clipH,
        scrollX: 0, scrollY: 0
      });
      download(canvas.toDataURL("image/png"), "PHQ9");
    }catch(e){
      console.error("캡처 실패:", e);
      alert("이미지 저장에 실패했습니다. 브라우저 확대/축소를 100%로 맞춘 뒤 다시 시도해 주세요.");
    }finally{
      // Plotly 원복
      for (const {img, plot} of replacements){
        img.parentNode?.replaceChild(plot, img);
      }
    }
  };
})();
</script>
""",
    height=0,
)



# ──────────────────────────────────────────────────────────────────────────────
# 끝. 서버 저장 없음(세션 내 계산), 공개 테스트용.
