import streamlit as st
import numpy as np
import pandas as pd

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="액침냉각 온도 변화 시뮬레이터",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 액침냉각유 온도 변화 시뮬레이터")
st.caption(
    "서버 발열량과 냉각유의 물성에 따른 온도 변화를 "
    "미분방정식과 오일러 방법으로 분석합니다."
)

st.latex(
    r"mc\frac{dT}{dt}=P-hA(T-T_a)"
)

st.info(
    "냉각유에 축적되는 열의 속도 = "
    "서버가 발생시키는 열의 속도 − 외부로 방출되는 열의 속도"
)

# --------------------------------------------------
# 사이드바: 변수 입력
# --------------------------------------------------
st.sidebar.header("⚙️ 조건 설정")

st.sidebar.subheader("서버 조건")

P = st.sidebar.slider(
    "서버 발열량 P (W)",
    min_value=100,
    max_value=3000,
    value=800,
    step=50,
    help="서버가 1초 동안 발생시키는 열에너지입니다."
)

st.sidebar.subheader("냉각유 조건")

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

st.sidebar.subheader("열전달 조건")

h = st.sidebar.slider(
    "열전달계수 h (W/m²·℃)",
    min_value=5.0,
    max_value=300.0,
    value=60.0,
    step=5.0,
    help="값이 클수록 냉각유에서 외부로 열이 잘 이동합니다."
)

A = st.sidebar.slider(
    "열전달 면적 A (m²)",
    min_value=0.1,
    max_value=10.0,
    value=2.0,
    step=0.1
)

Ta = st.sidebar.slider(
    "주변 또는 냉각수 온도 Tₐ (℃)",
    min_value=5.0,
    max_value=40.0,
    value=20.0,
    step=1.0
)

st.sidebar.subheader("시뮬레이션 조건")

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

st.sidebar.subheader("폐열 회수 조건")

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
    "설정한 안전 온도 기준 (℃)",
    min_value=30.0,
    max_value=100.0,
    value=60.0,
    step=1.0
)

# --------------------------------------------------
# 계산
# --------------------------------------------------
duration_sec = duration_min * 60
time = np.arange(0, duration_sec + dt, dt)

# 열전달 능력
hA = h * A

# 정상상태 온도
T_inf = Ta + P / hA

# 시간상수
tau = (m * c) / hA

# 해석적으로 구한 온도
T_exact = T_inf + (T0 - T_inf) * np.exp(-time / tau)

# 오일러 방법으로 구한 온도
T_euler = np.zeros(len(time))
T_euler[0] = T0

for i in range(len(time) - 1):
    temperature_rate = (
        P - hA * (T_euler[i] - Ta)
    ) / (m * c)

    T_euler[i + 1] = (
        T_euler[i] + dt * temperature_rate
    )

# 외부로 이동하는 순간 열전달률
heat_release_power = hA * (T_exact - Ta)

# 주변에서 냉각유로 열이 들어오는 구간은 회수 열량에서 제외
recoverable_power = np.maximum(heat_release_power, 0)

# 회수 기준 온도 이상에서만 폐열을 회수한다고 가정
recovery_mask = T_exact >= recovery_temp

actual_recovery_power = np.where(
    recovery_mask,
    efficiency * recoverable_power,
    0
)

# 누적 회수 에너지 계산
cumulative_energy_j = np.zeros(len(time))

for i in range(1, len(time)):
    average_power = (
        actual_recovery_power[i - 1]
        + actual_recovery_power[i]
    ) / 2

    cumulative_energy_j[i] = (
        cumulative_energy_j[i - 1]
        + average_power * dt
    )

cumulative_energy_kwh = cumulative_energy_j / 3_600_000

# 오일러 방법 오차
absolute_error = np.abs(T_exact - T_euler)
max_error = np.max(absolute_error)

# 초기 온도 상승률
initial_rate = (
    P - hA * (T0 - Ta)
) / (m * c)

# 회수 시작 시점
recovery_indices = np.where(recovery_mask)[0]

if len(recovery_indices) > 0:
    recovery_start_index = recovery_indices[0]
    recovery_start_min = time[recovery_start_index] / 60
else:
    recovery_start_index = None
    recovery_start_min = None

# 안전 온도 도달 시점
safe_indices = np.where(T_exact >= safe_temp)[0]

if len(safe_indices) > 0:
    safe_time_min = time[safe_indices[0]] / 60
else:
    safe_time_min = None

# --------------------------------------------------
# 핵심 결과
# --------------------------------------------------
st.subheader("📌 핵심 계산 결과")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "정상상태 온도",
    f"{T_inf:.2f} ℃",
    help="시간이 충분히 지났을 때 냉각유가 수렴하는 온도입니다."
)

col2.metric(
    "현재 관찰 종료 온도",
    f"{T_exact[-1]:.2f} ℃"
)

col3.metric(
    "시간상수",
    f"{tau / 60:.2f}분",
    help="온도가 정상상태에 접근하는 속도를 나타냅니다."
)

