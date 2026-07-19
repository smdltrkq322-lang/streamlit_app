import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="데이터센터 냉각 시뮬레이터", page_icon="🌡️", layout="wide")


FLUIDS = {
    "공기(강제대류)": {"rho": 1.20, "cp": 1005.0, "h": 60.0, "flow_lpm": 4000.0},
    "물(냉각판)": {"rho": 997.0, "cp": 4180.0, "h": 1500.0, "flow_lpm": 5.0},
    "광유계 절연유": {"rho": 850.0, "cp": 1900.0, "h": 250.0, "flow_lpm": 12.0},
    "합성 탄화수소계 절연유": {"rho": 800.0, "cp": 2100.0, "h": 320.0, "flow_lpm": 12.0},
    "직접 입력": {"rho": 850.0, "cp": 2000.0, "h": 250.0, "flow_lpm": 12.0},
}


def simulate(power, server_mass, server_cp, area, inlet_temp, duration, dt,
             rho, fluid_cp, h, flow_lpm, cooler_enabled, cooler_power,
             ambient_temp, cooler_efficiency):
    """서버-유체 2요소 집중정수(lumped) 에너지 보존 모형."""
    times = np.arange(0.0, duration + dt, dt)
    server_temp = np.empty_like(times)
    fluid_temp = np.empty_like(times)
    removed_heat = np.empty_like(times)

    server_temp[0] = inlet_temp
    fluid_temp[0] = inlet_temp
    removed_heat[0] = 0.0

    server_capacity = server_mass * server_cp
    # 1 L = 1e-3 m³. 체류 유체량은 20초 동안 통과하는 양으로 단순화한다.
    volume_flow = flow_lpm * 1e-3 / 60.0
    mass_flow = rho * volume_flow
    resident_mass = max(mass_flow * 20.0, 0.05)
    fluid_capacity = resident_mass * fluid_cp
    ua = h * area

    for i in range(1, len(times)):
        q_server_to_fluid = ua * (server_temp[i - 1] - fluid_temp[i - 1])

        # 순환 유체가 입구 온도로 교체되며 가져가는 열. 완전혼합 탱크 근사.
        q_flow = mass_flow * fluid_cp * (fluid_temp[i - 1] - inlet_temp)

        # 선택적 냉각기: 주변보다 뜨거울 때만 열 제거
        if cooler_enabled and fluid_temp[i - 1] > ambient_temp:
            q_cooler = min(
                cooler_power * cooler_efficiency,
                fluid_capacity * (fluid_temp[i - 1] - ambient_temp) / dt,
            )
        else:
            q_cooler = 0.0

        dts = (power - q_server_to_fluid) / server_capacity * dt
        dtf = (q_server_to_fluid - q_flow - q_cooler) / fluid_capacity * dt

        server_temp[i] = server_temp[i - 1] + dts
        fluid_temp[i] = fluid_temp[i - 1] + dtf
        removed_heat[i] = max(q_flow + q_cooler, 0.0)

    return pd.DataFrame({
        "시간 (s)": times,
        "서버 온도 (°C)": server_temp,
        "유체 온도 (°C)": fluid_temp,
        "제거 열률 (W)": removed_heat,
    }), mass_flow, ua


def run_case(name, values, common):
    df, mass_flow, ua = simulate(
        **common,
        rho=values["rho"],
        fluid_cp=values["cp"],
        h=values["h"],
        flow_lpm=values["flow_lpm"],
    )
    df["조건"] = name
    return df, mass_flow, ua


st.title("🌡️ AI 데이터센터 냉각 시뮬레이터")
st.caption("에너지 보존식으로 공랭·수랭·액침냉각의 온도 변화를 비교하는 교육용 모형")

with st.expander("이 시뮬레이터가 사용하는 물리 모형", expanded=False):
    st.latex(r"m_sc_s\frac{dT_s}{dt}=P-hA(T_s-T_f)")
    st.latex(r"m_fc_f\frac{dT_f}{dt}=hA(T_s-T_f)-\dot m c_f(T_f-T_{in})-\dot Q_{cooler}")
    st.markdown(
        "서버에서 발생한 열이 대류로 유체에 전달되고, 흐르는 유체와 냉각기가 그 열을 제거한다고 가정합니다. "
        "실제 장비의 복잡한 형상·난류·국부 온도는 생략했으므로 절대적인 설계값이 아니라 변수의 경향을 비교하는 모형입니다."
    )

left, right = st.columns([1, 2])

with left:
    st.subheader("1. 실험 조건")
    selected = st.selectbox("냉각 방식/유체", list(FLUIDS))
    defaults = FLUIDS[selected]

    power = st.slider("서버 발열량 P (W)", 100, 3000, 1000, 50)
    area = st.slider("유효 접촉 면적 A (m²)", 0.05, 2.00, 0.50, 0.05)
    server_mass = st.slider("서버 등가 질량 (kg)", 1.0, 30.0, 8.0, 0.5)
    server_cp = st.slider("서버 등가 비열 (J/kg·K)", 300, 1200, 700, 25)
    inlet_temp = st.slider("냉각 유체 입구 온도 (°C)", 10.0, 40.0, 25.0, 0.5)
    duration = st.slider("시뮬레이션 시간 (분)", 1, 60, 20)

    st.subheader("2. 냉각 유체 물성")
    rho = st.number_input("밀도 ρ (kg/m³)", 0.1, 2000.0, float(defaults["rho"]), 1.0)
    fluid_cp = st.number_input("비열 cₚ (J/kg·K)", 100.0, 5000.0, float(defaults["cp"]), 50.0)
    h = st.number_input("대류 열전달계수 h (W/m²·K)", 1.0, 5000.0, float(defaults["h"]), 10.0)
    flow_lpm = st.number_input("체적 유량 (L/min)", 0.1, 10000.0, float(defaults["flow_lpm"]), 1.0)

    cooler_enabled = st.checkbox("외부 냉각기 사용", value=False)
    cooler_power = st.slider("냉각기 소비전력 (W)", 0, 2000, 300, 50, disabled=not cooler_enabled)
    cooler_efficiency = st.slider("냉각기 성능계수(COP)", 1.0, 6.0, 3.0, 0.1, disabled=not cooler_enabled)
    ambient_temp = st.slider("주변 온도 (°C)", 5.0, 40.0, 22.0, 0.5, disabled=not cooler_enabled)

