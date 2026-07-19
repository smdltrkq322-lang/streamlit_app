import math
import random
from dataclasses import dataclass

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="SN1·SN2 반응 실험실",
    page_icon="🧪",
    layout="wide",
)

st.markdown(
    """
<style>
html, body, [class*="css"] {
    font-family: sans-serif;
}

.stApp {
    background: linear-gradient(
        145deg,
        #f4f9ff 0%,
        #fbfdff 48%,
        #f8f5ff 100%
    );
}

.hero {
    padding: 1.5rem 1.8rem;
    border-radius: 24px;
    color: white;
    background: linear-gradient(
        120deg,
        #173b66,
        #3d6997 58%,
        #7158a6
    );
    box-shadow: 0 16px 40px #173b6626;
    margin-bottom: 1rem;
}

.hero h1 {
    margin: 0;
    font-size: 2.2rem;
}

.hero p {
    margin: 0.45rem 0 0;
    color: #e7f2ff;
}

.lab-card {
    background: #ffffff;
    border: 1px solid #dfe9f3;
    border-radius: 20px;
    padding: 1rem 1.15rem;
    box-shadow: 0 8px 25px #173b6612;
    margin-bottom: 0.8rem;
}

.tag {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    border-radius: 999px;
    background: #e7f1ff;
    color: #244f7d;
    font-weight: 700;
    margin: 0.12rem;
}

.reaction {
    font-size: 1.08rem;
    text-align: center;
    background: #f2f6fb;
    border-radius: 14px;
    padding: 0.8rem;
    margin: 0.6rem 0;
    font-weight: 700;
}

.notice {
    border-left: 5px solid #f3ad35;
    background: #fff7e6;
    padding: 0.75rem 1rem;
    border-radius: 10px;
    color: #5c431c;
}

.result-box {
    background: #ebf8f3;
    border: 1px solid #a6ddc7;
    border-radius: 14px;
    padding: 0.8rem 1rem;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e1eaf3;
    border-radius: 16px;
    padding: 0.8rem;
}
</style>
""",
    unsafe_allow_html=True,
)


@dataclass(frozen=True)
class Substrate:
    name: str
    kind: str
    condensed: str
    sn1_factor: float
    sn2_factor: float
    steric: str
    carbocation: str


SUBSTRATES = {
    "1-브로모뷰테인": Substrate(
        name="1-브로모뷰테인",
        kind="1차",
        condensed="CH₃–CH₂–CH₂–CH₂–Br",
        sn1_factor=0.08,
        sn2_factor=1.00,
        steric="작음",
        carbocation="1차 카보양이온: 매우 불안정",
    ),
    "2-브로모뷰테인": Substrate(
        name="2-브로모뷰테인",
        kind="2차",
        condensed="CH₃–CH(Br)–CH₂–CH₃",
        sn1_factor=0.48,
        sn2_factor=0.45,
        steric="중간",
        carbocation="2차 카보양이온: 1차보다 안정",
    ),
}


def calculate_progress(
    mechanism,
    substrate,
    seconds,
    temperature,
):
    """
    실제 속도상수가 아니라 반응 경향을 보여 주기 위한 교육용 모형
    """

    if mechanism == "SN1":
        base_factor = substrate.sn1_factor
    else:
        base_factor = substrate.sn2_factor

    temperature_factor = 1.6 ** ((temperature - 25) / 10)

    time_constant = 115 / max(
        base_factor * temperature_factor,
        0.02,
    )

    progress = 1 - math.exp(-seconds / time_constant)

    return min(1.0, progress)