col4.metric(
    "누적 회수 에너지",
    f"{cumulative_energy_kwh[-1]:.4f} kWh"
)

# --------------------------------------------------
# 시각적 장치 표현
# --------------------------------------------------
current_temp = T_exact[-1]

if current_temp < recovery_temp:
    oil_color = "#58B7FF"
    state_text = "온도 상승 중"
elif current_temp < safe_temp:
    oil_color = "#FFB347"
    state_text = "폐열 회수 가능"
else:
    oil_color = "#FF5C5C"
    state_text = "안전 온도 확인 필요"

st.subheader("👀 액침냉각 장치 모형")

visual_left, visual_right = st.columns([1, 1])

with visual_left:
    st.markdown(
        f"""
        <div style="
            background:#F4F7FB;
            border:2px solid #D5DCE5;
            border-radius:20px;
            padding:24px;
            text-align:center;
        ">
            <div style="
                font-size:22px;
                font-weight:bold;
                margin-bottom:12px;
            ">
                액침냉각 탱크
            </div>

            <div style="
                width:82%;
                height:300px;
                margin:auto;
                border:5px solid #414B57;
                border-radius:10px 10px 25px 25px;
                background:{oil_color};
                position:relative;
                overflow:hidden;
                box-shadow:inset 0 0 25px rgba(0,0,0,0.18);
            ">
                <div style="
                    position:absolute;
                    top:22px;
                    left:0;
                    right:0;
                    color:white;
                    font-weight:bold;
                    font-size:18px;
                ">
                    냉각유 {current_temp:.1f}℃
                </div>

                <div style="
                    position:absolute;
                    width:38%;
                    height:155px;
                    left:31%;
                    bottom:35px;
                    background:#303843;
                    border-radius:8px;
                    box-shadow:0 0 12px rgba(255,255,255,0.5);
                    color:white;
                    padding-top:15px;
                    font-weight:bold;
                ">
                    SERVER
                    <div style="
                        margin:18px auto;
                        width:70%;
                        height:15px;
                        background:#71E096;
                        border-radius:5px;
                    "></div>
                    <div style="
                        margin:10px auto;
                        width:70%;
                        height:15px;
                        background:#71E096;
                        border-radius:5px;
                    "></div>
                    <div style="
                        margin:10px auto;
                        width:70%;
                        height:15px;
                        background:#71E096;
                        border-radius:5px;
                    "></div>
                </div>

                <div style="
                    position:absolute;
                    right:8px;
                    top:80px;
                    font-size:34px;
                ">
                    ↑
                </div>

                <div style="
                    position:absolute;
                    left:8px;
                    top:150px;
                    font-size:34px;
                ">
                    ↑
                </div>
            </div>

            <div style="
                margin-top:15px;
                font-size:20px;
                font-weight:bold;
                color:#303843;
            ">
                상태: {state_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with visual_right:
    st.markdown("#### 에너지의 이동")

    st.markdown(
        f"""
        <div style="
            padding:20px;
            border-radius:15px;
            background:#FFF3E0;
            border-left:7px solid #FF9F43;
            margin-bottom:12px;
        ">
            <b>① 서버에서 발생하는 열</b><br>
            {P:,.0f} W
        </div>

        <div style="
            text-align:center;
            font-size:30px;
            margin:4px;
        ">
            ↓
        </div>

        <div style="
            padding:20px;
            border-radius:15px;
            background:#E7F3FF;
            border-left:7px solid #4EA5FF;
            margin-bottom:12px;
        ">
            <b>② 냉각유가 열을 흡수</b><br>
            초기 온도변화율: {initial_rate * 60:.3f} ℃/분
        </div>

        <div style="
            text-align:center;
            font-size:30px;
            margin:4px;
        ">
            ↓
        </div>

        <div style="
            padding:20px;
            border-radius:15px;
            background:#EAFBEF;
            border-left:7px solid #42C66A;
        ">
            <b>③ 외부로 열 전달 및 회수</b><br>
            관찰 종료 시 열전달률:
            {heat_release_power[-1]:,.1f} W
        </div>
        """,
        unsafe_allow_html=True
    )

# --------------------------------------------------
# 시간에 따른 온도 그래프
# --------------------------------------------------
st.subheader("📈 시간에 따른 냉각유 온도")

temperature_df = pd.DataFrame({
    "시간(분)": time / 60,
    "해석적으로 구한 온도": T_exact,
    "오일러 방법으로 구한 온도": T_euler,
    "폐열 회수 기준 온도": np.full(len(time), recovery_temp),
    "안전 온도 기준": np.full(len(time), safe_temp)
}).set_index("시간(분)")

st.line_chart(temperature_df)

st.write(
    f"해석해와 오일러 근삿값 사이의 최대 오차는 "
    f"**{max_error:.6f}℃**입니다."
)

# --------------------------------------------------
# 온도 변화율
# --------------------------------------------------
st.subheader("📉 냉각유 온도의 순간변화율")

temperature_rate = (
    P - hA * (T_exact - Ta)
) / (m * c)

rate_df = pd.DataFrame({
    "시간(분)": time / 60,
    "온도변화율(℃/분)": temperature_rate * 60
}).set_index("시간(분)")

st.line_chart(rate_df)

st.write(
    "처음에는 서버에서 들어오는 열에 비해 외부로 나가는 열이 적어 "
    "온도가 빠르게 상승합니다. 냉각유 온도가 높아지면 외부로 나가는 "
    "열이 증가하므로 온도변화율은 점차 0에 가까워집니다."
)

# --------------------------------------------------
# 폐열 회수량
# --------------------------------------------------
st.subheader("♻️ 누적 폐열 회수 에너지")

energy_df = pd.DataFrame({
    "시간(분)": time / 60,
    "누적 회수 에너지(kWh)": cumulative_energy_kwh
}).set_index("시간(분)")

st.line_chart(energy_df)

if recovery_start_min is None:
    st.warning(
        f"관찰 시간 동안 냉각유 온도가 회수 기준인 "
        f"{recovery_temp:.1f}℃에 도달하지 않았습니다."
    )
else:
    st.success(
        f"냉각유가 약 {recovery_start_min:.2f}분 후 "
        f"{recovery_temp:.1f}℃에 도달하여 폐열 회수를 "
        f"시작할 수 있습니다."
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

# --------------------------------------------------
# 세부 결과 표
# --------------------------------------------------
with st.expander("📋 시간별 계산 결과 보기"):
    result_df = pd.DataFrame({
        "시간(분)": np.round(time / 60, 2),
        "해석해 온도(℃)": np.round(T_exact, 3),
        "오일러 온도(℃)": np.round(T_euler, 3),
        "온도변화율(℃/분)": np.round(
            temperature_rate * 60, 5
        ),
        "외부 열전달률(W)": np.round(
            heat_release_power, 2
        ),
        "누적 회수 에너지(kWh)": np.round(
            cumulative_energy_kwh, 6
        )
    })

    st.dataframe(result_df, use_container_width=True)

# --------------------------------------------------
# 변수별 의미 해석
# --------------------------------------------------
st.subheader("🔎 현재 조건의 수학적 해석")

if initial_rate > 0:
    initial_state = "상승"
elif initial_rate < 0:
    initial_state = "하강"
else:
    initial_state = "일정"

st.markdown(
    f"""
- 초기 냉각유 온도는 **{T0:.1f}℃**이며, 처음에는 온도가
  **{initial_state}**합니다.
- 초기 온도변화율은 약 **{initial_rate * 60:.3f}℃/분**입니다.
- 냉각유 온도는 장기적으로 약 **{T_inf:.2f}℃**에 수렴합니다.
- 시간상수는 약 **{tau / 60:.2f}분**입니다.
- 질량이나 비열을 크게 하면 온도 상승 속도는 느려지지만,
  이 단순 모형에서 정상상태 온도 자체는 변하지 않습니다.
- 열전달계수나 열전달 면적을 크게 하면 외부로 열이 더 잘 이동하여
  정상상태 온도가 낮아집니다.
"""
)

# --------------------------------------------------
# 공식 설명
# --------------------------------------------------
with st.expander("🧮 사용된 공식 확인하기"):
    st.markdown("#### 1. 에너지수지식")
    st.latex(
        r"mc\frac{dT}{dt}=P-hA(T-T_a)"
    )

    st.markdown("#### 2. 온도의 순간변화율")
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
        r"\left["
        r"\frac{P-hA(T_n-T_a)}{mc}"
        r"\right]"
    )

    st.markdown("#### 6. 누적 회수 열에너지")
    st.latex(
        r"Q_{\mathrm{recovery}}"
        r"=\int_{t_1}^{t_2}"
        r"\eta hA(T(t)-T_a)\,dt"
    )

# --------------------------------------------------
# 모형의 한계
# --------------------------------------------------
with st.expander("⚠️ 이 시뮬레이션의 가정과 한계"):
    st.markdown(
        """
이 시뮬레이션은 미적분 탐구를 위한 단순화된 모형입니다.

- 냉각유 전체의 온도가 균일하다고 가정했습니다.
- 서버의 발열량이 일정하다고 가정했습니다.
- 열전달계수와 냉각유의 비열이 온도에 따라 변하지 않는다고
  가정했습니다.
- 냉각유의 흐름, 펌프 동력, 국소적인 서버 온도 차이는
  반영하지 않았습니다.
- 폐열 회수는 외부로 전달되는 열 중 일정 비율을 활용한다고
  단순화했습니다.
- 사용자가 설정한 안전 온도는 실제 장비의 공식 허용온도가 아니라
  시뮬레이션에서 비교하기 위한 기준입니다.
"""
    )
