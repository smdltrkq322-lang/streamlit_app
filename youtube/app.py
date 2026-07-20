import html
import re
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from wordcloud import WordCloud


st.set_page_config(page_title="유튜브 댓글 분석기", page_icon="▶️", layout="wide")

FONT_CANDIDATES = [
    Path("NanumGothic.ttf"),
    Path("fonts/NanumGothic.ttf"),
    Path("NanumGothic-Regular.ttf"),
    Path("fonts/NanumGothic-Regular.ttf"),
]

POSITIVE_WORDS = {
    "좋다", "좋아요", "최고", "재밌다", "재미있다", "감사", "고맙다", "멋지다",
    "훌륭하다", "유익하다", "도움", "추천", "응원", "사랑", "행복", "웃기다",
    "대박", "완벽", "감동", "존경", "기대", "잘하다", "예쁘다", "귀엽다",
}
NEGATIVE_WORDS = {
    "싫다", "별로", "최악", "재미없다", "화나다", "짜증", "실망", "불편",
    "문제", "거짓", "나쁘다", "못하다", "답답", "비추천", "혐오", "슬프다",
    "무섭다", "지루하다", "아쉽다", "비판", "오류", "틀리다", "망하다",
}
STOPWORDS = {
    "그리고", "그러나", "하지만", "그래서", "정말", "진짜", "너무", "아주", "조금",
    "영상", "댓글", "유튜브", "제가", "저는", "나는", "이것", "저것", "그것", "있는",
    "없는", "같아요", "합니다", "입니다", "하는", "하면", "해서", "보다", "에서", "으로",
    "에게", "까지", "부터", "하고", "the", "and", "this", "that", "with", "you",
}


def extract_video_id(value: str) -> str | None:
    value = value.strip()
    patterns = [
        r"(?:youtube\.com/watch\?(?:[^#\s]*&)?v=)([\w-]{11})",
        r"(?:youtu\.be/)([\w-]{11})",
        r"(?:youtube\.com/(?:shorts|embed|live)/)([\w-]{11})",
        r"^([\w-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    return None


@st.cache_resource
def youtube_client(api_key: str):
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)


@st.cache_data(ttl=3600, show_spinner=False)
def get_video_info(api_key: str, video_id: str) -> dict:
    response = youtube_client(api_key).videos().list(
        part="snippet,statistics", id=video_id
    ).execute()
    if not response.get("items"):
        raise ValueError("영상을 찾을 수 없습니다. 공개 영상 링크인지 확인해 주세요.")
    item = response["items"][0]
    return {
        "title": item["snippet"]["title"],
        "channel": item["snippet"]["channelTitle"],
        "published_at": item["snippet"]["publishedAt"],
        "comment_count": int(item.get("statistics", {}).get("commentCount", 0)),
        "view_count": int(item.get("statistics", {}).get("viewCount", 0)),
        "like_count": int(item.get("statistics", {}).get("likeCount", 0)),
    }


@st.cache_data(ttl=3600, show_spinner=False)
def get_comments(api_key: str, video_id: str, limit: int, order: str) -> pd.DataFrame:
    service = youtube_client(api_key)
    rows, page_token = [], None
    while len(rows) < limit:
        response = service.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(100, limit - len(rows)),
            order=order,
            textFormat="plainText",
            pageToken=page_token,
        ).execute()
        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            rows.append({
                "작성 시각": snippet["publishedAt"],
                "댓글": html.unescape(snippet.get("textDisplay", "")),
                "좋아요": int(snippet.get("likeCount", 0)),
                "답글 수": int(item["snippet"].get("totalReplyCount", 0)),
            })
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["작성 시각"] = pd.to_datetime(frame["작성 시각"], utc=True).dt.tz_convert("Asia/Seoul")
    return frame


def tokens(text: str) -> list[str]:
    words = re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}", text.lower())
    return [word for word in words if word not in STOPWORDS]


def sentiment(text: str) -> tuple[str, int]:
    words = tokens(text)
    positive = sum(any(key in word or word in key for key in POSITIVE_WORDS) for word in words)
    negative = sum(any(key in word or word in key for key in NEGATIVE_WORDS) for word in words)
    score = positive - negative
    return ("긍정" if score > 0 else "부정" if score < 0 else "중립"), score


def find_font() -> Path | None:
    return next((path for path in FONT_CANDIDATES if path.exists()), None)


def wordcloud_figure(text: str, font_path: Path):
    frequencies = Counter(tokens(text))
    if not frequencies:
        return None
    cloud = WordCloud(
        font_path=str(font_path), width=1200, height=650, background_color="white",
        colormap="viridis", max_words=150, collocations=False,
    ).generate_from_frequencies(frequencies)
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.imshow(cloud, interpolation="bilinear")
    ax.axis("off")
    fig.tight_layout(pad=0)
    return fig


st.title("▶️ 유튜브 댓글 분석기")
st.caption("공개 영상의 최상위 댓글을 수집해 작성 추이, 반응도, 감성 분포와 워드클라우드를 보여줍니다.")

try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("YouTube API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에 YOUTUBE_API_KEY를 등록해 주세요.")
    st.code('YOUTUBE_API_KEY = "여기에_본인의_API_키"', language="toml")
    st.stop()