def create_test_tube_svg(
    progress,
    mechanism,
    seed,
):
    """시험관, 용액, 침전 입자를 SVG로 표현한다."""

    rng = random.Random(seed)

    if mechanism == "SN1":
        precipitate_color = "#f7efc4"
        liquid_color = "#e5f0fb"
        precipitate_name = "AgBr(s)"
    else:
        precipitate_color = "#f4f5f7"
        liquid_color = "#ebe6fb"
        precipitate_name = "NaBr(s)"

    particle_count = int(progress * 48)
    particle_svg = []

    for _ in range(particle_count):
        x = rng.uniform(72, 188)
        y = rng.uniform(166, 298)
        radius = rng.uniform(2.2, 5.2)
        opacity = rng.uniform(0.55, 0.95)

        particle_svg.append(
            f"""
            <circle
                cx="{x:.1f}"
                cy="{y:.1f}"
                r="{radius:.1f}"
                fill="{precipitate_color}"
                opacity="{opacity:.2f}"
            />
            """
        )

    bed_height = 4 + progress * 32
    bed_opacity = 0.35 + progress * 0.65

    return f"""
    <svg
        viewBox="0 0 260 390"
        width="100%"
        role="img"
        aria-label="{mechanism} 반응 시험관"
    >
        <defs>
            <linearGradient id="glass" x1="0" x2="1">
                <stop
                    offset="0"
                    stop-color="#ffffff"
                    stop-opacity="0.8"
                />
                <stop
                    offset="0.5"
                    stop-color="#d8e8f4"
                    stop-opacity="0.18"
                />
                <stop
                    offset="1"
                    stop-color="#ffffff"
                    stop-opacity="0.72"
                />
            </linearGradient>
        </defs>

        <!-- 시험관대 -->
        <rect
            x="25"
            y="340"
            width="210"
            height="20"
            rx="10"
            fill="#b7c8d8"
        />

        <!-- 시험관 그림자 -->
        <rect
            x="48"
            y="75"
            width="164"
            height="270"
            rx="28"
            fill="#dce7ef"
            opacity="0.25"
        />

        <!-- 시험관 본체 -->
        <path
            d="
                M68 48
                L68 280
                Q68 340 130 340
                Q192 340 192 280
                L192 48
            "
            fill="url(#glass)"
            stroke="#7b9ab3"
            stroke-width="6"
        />

        <!-- 용액 -->
        <path
            d="
                M72 150
                L188 150
                L188 282
                Q188 332 130 332
                Q72 332 72 282
                Z
            "
            fill="{liquid_color}"
            opacity="0.9"
        />

        <!-- 용액 표면 -->
        <ellipse
            cx="130"
            cy="150"
            rx="58"
            ry="9"
            fill="#cbdced"
        />

        <!-- 침전 입자 -->
        {''.join(particle_svg)}

        <!-- 바닥에 쌓인 침전 -->
        <path
            d="
                M78 {326 - bed_height:.1f}
                Q130 {318 - bed_height:.1f}
                182 {326 - bed_height:.1f}
                L180 323
                Q130 338 80 323
                Z
            "
            fill="{precipitate_color}"
            opacity="{bed_opacity:.2f}"
        />

        <!-- 시험관 입구 -->
        <rect
            x="43"
            y="34"
            width="174"
            height="24"
            rx="10"
            fill="#e9f1f6"
            stroke="#7b9ab3"
            stroke-width="4"
        />

        <text
            x="130"
            y="375"
            text-anchor="middle"
            font-family="sans-serif"
            font-size="17"
            font-weight="700"
            fill="#24435f"
        >
            {precipitate_name} 침전 · {progress * 100:.0f}%
        </text>
    </svg>
    """


def get_mechanism_steps(
    mechanism,
    substrate,
):
    if mechanism == "SN1":
        return [
            (
                "① 이온화",
                f"{substrate.condensed}에서 Br⁻가 먼저 이탈한다.",
            ),
            (
                "② 카보양이온 형성",
                f"{substrate.carbocation} 중간체가 만들어진다.",
            ),
            (
                "③ 친핵체의 공격",
                "에탄올이 카보양이온을 공격하고 "
                "이탈한 Br⁻는 AgBr 침전을 만든다.",
            ),
        ]

    return [
        (
            "① 뒷면 공격",
            f"I⁻가 C–Br 결합의 반대편에서 접근한다. "
            f"현재 기질의 입체장애는 {substrate.steric}이다.",
        ),
        (
            "② 한 단계 전이상태",
            "C–I 결합 형성과 C–Br 결합 절단이 동시에 진행된다.",
        ),
        (
            "③ 생성물 형성",
            "아이오도뷰테인과 NaBr 침전이 생성된다.",
        ),
    ]


st.markdown(
    """
<div class="hero">
    <h1>🧪 SN1·SN2 반응 실험실</h1>
    <p>
        1-브로모뷰테인과 2-브로모뷰테인의 구조가
        반응 경로와 침전 생성에 미치는 영향을 비교해 보세요.
    </p>
</div>
""",
    unsafe_allow_html=True,
)


with st.sidebar:
    st.header("🎛️ 실험 제어판")

    mechanism = st.radio(
        "반응 조건",
        ["SN2", "SN1"],
        horizontal=True,
    )

    substrate_name = st.selectbox(
        "할로알케인",
        list(SUBSTRATES.keys()),
    )

    seconds = st.slider(
        "반응 경과 시간",
        min_value=0,
        max_value=300,
        value=60,
        step=5,
        format="%d초",
    )

    temperature = st.slider(
        "모형 온도",
        min_value=20,
        max_value=50,
        value=25,
        step=5,
        format="%d℃",
    )

    show_particles = st.toggle(
        "침전 입자 표시",
        value=True,
    )

    st.divider()

    st.caption(
        "앱에 표시되는 시간과 진행률은 개념 비교를 위한 "
        "상대적 모형입니다. 실제 반응속도상수가 아닙니다."
    )


