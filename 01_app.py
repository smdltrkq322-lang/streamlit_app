from pathlib import Path
import io
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
    extra_units = ((60 - base_min).clip(lower=0) / add_min).apply(
        lambda x: int(-(-x // 1)) if pd.notna(x) and x != float("inf") else 0
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


def make_map(df):
    located = df.dropna(subset=["위도", "경도"])
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
    return fmap, len(located)
