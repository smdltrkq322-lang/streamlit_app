import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd

# ==================================================
# 페이지 설정
# ==================================================
st.set_page_config(
    page_title="액침냉각 미적분 시뮬레이터",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 액침냉각유 온도 변화 시뮬레이터")
st.caption(
    "서버 발열량과 냉각유의 물성에 따른 온도 변화를 "
    "미분방정식과 오일러 방법으로 분석합니다."
)

st.latex(r"mc\frac{dT}{dt}=P-hA(T-T_a)")

st.info(
    "냉각유에 축적되는 열의 속도 = "
    "서버가 발생시키는 열의 속도 − 외부로 방출되는 열의 속도"
)

# ==================================================
# 사이드바 변수 입력
# ==================================================
st.sidebar.header("⚙️ 시뮬레이션 조건")

st.sidebar.subheader("🔥 서버 조건")

P = st.sidebar.slider(
    "서버 발열량 P (W)",
    min_value=100,
    max_value=3000,
    value=800,
    step=50,
    help="서버가 1초 동안 발생시키는 열에너지입니다."
)

st.sidebar.subheader("🛢️ 냉각유 조건")

m = st.sidebar.slider(
    "냉각유 질량 m (kg)",
    min_value=1.0,
    max_value=100.0,
    value=20.0,
    step=1.0
)

c = st.sidebar.slider(
    "냉각유 비열 c (J/kg·℃)",
    min_value=500,
    max_value=3000,
    value=1800,
    step=50
)

T0 = st.sidebar.slider(
    "냉각유 초기 온도 T₀ (℃)",
    min_value=10.0,
    max_value=50.0,
    value=25.0,
    step=1.0
)

st.sidebar.subheader("❄️ 열전달 조건")

h = st.sidebar.slider(
    "열전달계수 h (W/m²·℃)",
    min_value=5.0,
    max_value=300.0,
    value=60.0,
    step=5.0
)

A = st.sidebar.slider(
    "열전달 면적 A (m²)",
    min_value=0.1,
    max_value=10.0,
    value=2.0,
    step=0.1
)

Ta = st.sidebar.slider(
    "주변 온도 Tₐ (℃)",
    min_value=5.0,
    max_value=40.0,
    value=20.0,
    step=1.0
)

st.sidebar.subheader("⏱️ 시간 조건")

duration_min = st.sidebar.slider(
    "관찰 시간 (분)",
    min_value=5,
    max_value=240,
    value=60,
    step=5
)

dt = st.sidebar.select_slider(
    "오일러 방법의 시간 간격 Δt (초)",
    options=[1, 2, 5, 10, 20, 30, 60],
    value=10,
    help="간격이 작을수록 오일러 근삿값이 정확해집니다."
)

st.sidebar.subheader("♻️ 폐열 회수 조건")

recovery_temp = st.sidebar.slider(
    "폐열 회수 시작 온도 (℃)",
    min_value=20.0,
    max_value=80.0,
    value=35.0,
    step=1.0
)

efficiency = st.sidebar.slider(
    "폐열 회수 효율 (%)",
    min_value=10,
    max_value=100,
    value=70,
    step=5
) / 100

safe_temp = st.sidebar.slider(
    "비교용 안전 온도 기준 (℃)",
    min_value=30.0,
    max_value=100.0,
    value=60.0,
    step=1.0
)

# ==================================================
# 미분방정식 계산
# ==================================================
duration_sec = duration_min * 60
time = np.arange(0, duration_sec + dt, dt)

# hA: 전체 열전달 능력
hA = h * A

# 정상상태 온도
T_inf = Ta + P / hA

# 시간상수
tau = m * c / hA

# 해석적으로 구한 온도 함수
T_exact = (
    T_inf
    + (T0 - T_inf) * np.exp(-time / tau)
)

# 오일러 방법
T_euler = np.zeros(len(time))
T_euler[0] = T0

for i in range(len(time) - 1):
    rate = (
        P - hA * (T_euler[i] - Ta)
    ) / (m * c)

    T_euler[i + 1] = T_euler[i] + dt * rate

# 순간 온도변화율
temperature_rate = (
    P - hA * (T_exact - Ta)
) / (m * c)

# 외부로 전달되는 열의 세기
heat_release_power = hA * (T_exact - Ta)

# 외부로 열이 빠져나갈 때만 양수로 처리
positive_heat_power = np.maximum(
    heat_release_power,
    0
)

# 폐열 회수 기준 온도 이상인지 확인
recovery_mask = T_exact >= recovery_temp

# 실제 회수 전력
recovery_power = np.where(
    recovery_mask,
    efficiency * positive_heat_power,
    0
)

# 누적 회수 에너지
cumulative_energy_j = np.zeros(len(time))

for i in range(1, len(time)):
    average_power = (
        recovery_power[i - 1]
        + recovery_power[i]
    ) / 2

    cumulative_energy_j[i] = (
        cumulative_energy_j[i - 1]
        + average_power * dt
    )

cumulative_energy_kwh = (
    cumulative_energy_j / 3_600_000
)

# 해석해와 오일러 방법 사이의 오차
absolute_error = np.abs(T_exact - T_euler)
max_error = np.max(absolute_error)

# 초기 온도변화율
initial_rate = (
    P - hA * (T0 - Ta)
) / (m * c)

# 폐열 회수 시작 시점
recovery_indices = np.where(recovery_mask)[0]

if len(recovery_indices) > 0:
    recovery_start_min = (
        time[recovery_indices[0]] / 60
    )
else:
    recovery_start_min = None

# 안전 온도 도달 시점
safe_indices = np.where(T_exact >= safe_temp)[0]

if len(safe_indices) > 0:
    safe_time_min = time[safe_indices[0]] / 60
else:
    safe_time_min = None

# 현재 온도
current_temp = T_exact[-1]

# ==================================================
# 핵심 결과
# ==================================================
st.subheader("📌 핵심 결과")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "정상상태 온도",
    f"{T_inf:.2f} ℃"
)

