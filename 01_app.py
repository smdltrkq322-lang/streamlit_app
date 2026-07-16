from pathlib import Path
import io
import math
import re

import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium


st.set_page_config(page_title="서울 공영주차장 찾기", page_icon="🅿️", layout="wide")

BASE_DIR = Path(__file__).parent
DEFAULT_CSV = BASE_DIR / "서울시_공영주차장.csv"

REQUIRED = ["주차장명", "주소", "위도", "경도"]


def read_csv(source):
    """서울시 원본(CP949)과 일반 UTF-8 CSV를 모두 읽는다."""
    raw = source.read() if hasattr(source, "read") else Path(source).read_bytes()
    if hasattr(source, "seek"):
        source.seek(0)
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV 문자 인코딩을 확인할 수 없습니다. UTF-8 또는 CP949 파일을 사용해 주세요.")


def clean_data(df):
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError("필수 열이 없습니다: " + ", ".join(missing))

    numeric_cols = [
        "위도", "경도", "기본 주차 요금", "기본 주차 시간(분 단위)",
        "추가 단위 요금", "추가 단위 시간(분 단위)", "일 최대 요금",
        "월 정기권 금액", "총 주차면",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 주소 첫 부분에서 서울 자치구를 추출한다.
    df["자치구"] = df["주소"].fillna("").astype(str).str.extract(r"((?:서울특별시\s+)?[가-힣]+구)", expand=False)
    df["자치구"] = df["자치구"].str.replace("서울특별시 ", "", regex=False)
    df["자치구"] = df["자치구"].fillna("구 정보 없음")

    free_name = df.get("유무료구분명", pd.Series("", index=df.index)).fillna("").astype(str)
    base_fee = df.get("기본 주차 요금", pd.Series(float("nan"), index=df.index))
    df["무료 여부"] = free_name.eq("무료") | base_fee.eq(0)

    weekend_start = df.get("주말 운영 시작시각(HHMM)", pd.Series(float("nan"), index=df.index))
    weekend_end = df.get("주말 운영 종료시각(HHMM)", pd.Series(float("nan"), index=df.index))
    saturday = df.get("토요일 유,무료 구분명", pd.Series("", index=df.index)).fillna("").astype(str)
    df["주말 운영"] = weekend_start.notna() & weekend_end.notna() | saturday.ne("")

    # 서로 다른 기본 시간 체계를 공정하게 비교하기 위한 60분 예상 요금.
    base_min = df.get("기본 주차 시간(분 단위)", pd.Series(float("nan"), index=df.index))
    add_fee = df.get("추가 단위 요금", pd.Series(float("nan"), index=df.index)).fillna(0)
    add_min = df.get("추가 단위 시간(분 단위)", pd.Series(float("nan"), index=df.index))
    # 추가 단위 시간이 0/결측인 행은 추가요금을 계산하지 않는다.
    safe_add_min = add_min.where(add_min.gt(0))
    extra_units = ((60 - base_min).clip(lower=0) / safe_add_min).apply(
        lambda x: math.ceil(x) if pd.notna(x) and math.isfinite(x) else 0
    )
    df["60분 예상 요금"] = base_fee + extra_units * add_fee
    df.loc[df["무료 여부"], "60분 예상 요금"] = 0
    df.loc[base_fee.isna(), "60분 예상 요금"] = pd.NA
    return df


def won(value):
    return "정보 없음" if pd.isna(value) else f"{value:,.0f}원"


def hhmm(value):
    if pd.isna(value):
        return "정보 없음"
    value = int(value)
    if value == 2400:
        return "24:00"
    return f"{value // 100:02d}:{value % 100:02d}"


def make_map(df, marker_limit=400):
    located = df.dropna(subset=["위도", "경도"])
    total_located = len(located)
    # 너무 많은 HTML 마커는 Streamlit 화면을 멈추게 할 수 있어 표시 수를 제한한다.
    located = located.head(marker_limit)
    center = [located["위도"].mean(), located["경도"].mean()] if len(located) else [37.5665, 126.9780]
    fmap = folium.Map(location=center, zoom_start=12, tiles="CartoDB positron")
    cluster = MarkerCluster(name="공영주차장").add_to(fmap)

    for _, row in located.iterrows():
        fee = "무료" if row["무료 여부"] else won(row.get("기본 주차 요금"))
        weekend = "운영 정보 있음" if row["주말 운영"] else "정보 없음"
        tooltip = folium.Tooltip(
            f"<b>{row['주차장명']}</b><br>주소: {row['주소']}<br>기본 요금: {fee}<br>주말: {weekend}",
            sticky=True,
        )
        popup = folium.Popup(
            f"<b>{row['주차장명']}</b><br>{row['주소']}<br>"
            f"60분 예상 요금: {won(row.get('60분 예상 요금'))}<br>"
            f"주차면: {won(row.get('총 주차면')).replace('원', '면')}<br>"
            f"전화: {row.get('전화번호', '정보 없음')}",
            max_width=330,
        )
        color = "green" if row["무료 여부"] else "blue"
        folium.Marker(
            [row["위도"], row["경도"]], tooltip=tooltip, popup=popup,
            icon=folium.Icon(color=color, icon="car", prefix="fa"),
        ).add_to(cluster)
    return fmap, len(located), total_located


st.title("🅿️ 서울 공영주차장 찾기")
st.caption("주소·요금·운영 정보를 비교하고, 자치구별 저렴한 주차장을 찾아보세요.")

with st.sidebar:
    st.header("데이터")
    uploaded = st.file_uploader("공영주차장 CSV 업로드", type=["csv"], help="UTF-8 또는 CP949 CSV를 지원합니다.")

try:
    df, encoding = read_csv(uploaded if uploaded is not None else DEFAULT_CSV)
    df = clean_data(df)
except Exception as exc:
    st.error(f"데이터를 불러오지 못했습니다: {exc}")
    st.stop()

districts = sorted(x for x in df["자치구"].unique() if x != "구 정보 없음")
with st.sidebar:
    st.success(f"{len(df):,}개 주차장 · {encoding.upper()}")
    district = st.selectbox("자치구", ["전체"] + districts)
    query = st.text_input("주차장명 또는 주소 검색")
    fee_mode = st.radio("요금", ["전체", "무료만", "유료만"], horizontal=True)
    weekend_only = st.checkbox("주말 운영 정보가 있는 곳만")
    max_hour = st.number_input("60분 예상 요금 상한(원, 0은 제한 없음)", min_value=0, value=0, step=500)
    marker_limit = st.select_slider("지도에 표시할 최대 마커", options=[100, 200, 300, 400], value=300)

filtered = df.copy()
if district != "전체":
    filtered = filtered[filtered["자치구"] == district]
if query:
    mask = (
        filtered["주차장명"].fillna("").str.contains(re.escape(query), case=False)
        | filtered["주소"].fillna("").str.contains(re.escape(query), case=False)
    )
    filtered = filtered[mask]
if fee_mode == "무료만":
    filtered = filtered[filtered["무료 여부"]]
elif fee_mode == "유료만":
    filtered = filtered[~filtered["무료 여부"]]
if weekend_only:
    filtered = filtered[filtered["주말 운영"]]
if max_hour > 0:
    filtered = filtered[filtered["60분 예상 요금"].le(max_hour)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("검색 결과", f"{len(filtered):,}곳")
c2.metric("무료", f"{int(filtered['무료 여부'].sum()):,}곳")
c3.metric("주말 정보 있음", f"{int(filtered['주말 운영'].sum()):,}곳")
c4.metric("좌표 보유", f"{filtered[['위도', '경도']].notna().all(axis=1).sum():,}곳")

st.subheader("추천: 선택 지역의 최저 요금")
priced = filtered.dropna(subset=["60분 예상 요금"]).sort_values(["60분 예상 요금", "기본 주차 요금", "주차장명"])
if priced.empty:
    st.info("현재 조건에서 요금을 비교할 수 있는 주차장이 없습니다.")
else:
    cheapest_fee = priced.iloc[0]["60분 예상 요금"]
    cheapest = priced[priced["60분 예상 요금"] == cheapest_fee].head(5)
    st.success(f"60분 예상 요금 최저: {won(cheapest_fee)} · 동률 최대 5곳 표시")
    st.dataframe(
        cheapest[["주차장명", "주소", "유무료구분명", "기본 주차 요금", "기본 주차 시간(분 단위)", "60분 예상 요금"]],
        use_container_width=True, hide_index=True,
    )

st.subheader("지도")
fmap, mapped_count, total_located = make_map(filtered, marker_limit)
st_folium(fmap, use_container_width=True, height=580, key="parking_map")
if total_located > mapped_count:
    st.info(
        f"빠른 화면 표시를 위해 좌표가 있는 {total_located:,}곳 중 {mapped_count:,}곳만 지도에 표시했습니다. "
        "자치구나 검색 조건을 선택하면 원하는 지역을 모두 확인하기 쉽습니다."
    )
missing_coords = len(filtered) - total_located
if missing_coords:
    st.caption(f"위도·경도가 없는 {missing_coords:,}곳은 지도에서 제외되었습니다. 아래 표에서는 확인할 수 있습니다.")

st.subheader("상세 정보")
display_cols = [c for c in [
    "주차장명", "자치구", "주소", "유무료구분명", "60분 예상 요금", "일 최대 요금",
    "총 주차면", "주차장 종류명", "운영구분명", "야간무료개방여부명", "전화번호"
] if c in filtered.columns]
st.dataframe(filtered[display_cols].sort_values(["60분 예상 요금", "주차장명"], na_position="last"), use_container_width=True, hide_index=True)

download = filtered[display_cols].to_csv(index=False).encode("utf-8-sig")
st.download_button("검색 결과 CSV 내려받기", download, "공영주차장_검색결과.csv", "text/csv")

with st.expander("요금 비교 기준과 데이터 안내"):
    st.write(
        "60분 예상 요금은 기본 요금에 60분까지 필요한 추가 단위 요금을 올림하여 더한 값입니다. "
        "실제 요금은 입·출차 시각, 감면, 운영 정책에 따라 달라질 수 있습니다. "
        "주말 운영 여부는 주말 운영시간 또는 토요일 요금 정보가 기록되어 있는지를 기준으로 표시합니다."
    )


    