with st.sidebar:
    st.header("분석 설정")
    url = st.text_input("유튜브 영상 링크", placeholder="https://www.youtube.com/watch?v=...")
    limit = st.slider("가져올 댓글 수", 10, 1000, 200, step=10)
    order_label = st.radio("댓글 수집 순서", ["인기순", "최신순"], horizontal=True)
    interval = st.selectbox("작성 추이 시간 단위", ["시간", "일", "주", "월"], index=1)
    analyze = st.button("댓글 분석하기", type="primary", use_container_width=True)
    st.caption("설정한 수는 최대 수집 개수이며, 실제 공개 댓글이 적으면 더 적게 표시됩니다.")

if not analyze:
    st.info("왼쪽에서 영상 링크와 댓글 수를 설정한 뒤 ‘댓글 분석하기’를 눌러 주세요.")
    st.stop()

video_id = extract_video_id(url)
if not video_id:
    st.error("올바른 YouTube 영상 링크 또는 11자리 영상 ID를 입력해 주세요.")
    st.stop()

try:
    with st.spinner("영상 정보와 댓글을 불러오는 중입니다..."):
        info = get_video_info(API_KEY, video_id)
        df = get_comments(API_KEY, video_id, limit, "relevance" if order_label == "인기순" else "time")
except HttpError as error:
    reason = "YouTube API 요청에 실패했습니다. API 사용 설정, 할당량, 영상의 댓글 공개 여부를 확인해 주세요."
    if getattr(error, "resp", None) is not None and error.resp.status == 403:
        reason = "API 요청이 거부되었습니다. YouTube Data API v3 활성화 여부와 일일 할당량을 확인해 주세요."
    st.error(reason)
    st.stop()
except (ValueError, Exception) as error:
    st.error(f"분석할 수 없습니다: {error}")
    st.stop()

st.video(f"https://www.youtube.com/watch?v={video_id}")
st.subheader(info["title"])
st.caption(f"채널: {info['channel']}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("조회 수", f"{info['view_count']:,}")
c2.metric("영상 좋아요", f"{info['like_count']:,}")
c3.metric("전체 댓글 수", f"{info['comment_count']:,}")
c4.metric("분석 댓글 수", f"{len(df):,}")

if df.empty:
    st.warning("수집할 수 있는 공개 댓글이 없습니다. 댓글이 사용 중지되었거나 공개 댓글이 없을 수 있습니다.")
    st.stop()

labels_scores = df["댓글"].apply(sentiment)
df["감성"] = labels_scores.str[0]
df["감성 점수"] = labels_scores.str[1]

tab1, tab2, tab3, tab4 = st.tabs(["작성 추이", "댓글 반응도", "워드클라우드", "댓글 데이터"])

with tab1:
    freq_map = {"시간": "h", "일": "D", "주": "W-MON", "월": "MS"}
    timeline = (
        df.set_index("작성 시각").resample(freq_map[interval]).size()
        .rename("댓글 수").reset_index()
    )
    fig = px.line(timeline, x="작성 시각", y="댓글 수", markers=True, title=f"{interval}별 댓글 작성 추이")
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    left, right = st.columns(2)
    counts = df["감성"].value_counts().reindex(["긍정", "중립", "부정"], fill_value=0).reset_index()
    counts.columns = ["감성", "댓글 수"]
    color_map = {"긍정": "#2ca02c", "중립": "#9e9e9e", "부정": "#d62728"}
    left.plotly_chart(px.pie(counts, names="감성", values="댓글 수", hole=.45, color="감성", color_discrete_map=color_map,
                             title="댓글 감성 분포"), use_container_width=True)
    reaction = df.sort_values("좋아요", ascending=False).head(15).copy()
    reaction["짧은 댓글"] = reaction["댓글"].str.replace(r"\s+", " ", regex=True).str.slice(0, 35)
    right.plotly_chart(px.bar(reaction, x="좋아요", y="짧은 댓글", orientation="h", color="감성",
                              color_discrete_map=color_map, title="좋아요가 많은 댓글", hover_data=["댓글", "답글 수"]),
                       use_container_width=True)
    st.caption("감성 결과는 간단한 한국어 표현 사전 기반의 참고값입니다. 문맥, 반어법, 신조어를 정확히 판별하지 못할 수 있습니다.")

with tab3:
    font_path = find_font()
    if font_path is None:
        st.error("한글 폰트 파일을 찾지 못했습니다. GitHub 저장소 루트 또는 fonts 폴더에 NanumGothic.ttf를 업로드해 주세요.")
    else:
        wc_fig = wordcloud_figure(" ".join(df["댓글"]), font_path)
        if wc_fig:
            st.pyplot(wc_fig, use_container_width=True)
            plt.close(wc_fig)
        else:
            st.info("워드클라우드를 만들 한글·영문 단어가 충분하지 않습니다.")
        top_words = pd.DataFrame(Counter(tokens(" ".join(df["댓글"]))).most_common(20), columns=["단어", "빈도"])
        if not top_words.empty:
            st.plotly_chart(px.bar(top_words, x="빈도", y="단어", orientation="h", title="상위 20개 단어"), use_container_width=True)

with tab4:
    st.dataframe(df.sort_values("작성 시각", ascending=False), use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("분석 결과 CSV 다운로드", csv, f"youtube_comments_{video_id}.csv", "text/csv")