values = {"rho": rho, "cp": fluid_cp, "h": h, "flow_lpm": flow_lpm}
common = dict(
    power=power,
    server_mass=server_mass,
    server_cp=server_cp,
    area=area,
    inlet_temp=inlet_temp,
    duration=duration * 60.0,
    dt=0.2,
    cooler_enabled=cooler_enabled,
    cooler_power=cooler_power,
    ambient_temp=ambient_temp,
    cooler_efficiency=cooler_efficiency,
)

df, mass_flow, ua = run_case(selected, values, common)

with right:
    st.subheader("온도 변화 결과")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("최종 서버 온도", f"{df['서버 온도 (°C)'].iloc[-1]:.1f} °C")
    m2.metric("최고 서버 온도", f"{df['서버 온도 (°C)'].max():.1f} °C")
    m3.metric("질량 유량", f"{mass_flow:.3f} kg/s")
    m4.metric("UA", f"{ua:.1f} W/K")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["시간 (s)"] / 60, y=df["서버 온도 (°C)"], name="서버"))
    fig.add_trace(go.Scatter(x=df["시간 (s)"] / 60, y=df["유체 온도 (°C)"], name="냉각 유체"))
    fig.update_layout(xaxis_title="시간 (분)", yaxis_title="온도 (°C)", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    volumetric_heat_capacity = rho * fluid_cp / 1_000_000
    st.info(
        f"현재 유체의 단위 부피당 열용량 ρcₚ = **{volumetric_heat_capacity:.3f} MJ/(m³·K)**입니다. "
        "이 값이 클수록 같은 부피의 유체가 온도 1 K 상승하며 더 많은 에너지를 저장합니다."
    )

st.divider()
st.subheader("3. 변수 통제 실험")
experiment = st.selectbox("한 변수만 변화시켜 영향 확인", ["비열", "밀도", "열전달계수", "유량"])

ranges = {
    "비열": ("cp", np.linspace(max(200, fluid_cp * 0.4), fluid_cp * 1.6, 15), "비열 (J/kg·K)"),
    "밀도": ("rho", np.linspace(max(0.5, rho * 0.4), rho * 1.6, 15), "밀도 (kg/m³)"),
    "열전달계수": ("h", np.linspace(max(1, h * 0.25), h * 2.0, 15), "열전달계수 (W/m²·K)"),
    "유량": ("flow_lpm", np.linspace(max(0.1, flow_lpm * 0.25), flow_lpm * 2.0, 15), "유량 (L/min)"),
}
key, test_values, x_label = ranges[experiment]
records = []
for x in test_values:
    trial = values.copy()
    trial[key] = float(x)
    trial_df, _, _ = run_case("실험", trial, common)
    records.append({x_label: x, "최고 서버 온도 (°C)": trial_df["서버 온도 (°C)"].max()})
sweep = pd.DataFrame(records)
st.line_chart(sweep, x=x_label, y="최고 서버 온도 (°C)")

with st.expander("공랭·수랭·액침냉각을 한 번에 비교"):
    compare_names = ["공기(강제대류)", "물(냉각판)", "광유계 절연유", "합성 탄화수소계 절연유"]
    comparison = []
    summary = []
    for name in compare_names:
        case_df, case_flow, case_ua = run_case(name, FLUIDS[name], common)
        comparison.append(case_df)
        summary.append({
            "방식": name,
            "최고 서버 온도 (°C)": case_df["서버 온도 (°C)"].max(),
            "최종 서버 온도 (°C)": case_df["서버 온도 (°C)"].iloc[-1],
            "ρcₚ (MJ/m³·K)": FLUIDS[name]["rho"] * FLUIDS[name]["cp"] / 1_000_000,
            "hA (W/K)": case_ua,
        })
    all_cases = pd.concat(comparison, ignore_index=True)
    compare_fig = go.Figure()
    for name in compare_names:
        part = all_cases[all_cases["조건"] == name]
        compare_fig.add_trace(go.Scatter(x=part["시간 (s)"] / 60, y=part["서버 온도 (°C)"], name=name))
    compare_fig.update_layout(xaxis_title="시간 (분)", yaxis_title="서버 온도 (°C)", hovermode="x unified")
    st.plotly_chart(compare_fig, use_container_width=True)
    st.dataframe(pd.DataFrame(summary).style.format(precision=2), use_container_width=True)
    st.warning(
        "기본값은 대표적인 교육용 가정값입니다. 열전달계수는 유체만의 고유값이 아니라 장치 구조와 유속에 따라 달라지므로, "
        "이 비교 결과를 실제 제품의 성능 보증값으로 사용하면 안 됩니다."
    )

st.subheader("4. 결과 저장")
st.download_button(
    "현재 결과 CSV 내려받기",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name="cooling_simulation_result.csv",
    mime="text/csv",
)