col2.metric(
    "관찰 종료 온도",
    f"{current_temp:.2f} ℃"
)

col3.metric(
    "시간상수",
    f"{tau / 60:.2f}분"
)

col4.metric(
    "누적 회수 에너지",
    f"{cumulative_energy_kwh[-1]:.4f} kWh"
)

# ==================================================
# 탱크 상태 설정
# ==================================================
if current_temp < recovery_temp:
    oil_color_top = "#5CCBFF"
    oil_color_bottom = "#167BD8"
    status_color = "#1D77C3"
    status_text = "온도 상승 중"
elif current_temp < safe_temp:
    oil_color_top = "#FFD166"
    oil_color_bottom = "#F39C12"
    status_color = "#D88400"
    status_text = "폐열 회수 가능"
else:
    oil_color_top = "#FF7B7B"
    oil_color_bottom = "#D93636"
    status_color = "#C62828"
    status_text = "안전 온도 확인 필요"

# 온도계 높이 계산
minimum_display_temp = 0
maximum_display_temp = 100

thermometer_height = np.clip(
    (current_temp - minimum_display_temp)
    / (maximum_display_temp - minimum_display_temp)
    * 180,
    0,
    180
)

thermometer_y = 245 - thermometer_height

# ==================================================
# SVG 액침냉각 탱크
# ==================================================
st.subheader("👀 액침냉각 탱크 시각화")

visual_col1, visual_col2 = st.columns([1.3, 1])

