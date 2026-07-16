import math
import time

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="SN1·SN2 반응 시뮬레이터",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(135deg,#f7fbff 0%,#fff9f2 100%);}
    .main-title {font-size:2.2rem;font-weight:850;color:#172554;line-height:1.15;}
    .sub-title {color:#53657d;margin-top:.35rem;margin-bottom:1.2rem;}
    .chip {display:inline-block;background:#e0ecff;color:#1e3a8a;border-radius:999px;
           padding:.3rem .75rem;margin:.12rem;font-weight:700;font-size:.88rem;}
    .info-card {background:white;border:1px solid #e5eaf2;border-radius:18px;padding:1rem 1.1rem;
                box-shadow:0 10px 30px rgba(31,50,81,.07);min-height:132px;}
    .info-card h4 {margin:.05rem 0 .45rem;color:#172554;}
    .info-card p {margin:.15rem 0;color:#526174;line-height:1.55;}
    div[data-testid="stMetric"] {background:white;border:1px solid #e7eaf0;padding:12px 16px;
                                 border-radius:16px;box-shadow:0 8px 22px rgba(31,50,81,.05);}
    div[data-testid="stSidebar"] {background:#f3f7ff;}
    .small-note {font-size:.88rem;color:#64748b;line-height:1.55;}
    </style>
    """,
    unsafe_allow_html=True,
)


SUBSTRATES = {
    "1-브로모뷰테인 (1차)": {
        "short": "1-브로모뷰테인",
        "formula": "CH₃–CH₂–CH₂–CH₂–Br",
        "degree": "1차",
        "sn1": 0.035,
        "sn2": 1.00,
        "steric": "작음",
        "carbocation": "매우 불안정",
    },
    "2-브로모뷰테인 (2차)": {
        "short": "2-브로모뷰테인",
        "formula": "CH₃–CH(Br)–CH₂–CH₃",
        "degree": "2차",
        "sn1": 0.40,
        "sn2": 0.38,
        "steric": "중간",
        "carbocation": "1차보다 안정",
    },
}

SOLVENTS = {
    "극성 양성자성": {"SN1": 1.35, "SN2": 0.62, "label": "SN1에 유리"},
    "극성 비양성자성": {"SN1": 0.68, "SN2": 1.35, "label": "SN2에 유리"},
    "중간 극성": {"SN1": 0.82, "SN2": 0.86, "label": "둘 다 덜 유리"},
}


def relative_rate(substrate: str, mechanism: str, temperature: int,
                  solvent: str, nucleophile: int) -> float:
    """A qualitative teaching model, not a kinetic prediction."""
    data = SUBSTRATES[substrate]
    structure = data[mechanism.lower()]
    solvent_factor = SOLVENTS[solvent][mechanism]
    temperature_factor = math.exp(0.032 * (temperature - 25))
    # Nucleophile concentration/strength affects SN2 strongly, but is not in the SN1 rate law.
    nucleophile_factor = 0.50 + nucleophile / 5 if mechanism == "SN2" else 1.0
    return structure * solvent_factor * temperature_factor * nucleophile_factor


def rate_label(value: float) -> str:
    if value < 0.08:
        return "거의 진행되지 않음"
    if value < 0.32:
        return "느림"
    if value < 0.85:
        return "보통"
    return "빠름"


def reaction_animation(substrate: str, mechanism: str, speed: float) -> str:
    d = SUBSTRATES[substrate]
    formula = d["formula"]
    if mechanism == "SN2":
        mechanism_html = f"""
        <div class="stage-label">한 단계 반응 · 카보양이온 없음</div>
        <div class="scene sn2">
          <div class="nu">Nu⁻</div>
          <div class="arrow a1">➜</div>
          <div class="molecule"><b>{formula}</b><small>친핵체의 뒤쪽 공격</small></div>
          <div class="arrow a2">➜</div>
          <div class="product"><b>치환 생성물</b><small>Nu 결합</small></div>
          <div class="leaving">Br⁻</div>
        </div>
        <div class="timeline"><span>Nu⁻ 접근</span><span>전이상태</span><span>Br⁻ 이탈</span></div>
        """
    else:
        carb = "CH₃–CH⁺–CH₂–CH₃" if d["degree"] == "2차" else "CH₃–CH₂–CH₂–CH₂⁺"
        mechanism_html = f"""
        <div class="stage-label">두 단계 반응 · 카보양이온 중간체 형성</div>
        <div class="scene sn1">
          <div class="molecule"><b>{formula}</b><small>이온화</small></div>
          <div class="arrow">➜</div>
          <div class="carb"><b>{carb}</b><small>{d['degree']} 카보양이온</small></div>
          <div class="nu top">Nu:</div>
          <div class="arrow">➜</div>
          <div class="product"><b>치환 생성물</b><small>Nu 결합</small></div>
          <div class="leaving">Br⁻</div>
        </div>
        <div class="timeline"><span>Br⁻ 먼저 이탈</span><span>카보양이온</span><span>Nu 공격</span></div>
        """

    duration = max(1.2, min(5.0, 3.8 / max(speed, 0.15)))
    return f"""
    <html><head><style>
      *{{box-sizing:border-box}} body{{margin:0;font-family:Arial,'Noto Sans KR',sans-serif;color:#172554}}
      .lab{{height:310px;border-radius:24px;padding:20px;background:
        radial-gradient(circle at 15% 20%,#dbeafe 0,transparent 35%),
        radial-gradient(circle at 85% 75%,#ffedd5 0,transparent 32%),#f8fafc;
        border:1px solid #dbe4f0;overflow:hidden;position:relative}}
      .stage-label{{display:inline-block;background:#172554;color:white;border-radius:999px;padding:7px 13px;font-size:13px}}
      .scene{{height:205px;display:flex;align-items:center;justify-content:center;gap:17px;position:relative}}
      .molecule,.product,.carb{{padding:18px 20px;background:white;border:2px solid #88a7d8;border-radius:18px;
        box-shadow:0 9px 24px #6682a526;text-align:center;min-width:150px}}
      .molecule b,.product b,.carb b{{font-size:18px;white-space:nowrap}} small{{display:block;margin-top:7px;color:#64748b}}
      .carb{{border-color:#f59e0b;background:#fffbeb;animation:pulse {duration}s infinite}}
      .product{{border-color:#22c55e;background:#f0fdf4;animation:appear {duration}s infinite}}
      .nu{{font-size:21px;font-weight:800;color:#7c3aed;animation:approach {duration}s infinite}}
      .sn1 .nu.top{{position:absolute;top:20px;left:53%;animation:drop {duration}s infinite}}
      .arrow{{font-size:28px;color:#7c8da5}} .a1{{animation:fade {duration}s infinite}}
      .leaving{{position:absolute;color:#c2410c;font-weight:800;font-size:20px;right:31%;top:38%;
        animation:leave {duration}s infinite}}
      .timeline{{display:flex;justify-content:space-around;border-top:2px dashed #cbd5e1;padding-top:10px;color:#526174;font-size:13px}}
      @keyframes approach{{0%,12%{{transform:translateX(-25px);opacity:.4}}45%,70%{{transform:translateX(6px);opacity:1}}100%{{transform:translateX(-25px);opacity:.4}}}}
      @keyframes drop{{0%,35%{{transform:translateY(-22px);opacity:.2}}65%,85%{{transform:translateY(28px);opacity:1}}100%{{transform:translateY(-22px);opacity:.2}}}}
      @keyframes leave{{0%,35%{{transform:translate(0,0);opacity:1}}70%,100%{{transform:translate(75px,-45px);opacity:.15}}}}
      @keyframes appear{{0%,48%{{opacity:.15;transform:scale(.9)}}75%,100%{{opacity:1;transform:scale(1)}}}}
      @keyframes pulse{{0%,35%{{box-shadow:0 0 0 0 #f59e0b66}}60%{{box-shadow:0 0 0 14px #f59e0b00}}100%{{box-shadow:0 0 0 0 #f59e0b00}}}}
      @keyframes fade{{0%,100%{{opacity:.25}}50%{{opacity:1}}}}
      @media(max-width:680px){{.scene{{gap:6px;transform:scale(.78)}}.lab{{padding:12px}}}}
    </style></head><body><div class="lab">{mechanism_html}</div></body></html>
    """


st.markdown('<div class="main-title">🧪 SN1·SN2 반응 시뮬레이터</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">1-브로모뷰테인과 2-브로모뷰테인의 구조가 반응 경향에 미치는 영향을 비교해 보세요.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<span class="chip">입체장애</span><span class="chip">카보양이온 안정성</span>'
    '<span class="chip">용매 효과</span><span class="chip">반응속도</span>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ 실험 조건")
    substrate = st.selectbox("기질", list(SUBSTRATES))
    mechanism = st.radio("반응 경로", ["SN2", "SN1"], horizontal=True)
    solvent = st.selectbox("용매의 성격", list(SOLVENTS))
    temperature = st.slider("온도 (°C)", 10, 70, 25, 5)
    nucleophile = st.slider(
        "친핵체 세기·유효 농도", 1, 5, 3,
        help="교육용 통합 변수입니다. SN2 속도에는 영향을 주지만 SN1 속도식에는 직접 포함되지 않습니다.",
    )
    run = st.button("▶ 시뮬레이션 실행", type="primary", use_container_width=True)
    st.divider()
    st.caption("이 앱은 개념 학습용 상대 모형입니다. 실제 반응속도, 수율 또는 실험 안전성을 예측하지 않습니다.")

if "runs" not in st.session_state:
    st.session_state.runs = 0
if run:
    st.session_state.runs += 1
    with st.spinner("분자 충돌과 반응 경로를 계산하는 중…"):
        time.sleep(0.35)

rate = relative_rate(substrate, mechanism, temperature, solvent, nucleophile)
d = SUBSTRATES[substrate]

tab1, tab2, tab3 = st.tabs(["🔬 반응 관찰", "📊 비교 분석", "📘 원리 노트"])

with tab1:
    left, right = st.columns([1.55, 1], gap="large")
    with left:
        st.subheader(f"{d['short']}의 {mechanism} 경로")
        components.html(reaction_animation(substrate, mechanism, rate), height=325)
    with right:
        st.subheader("관찰 결과")
        m1, m2 = st.columns(2)
        m1.metric("상대 반응성 지수", f"{rate:.2f}", help="절대 속도상수가 아닌 교육용 무차원 지수")
        m2.metric("예상 경향", rate_label(rate))
        st.markdown(
            f"""
            <div class="info-card">
              <h4>구조 해석</h4>
              <p><b>기질:</b> {d['formula']} ({d['degree']})</p>
              <p><b>입체장애:</b> {d['steric']} · <b>카보양이온:</b> {d['carbocation']}</p>
              <p><b>용매 효과:</b> {SOLVENTS[solvent]['label']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if mechanism == "SN2":
            st.info("SN2는 친핵체의 공격과 Br⁻ 이탈이 동시에 일어납니다. 카보양이온은 만들어지지 않습니다.")
        else:
            st.warning("SN1의 느린 단계는 Br⁻가 먼저 이탈하여 카보양이온을 만드는 단계입니다.")

with tab2:
    st.subheader("같은 조건에서 두 기질 비교")
    times = np.linspace(0, 10, 121)
    progress_data = {"정규화된 시간 지수": times}
    for name, info in SUBSTRATES.items():
        r = relative_rate(name, mechanism, temperature, solvent, nucleophile)
        # Scale time only for a readable conceptual progress curve.
        progress = 100 * (1 - np.exp(-0.26 * r * times))
        progress_data[info["short"]] = progress
    progress_df = pd.DataFrame(progress_data).set_index("정규화된 시간 지수")
    st.line_chart(
        progress_df,
        color=["#2563eb", "#f97316"],
        x_label="정규화된 시간 지수",
        y_label="모형상 반응 진행도 (%)",
        height=410,
    )

    r1 = relative_rate("1-브로모뷰테인 (1차)", mechanism, temperature, solvent, nucleophile)
    r2 = relative_rate("2-브로모뷰테인 (2차)", mechanism, temperature, solvent, nucleophile)
    winner = "1-브로모뷰테인" if r1 > r2 else "2-브로모뷰테인"
    reason = "입체장애가 더 작기 때문" if mechanism == "SN2" else "형성되는 2차 카보양이온이 1차보다 안정하기 때문"
    st.success(f"현재 모형에서는 **{winner}**이 더 빠릅니다. 핵심 이유는 {reason}입니다.")

    result_df = pd.DataFrame({
        "기질": ["1-브로모뷰테인", "2-브로모뷰테인"],
        "탄소 차수": ["1차", "2차"],
        "SN1 핵심 요인": ["1차 카보양이온이 매우 불안정", "2차 카보양이온이 상대적으로 안정"],
        "SN2 핵심 요인": ["입체장애가 작음", "입체장애가 더 큼"],
        "현재 상대 지수": [round(r1, 3), round(r2, 3)],
    })
    st.dataframe(result_df, hide_index=True, use_container_width=True)

with tab3:
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("""
        <div class="info-card">
          <h4>SN1: 카보양이온 안정성이 핵심</h4>
          <p>이탈기가 먼저 떨어지는 단계가 느린 단계입니다. 2차 카보양이온은 1차 카보양이온보다 알킬기의 유도 효과와 하이퍼컨쥬게이션으로 안정화됩니다.</p>
          <p><b>이 비교의 예상 경향:</b> 2-브로모뷰테인 &gt; 1-브로모뷰테인</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="info-card">
          <h4>SN2: 입체장애가 핵심</h4>
          <p>친핵체가 뒤쪽에서 접근하는 동시에 Br⁻가 이탈합니다. 반응 중심 주변의 알킬기가 많을수록 접근이 방해됩니다.</p>
          <p><b>이 비교의 예상 경향:</b> 1-브로모뷰테인 &gt; 2-브로모뷰테인</p>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("스스로 확인하기")
    quiz = st.radio(
        "친핵체 세기를 높였는데 SN1의 상대 지수가 변하지 않는 이유는?",
        ["친핵체가 반응에 전혀 참여하지 않아서", "속도 결정 단계에 친핵체가 참여하지 않아서", "Br이 친핵체보다 강해서"],
        index=None,
    )
    if quiz:
        if quiz == "속도 결정 단계에 친핵체가 참여하지 않아서":
            st.success("정답! SN1의 속도 결정 단계는 기질이 이온화되어 카보양이온을 형성하는 단계입니다.")
        else:
            st.error("다시 생각해 보세요. 친핵체는 이후 생성물 형성에는 참여하지만, 느린 단계에는 참여하지 않습니다.")

    with st.expander("이 모형의 한계와 올바른 해석"):
        st.markdown("""
        - 그래프와 상대 지수는 개념을 시각화하기 위한 값이며 실측 속도상수나 수율이 아닙니다.
        - 실제 반응은 기질 농도, 이탈기의 종류, 정확한 용매 조성, 온도 및 경쟁 제거 반응의 영향을 받습니다.
        - 2-브로모뷰테인은 조건에 따라 SN1·SN2뿐 아니라 E1·E2와 경쟁할 수 있습니다.
        - 이 앱의 결과만으로 실제 실험 조건이나 안전성을 결정하면 안 됩니다.
        """)

st.divider()
st.caption("교육용 모형 · 실제 화학 실험은 학교의 안전 규정과 교사의 지도에 따라 수행해야 합니다.")