substrate = SUBSTRATES[substrate_name]

progress = calculate_progress(
    mechanism,
    substrate,
    seconds,
    temperature,
)


tab_experiment, tab_process, tab_graph, tab_record = st.tabs(
    [
        "🔬 가상 실험",
        "⚛️ 반응 과정",
        "📊 두 기질 비교",
        "📝 탐구 기록",
    ]
)


with tab_experiment:
    left, center, right = st.columns(
        [1.05, 1.2, 1.15]
    )

    with left:
        st.markdown(
            '<div class="lab-card">',
            unsafe_allow_html=True,
        )

        st.subheader("실험대 위 도구")

        st.write("🧪 시험관과 시험관대")
        st.write("💧 전용 스포이트")
        st.write("⏱️ 초시계")
        st.write("⬜ 흰색 관찰 배경")
        st.write("🥽 보안경과 실험복")

        if mechanism == "SN1":
            reagent = "질산은–에탄올 시험 용액"
        else:
            reagent = "아이오딘화나트륨–아세톤 시험 용액"

        st.markdown(
            f"""
            <span class="tag">{substrate.kind} 기질</span>
            <span class="tag">{reagent}</span>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="notice">
                실제 실험은 교사의 감독, 흄후드,
                적절한 보호구 및 폐액 처리 조건에서 진행해야 합니다.
                이 앱은 개념 학습용 시뮬레이터입니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with center:
        if show_particles:
            displayed_progress = progress
        else:
            displayed_progress = 0

        seed = 101 if substrate_name == "1-브로모뷰테인" else 202

        if mechanism == "SN1":
            seed += 10

        st.markdown(
            create_test_tube_svg(
                displayed_progress,
                mechanism,
                seed,
            ),
            unsafe_allow_html=True,
        )

        if progress >= 0.65:
            observed_state = "뚜렷한 침전이 관찰됨"
        elif progress >= 0.25:
            observed_state = "용액의 혼탁이 증가함"
        else:
            observed_state = "겉보기 변화가 아직 작음"

        st.markdown(
            f"""
            <div class="result-box">
                <b>현재 관찰</b><br>
                {observed_state}<br><br>
                <b>사용 용액</b><br>
                {reagent}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.subheader("반응물 → 생성물")

        if mechanism == "SN1":
            if substrate_name == "1-브로모뷰테인":
                organic_product = "1-에톡시뷰테인"
            else:
                organic_product = "2-에톡시뷰테인"

            product = f"{organic_product} + AgBr(s)"
            precipitate = "AgBr"
            precipitate_color_name = "연한 크림색"
        else:
            if substrate_name == "1-브로모뷰테인":
                organic_product = "1-아이오도뷰테인"
            else:
                organic_product = "2-아이오도뷰테인"

            product = f"{organic_product} + NaBr(s)"
            precipitate = "NaBr"
            precipitate_color_name = "흰색"

        st.markdown(
            f"""
            <div class="reaction">
                {substrate.condensed}
                <br>
                ＋
                <br>
                {reagent}
                <br><br>
                ↓
                <br><br>
                {product}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.metric(
            "모형 반응 진행률",
            f"{progress * 100:.0f}%",
        )

        st.metric(
            "침전",
            f"{precipitate_color_name} {precipitate}",
        )

        st.info(
            "침전이 빨리 보인다는 것은 이 시험 조건에서 "
            "반응이 상대적으로 빠르다는 정성적 단서입니다. "
            "절대적인 반응속도상수를 의미하지는 않습니다."
        )


with tab_process:
    st.subheader(
        f"{mechanism} 메커니즘을 단계별로 보기"
    )

    step_columns = st.columns(3)

    steps = get_mechanism_steps(
        mechanism,
        substrate,
    )

    for column, step in zip(step_columns, steps):
        title, description = step

        with column:
            st.markdown(
                f"""
                <div class="lab-card">
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if mechanism == "SN1":
        st.latex(
            r"v_{\mathrm{SN1}}=k[\mathrm{RBr}]"
        )

        st.write(
            "SN1에서는 C–Br 결합이 먼저 끊어지므로 "
            "형성되는 카보양이온의 안정성이 중요합니다. "
            "따라서 2차 기질이 1차 기질보다 유리합니다."
        )

        st.warning(
            "AgBr 침전은 Br⁻가 이탈했다는 간접적인 증거입니다. "
            "침전만으로 모든 유기 생성물의 종류와 비율을 "
            "확정할 수는 없습니다."
        )

    else:
        st.latex(
            r"v_{\mathrm{SN2}}"
            r"=k[\mathrm{RBr}][\mathrm{I^-}]"
        )

        st.write(
            "SN2에서는 친핵체의 접근과 이탈기의 이탈이 "
            "동시에 일어나므로 반응 탄소 주변의 입체장애가 "
            "중요합니다. 따라서 1차 기질이 2차 기질보다 "
            "유리합니다."
        )

        st.warning(
            "SN2 반응에는 카보양이온 중간체가 없습니다. "
            "따라서 SN2 속도를 카보양이온 안정성으로 "
            "설명하면 안 됩니다."
        )


with tab_graph:
    st.subheader(
        f"{mechanism} 조건에서 두 기질의 상대적 진행 비교"
    )

    time_values = list(range(0, 301, 10))
    graph_rows = []

    for name, current_substrate in SUBSTRATES.items():
        for time_value in time_values:
            current_progress = calculate_progress(
                mechanism,
                current_substrate,
                time_value,
                temperature,
            )

            graph_rows.append(
                {
                    "시간(초)": time_value,
                    "진행률(%)": current_progress * 100,
                    "기질": name,
                }
            )

    graph_data = pd.DataFrame(graph_rows)

    figure = px.line(
        graph_data,
        x="시간(초)",
        y="진행률(%)",
        color="기질",
        range_y=[0, 105],
        color_discrete_map={
            "1-브로모뷰테인": "#397bb5",
            "2-브로모뷰테인": "#8b5bb5",
        },
    )

    figure.update_layout(
        height=420,
        legend_title_text="",
        hovermode="x unified",
        margin={
            "l": 10,
            "r": 10,
            "t": 25,
            "b": 10,
        },
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )

    if mechanism == "SN1":
        faster_substrate = "2-브로모뷰테인"
        reason = (
            "2차 카보양이온이 1차 카보양이온보다 "
            "상대적으로 안정하기 때문입니다."
        )
    else:
        faster_substrate = "1-브로모뷰테인"
        reason = (
            "반응 탄소 주변의 입체장애가 더 작아 "
            "I⁻의 뒷면 공격이 쉽기 때문입니다."
        )

    st.success(
        f"예상 경향: **{faster_substrate}**이 더 빠릅니다. "
        f"{reason}"
    )

    st.caption(
        "그래프의 곡선은 알려진 정성적 경향을 "
        "직관적으로 비교하기 위한 교육용 모형이며 "
        "실제 실험 데이터가 아닙니다."
    )


with tab_record:
    st.subheader("실제 실험 관찰 기록표")

    record_template = pd.DataFrame(
        {
            "조건": [
                "NaI–아세톤",
                "NaI–아세톤",
                "AgNO₃–에탄올",
                "AgNO₃–에탄올",
            ],
            "기질": [
                "1-브로모뷰테인",
                "2-브로모뷰테인",
                "1-브로모뷰테인",
                "2-브로모뷰테인",
            ],
            "1회(초)": [None, None, None, None],
            "2회(초)": [None, None, None, None],
            "3회(초)": [None, None, None, None],
            "관찰 내용": ["", "", "", ""],
        }
    )

    edited_record = st.data_editor(
        record_template,
        use_container_width=True,
        num_rows="fixed",
    )

    csv_data = edited_record.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="기록표 CSV 내려받기",
        data=csv_data,
        file_name="SN1_SN2_관찰기록.csv",
        mime="text/csv",
    )

    with st.expander("결과를 해석할 때 확인할 점"):
        st.markdown(
            """
- 침전이 보이기까지의 시간은 용액의 수분, 온도, 혼합 상태와 용해도의 영향도 받습니다.
- SN1 조건의 침전은 Br⁻의 이탈을 보여 주는 간접적인 지표입니다.
- 침전만으로 모든 유기 생성물의 종류와 비율을 확정할 수는 없습니다.
- SN2에는 카보양이온 중간체가 없으므로 카보양이온 안정성으로 SN2 속도를 설명하면 안 됩니다.
- 1차와 2차 기질만 비교하므로 실제 실험에서는 예상보다 차이가 작게 나타날 수 있습니다.
- 관찰 시간 안에 변화가 없으면 임의의 시간을 기록하지 말고 ‘관찰되지 않음’이라고 기록해야 합니다.
"""
        )


st.divider()

st.caption(
    "교육용 가상 실험입니다. 실제 실험 전에는 담당 교사의 "
    "위험성 평가와 학교 실험실 안전 지침을 따라야 합니다."
)