with visual_col1:
    tank_html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
    body {{
        margin: 0;
        background: transparent;
        font-family: Arial, sans-serif;
    }}

    .container {{
        background: linear-gradient(145deg, #f8fbff, #eef3f8);
        border: 1px solid #d8e0e8;
        border-radius: 20px;
        padding: 15px;
        text-align: center;
    }}

    .title {{
        font-size: 21px;
        font-weight: bold;
        color: #25364a;
        margin-bottom: 5px;
    }}

    .subtitle {{
        font-size: 14px;
        color: #66788a;
        margin-bottom: 5px;
    }}

    .status {{
        display: inline-block;
        margin-top: 5px;
        padding: 8px 18px;
        border-radius: 20px;
        color: white;
        background: {status_color};
        font-weight: bold;
    }}

    .heat-arrow {{
        animation: moveUp 1.5s infinite;
    }}

    .heat-arrow-delay {{
        animation: moveUp 1.5s infinite;
        animation-delay: 0.7s;
    }}

    .bubble {{
        animation: bubbleUp 2.2s infinite;
        opacity: 0.7;
    }}

    .bubble-delay {{
        animation: bubbleUp 2.2s infinite;
        animation-delay: 1.1s;
        opacity: 0.7;
    }}

    @keyframes moveUp {{
        0% {{
            transform: translateY(12px);
            opacity: 0.2;
        }}
        50% {{
            opacity: 1;
        }}
        100% {{
            transform: translateY(-15px);
            opacity: 0.2;
        }}
    }}

    @keyframes bubbleUp {{
        0% {{
            transform: translateY(20px);
            opacity: 0;
        }}
        40% {{
            opacity: 0.8;
        }}
        100% {{
            transform: translateY(-70px);
            opacity: 0;
        }}
    }}
</style>
</head>

<body>
<div class="container">
    <div class="title">액침냉각 장치 모형</div>
    <div class="subtitle">
        서버가 절연성 냉각유에 잠겨 있는 모습을 단순화함
    </div>

    <svg
        width="100%"
        height="380"
        viewBox="0 0 650 380"
        xmlns="http://www.w3.org/2000/svg"
    >
        <defs>
            <linearGradient
                id="oilGradient"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
            >
                <stop
                    offset="0%"
                    stop-color="{oil_color_top}"
                    stop-opacity="0.78"
                />
                <stop
                    offset="100%"
                    stop-color="{oil_color_bottom}"
                    stop-opacity="0.92"
                />
            </linearGradient>

            <linearGradient
                id="serverGradient"
                x1="0"
                y1="0"
                x2="1"
                y2="1"
            >
                <stop
                    offset="0%"
                    stop-color="#485767"
                />
                <stop
                    offset="100%"
                    stop-color="#202a35"
                />
            </linearGradient>

            <filter id="shadow">
                <feDropShadow
                    dx="0"
                    dy="4"
                    stdDeviation="5"
                    flood-opacity="0.25"
                />
            </filter>
        </defs>

        <!-- 탱크 뚜껑 -->
        <rect
            x="80"
            y="40"
            width="420"
            height="25"
            rx="10"
            fill="#354657"
        />

        <!-- 탱크 외벽 -->
        <rect
            x="95"
            y="60"
            width="390"
            height="275"
            rx="20"
            fill="white"
            stroke="#354657"
            stroke-width="8"
            filter="url(#shadow)"
        />

        <!-- 냉각유 -->
        <path
            d="
                M103 105
                Q145 92 190 105
                T280 105
                T370 105
                T477 105
                L477 310
                Q477 327 460 327
                L120 327
                Q103 327 103 310
                Z
            "
            fill="url(#oilGradient)"
        />

        <!-- 냉각유 표면 -->
        <path
            d="
                M103 105
                Q145 92 190 105
                T280 105
                T370 105
                T477 105
            "
            fill="none"
            stroke="white"
            stroke-width="4"
            opacity="0.75"
        />

        <!-- 서버 본체 -->
        <rect
            x="210"
            y="145"
            width="160"
            height="155"
            rx="12"
            fill="url(#serverGradient)"
            stroke="#15202b"
            stroke-width="4"
            filter="url(#shadow)"
        />

        <!-- 서버 제목 -->
        <text
            x="290"
            y="172"
            fill="white"
            font-size="17"
            font-weight="bold"
            text-anchor="middle"
        >
            SERVER
        </text>

        <!-- 서버 내부 부품 -->
        <rect
            x="235"
            y="190"
            width="110"
            height="18"
            rx="5"
            fill="#52df91"
        />

        <rect
            x="235"
            y="222"
            width="110"
            height="18"
            rx="5"
            fill="#52df91"
        />

        <rect
            x="235"
            y="254"
            width="110"
            height="18"
            rx="5"
            fill="#52df91"
        />

        <!-- 서버 열 발생 표시 -->
        <g class="heat-arrow">
            <path
                d="M190 230 L170 200 L150 230"
                fill="none"
                stroke="#ff4d4d"
                stroke-width="8"
                stroke-linecap="round"
                stroke-linejoin="round"
            />
        </g>

        <g class="heat-arrow-delay">
            <path
                d="M430 230 L410 200 L390 230"
                fill="none"
                stroke="#ff4d4d"
                stroke-width="8"
                stroke-linecap="round"
                stroke-linejoin="round"
            />
        </g>

        <!-- 냉각유 순환 화살표 -->
        <path
            d="M150 285 C115 230 120 160 170 130"
            fill="none"
            stroke="white"
            stroke-width="5"
            stroke-dasharray="10 8"
            opacity="0.85"
        />

        <polygon
            points="168,122 174,143 151,137"
            fill="white"
            opacity="0.85"
        />

        <path
            d="M430 130 C480 160 485 230 445 285"
            fill="none"
            stroke="white"
            stroke-width="5"
            stroke-dasharray="10 8"
            opacity="0.85"
        />

        <polygon
            points="447,294 426,284 445,270"
            fill="white"
            opacity="0.85"
        />

        <!-- 움직이는 기포 -->
        <circle
            class="bubble"
            cx="180"
            cy="270"
            r="8"
            fill="white"
        />

        <circle
            class="bubble-delay"
            cx="405"
            cy="265"
            r="6"
            fill="white"
        />

        <!-- 열교환기 -->
        <rect
            x="525"
            y="115"
            width="75"
            height="145"
            rx="12"
            fill="#dce8f2"
            stroke="#53687c"
            stroke-width="4"
        />

        <text
            x="562"
            y="142"
            fill="#31475b"
            font-size="14"
            font-weight="bold"
            text-anchor="middle"
        >
            열교환기
        </text>

        <path
            d="
                M545 165
                C585 175 540 190 580 200
                C540 210 585 225 545 235
            "
            fill="none"
            stroke="#2585d8"
            stroke-width="6"
        />

        <!-- 탱크와 열교환기 연결 -->
        <path
            d="M485 155 L525 155"
            stroke="#53687c"
            stroke-width="8"
        />

        <path
            d="M485 245 L525 245"
            stroke="#53687c"
            stroke-width="8"
        />

        <!-- 온도계 -->
        <rect
            x="35"
            y="65"
            width="24"
            height="200"
            rx="12"
            fill="#f1f4f8"
            stroke="#5d6b78"
            stroke-width="3"
        />

        <rect
            x="41"
            y="{thermometer_y:.1f}"
            width="12"
            height="{thermometer_height:.1f}"
            rx="6"
            fill="{status_color}"
        />

        <circle
            cx="47"
            cy="270"
            r="22"
            fill="{status_color}"
            stroke="#5d6b78"
            stroke-width="3"
        />

        <text
            x="47"
            y="315"
            fill="#25364a"
            font-size="16"
            font-weight="bold"
            text-anchor="middle"
        >
            {current_temp:.1f}℃
        </text>

        <!-- 설명 -->
        <text
            x="290"
            y="360"
            fill="#33485c"
            font-size="15"
            text-anchor="middle"
        >
            붉은 화살표: 서버에서 발생하는 열
            / 흰색 점선: 냉각유의 순환
        </text>
    </svg>

    <div class="status">
        {status_text}
    </div>
</div>
</body>
</html>
"""

    components.html(
        tank_html,
        height=470,
        scrolling=False
    )

with visual_col2:
    st.markdown("#### 에너지 이동 과정")

    st.success(
        f"① 서버에서 매초 약 {P:,.0f}J의 "
        "열에너지가 발생합니다."
    )

    st.markdown("### ↓")

    st.info(
        f"② 냉각유가 열을 흡수합니다. "
        f"초기 온도변화율은 "
        f"{initial_rate * 60:.3f}℃/분입니다."
    )

    st.markdown("### ↓")

    st.warning(
        f"③ 관찰 종료 시 외부로 전달되는 열의 세기는 "
        f"{heat_release_power[-1]:,.1f}W입니다."
    )

    st.markdown("### ↓")

    st.success(
        f"④ 회수 가능한 누적 에너지는 약 "
        f"{cumulative_energy_kwh[-1]:.4f}kWh입니다."
    )

# ==================================================
# 온도 그래프
# ==================================================
st.subheader("📈 시간에 따른 냉각유 온도")

temperature_df = pd.DataFrame({
    "시간(분)": time / 60,
    "해석적으로 구한 온도": T_exact,
    "오일러 방법으로 구한 온도": T_euler,
    "폐열 회수 기준": np.full(
        len(time),
        recovery_temp
    ),
    "안전 온도 기준": np.full(
        len(time),
        safe_temp
    )
}).set_index("시간(분)")

st.line_chart(temperature_df)

st.write(
    f"해석적으로 구한 온도와 오일러 방법의 근삿값 사이의 "
    f"최대 오차는 **{max_error:.6f}℃**입니다."
)

# ==================================================
# 순간변화율 그래프
# ==================================================
st.subheader("📉 온도의 순간변화율")

rate_df = pd.DataFrame({
    "시간(분)": time / 60,
    "온도변화율(℃/분)": temperature_rate * 60
}).set_index("시간(분)")

st.line_chart(rate_df)

st.write(
    "냉각유 온도가 상승할수록 주변과의 온도 차가 커져 "
    "외부로 방출되는 열이 증가합니다. 따라서 온도변화율은 "
    "시간이 지날수록 0에 가까워집니다."
)

# ==================================================
# 폐열 회수 그래프
# ==================================================
st.subheader("♻️ 누적 폐열 회수 에너지")

energy_df = pd.DataFrame({
    "시간(분)": time / 60,
    "누적 회수 에너지(kWh)": cumulative_energy_kwh
}).set_index("시간(분)")

st.line_chart(energy_df)

if recovery_start_min is None:
    st.warning(
        f"관찰 시간 동안 냉각유가 폐열 회수 기준인 "
        f"{recovery_temp:.1f}℃에 도달하지 않았습니다."
    )
else:
    st.success(
        f"약 {recovery_start_min:.2f}분 후 냉각유가 "
        f"{recovery_temp:.1f}℃에 도달하여 폐열 회수를 "
        "시작할 수 있습니다."
    )

if safe_time_min is None:
    st.success(
        f"관찰 시간 동안 설정한 안전 온도 "
        f"{safe_temp:.1f}℃에 도달하지 않았습니다."
    )
else:
    st.error(
        f"약 {safe_time_min:.2f}분 후 설정한 안전 온도 "
        f"{safe_temp:.1f}℃에 도달합니다."
    )

# ==================================================
# 결과 해석
# ==================================================
st.subheader("🔎 현재 조건 해석")

if initial_rate > 0:
    initial_state = "상승"
elif initial_rate < 0:
    initial_state = "하강"
else:
    initial_state = "일정하게 유지"

st.markdown(
    f"""
- 초기 냉각유 온도는 **{T0:.1f}℃**이고 처음에는 온도가
  **{initial_state}**합니다.
- 초기 온도변화율은 **{initial_rate * 60:.3f}℃/분**입니다.
- 냉각유 온도는 장기적으로 **{T_inf:.2f}℃**에 수렴합니다.
- 시간상수는 **{tau / 60:.2f}분**입니다.
- 냉각유의 질량이나 비열을 높이면 온도 변화가 느려집니다.
- 열전달계수나 열전달 면적을 높이면 정상상태 온도가 낮아집니다.
"""
)

# ==================================================
# 시간별 결과
# ==================================================
with st.expander("📋 시간별 계산 결과 확인"):
    result_df = pd.DataFrame({
        "시간(분)": np.round(time / 60, 2),
        "해석해 온도(℃)": np.round(T_exact, 3),
        "오일러 온도(℃)": np.round(T_euler, 3),
        "온도변화율(℃/분)": np.round(
            temperature_rate * 60,
            5
        ),
        "외부 열전달률(W)": np.round(
            heat_release_power,
            2
        ),
        "누적 회수 에너지(kWh)": np.round(
            cumulative_energy_kwh,
            6
        )
    })

    st.dataframe(
        result_df,
        use_container_width=True
    )

# ==================================================
# 공식 설명
# ==================================================
with st.expander("🧮 사용된 미적분 공식"):
    st.markdown("#### 1. 에너지수지식")
    st.latex(
        r"mc\frac{dT}{dt}=P-hA(T-T_a)"
    )

    st.markdown("#### 2. 순간 온도변화율")
    st.latex(
        r"\frac{dT}{dt}"
        r"=\frac{P-hA(T-T_a)}{mc}"
    )

    st.markdown("#### 3. 정상상태 온도")
    st.latex(
        r"T_{\infty}=T_a+\frac{P}{hA}"
    )

    st.markdown("#### 4. 시간에 따른 온도")
    st.latex(
        r"T(t)=T_{\infty}"
        r"+(T_0-T_{\infty})"
        r"e^{-\frac{hA}{mc}t}"
    )

    st.markdown("#### 5. 오일러 방법")
    st.latex(
        r"T_{n+1}=T_n+\Delta t"
        r"\left("
        r"\frac{P-hA(T_n-T_a)}{mc}"
        r"\right)"
    )

    st.markdown("#### 6. 누적 폐열 회수량")
    st.latex(
        r"Q=\int_{t_1}^{t_2}"
        r"\eta hA(T(t)-T_a)\,dt"
    )

# ==================================================
# 가정과 한계
# ==================================================
with st.expander("⚠️ 시뮬레이션의 가정과 한계"):
    st.markdown(
        """
- 냉각유 전체의 온도가 균일하다고 가정했습니다.
- 서버 발열량이 시간에 따라 일정하다고 가정했습니다.
- 비열과 열전달계수가 온도에 따라 변하지 않는다고 가정했습니다.
- 펌프의 전력 소비와 냉각유의 실제 유동은 반영하지 않았습니다.
- 회수 효율은 일정하다고 가정했습니다.
- 안전 온도는 실제 장비의 공식 허용온도가 아니라 사용자가
  비교를 위해 설정한 기준입니다.
"""
    )
