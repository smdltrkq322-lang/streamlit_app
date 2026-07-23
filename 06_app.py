import random
from datetime import datetime

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="고3 생존 시뮬레이터",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)


MAX_TURNS = 16
STAT_INFO = {
    "study": ("📚", "공부"),
    "energy": ("💪", "체력"),
    "mental": ("🌈", "멘탈"),
    "relation": ("🤝", "인간관계"),
}


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&family=Noto+Sans+KR:wght@400;600;700&display=swap');

:root {
    --pink: #ff7eb6;
    --purple: #a78bfa;
    --blue: #72b6ff;
    --mint: #63d8c6;
    --cream: #fffaf3;
}
.stApp {
    background:
      radial-gradient(circle at 10% 0%, rgba(255, 192, 220, .36), transparent 30%),
      radial-gradient(circle at 92% 8%, rgba(188, 218, 255, .38), transparent 28%),
      linear-gradient(180deg, #fffaff 0%, #f7fbff 100%);
    color: #3f3b55;
}
html, body, [class*="css"] { font-family: "Noto Sans KR", sans-serif; }
h1, h2, h3 { font-family: "Jua", "Noto Sans KR", sans-serif !important; color: #51476f; }
.hero {
    padding: 1.4rem 1.6rem;
    border-radius: 26px;
    background: linear-gradient(135deg, #fff0f7, #eef5ff);
    border: 2px solid rgba(255,255,255,.9);
    box-shadow: 0 12px 30px rgba(116, 94, 150, .12);
    margin-bottom: 1rem;
}
.hero-title { font-family: "Jua"; font-size: 2.45rem; color: #6d57a5; line-height: 1.1; }
.hero-sub { margin-top: .55rem; color: #766d8e; font-weight: 600; }
.cute-card {
    background: rgba(255,255,255,.82);
    padding: 1rem 1.1rem;
    border-radius: 20px;
    border: 1px solid rgba(181,168,214,.22);
    box-shadow: 0 8px 20px rgba(90,73,120,.08);
    margin: .3rem 0 .8rem;
}
.event-card {
    background: linear-gradient(135deg, #fff8d9 0%, #fff0f7 100%);
    padding: 1.25rem 1.35rem;
    border-radius: 22px;
    border: 2px dashed #efb6d2;
    margin: .6rem 0 1rem;
}
.event-title { font-family: "Jua"; font-size: 1.55rem; color: #6a537c; }
.tag {
    display: inline-block; padding: .25rem .65rem; margin: .1rem;
    background: #f1ebff; color: #685692; border-radius: 999px; font-size: .84rem;
}
.stat-label { font-weight: 700; color: #5e5674; }
.ending-card {
    text-align: center; padding: 2rem 1.2rem; border-radius: 28px;
    background: linear-gradient(135deg, #fff1b8, #ffd7ec 48%, #dcecff);
    border: 3px solid white; box-shadow: 0 15px 35px rgba(99,74,132,.17);
}
.ending-emoji { font-size: 5rem; line-height: 1; }
.ending-title { font-family: "Jua"; font-size: 2rem; color: #665093; margin: .6rem 0; }
.tiny { font-size: .84rem; color: #8b829b; }
.stButton > button {
    border-radius: 15px; border: 0; font-weight: 700; min-height: 3rem;
    background: linear-gradient(135deg, #ff91bd, #a990f8); color: white;
    box-shadow: 0 5px 12px rgba(142,101,170,.18);
}
.stButton > button:hover { transform: translateY(-1px); color: white; }
div[data-testid="stMetric"] {
    background: rgba(255,255,255,.78); border-radius: 17px; padding: .8rem;
    border: 1px solid rgba(170,150,210,.2);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


PERSONALITIES = {
    "🌱 차분한 계획형": {"study": 8, "mental": 5},
    "🔥 열정 돌격형": {"study": 5, "energy": 8},
    "🎈 긍정 만렙형": {"mental": 10, "relation": 5},
    "🫶 다정한 협력형": {"relation": 10, "mental": 3},
}

SPECIALTIES = {
    "📝 수행평가 정리": "첫 수행평가 선택의 공부 효과 +5",
    "⚡ 초고속 낮잠": "낮잠권의 체력 회복 +10",
    "🗣️ 친구와 소통": "인간관계 상승 효과 +3",
    "🧘 멘탈 회복": "멘탈 감소량 20% 완화",
}

ITEMS = {
    "🍪 행복 간식": {"description": "멘탈 +12, 체력 +5", "delta": {"mental": 12, "energy": 5}},
    "😴 낮잠권": {"description": "체력 +22, 공부 -3", "delta": {"energy": 22, "study": -3}},
    "📮 수행평가 연장권": {"description": "공부 +15, 멘탈 +6", "delta": {"study": 15, "mental": 6}},
    "💌 응원 쪽지": {"description": "멘탈 +10, 인간관계 +8", "delta": {"mental": 10, "relation": 8}},
}

EVENTS = [
    {
        "id": "assignment",
        "emoji": "📝",
        "title": "수행평가 D-1",
        "text": "제출은 내일인데 아직 절반밖에 못 했다! 교실 시계가 유난히 빠르게 간다.",
        "choices": [
            ("🌙 계획을 세워 늦게까지 완성한다", {"study": 25, "energy": -22, "mental": -8}, "어찌어찌 완성! 하지만 눈꺼풀이 무겁다."),
            ("🤝 친구에게 막힌 부분을 물어본다", {"study": 15, "relation": 10, "mental": 3}, "서로 설명하며 함께 진도가 나갔다."),
            ("🙋 선생님께 상황을 솔직하게 말한다", {"mental": 5}, "선생님의 답변을 기다리는 중이다.", "teacher"),
            ("🛌 오늘은 충분히 자고 내일 집중한다", {"energy": 20, "study": -15, "mental": 5}, "개운하지만 남은 시간이 줄었다."),
        ],
    },
    {
        "id": "exam",
        "emoji": "📖",
        "title": "갑작스러운 쪽지시험",
        "text": "선생님이 밝게 웃으며 종이를 나눠 주신다. 교실에는 긴장감이 흐른다.",
        "choices": [
            ("✏️ 아는 문제부터 침착하게 푼다", {"study": 13, "mental": 5}, "생각보다 술술 풀렸다!"),
            ("🧠 마지막 3분까지 검토한다", {"study": 18, "energy": -7}, "실수 하나를 발견했다."),
            ("🍀 감을 믿고 빠르게 제출한다", {"study": -5, "mental": 8, "energy": 4}, "결과는 미래의 나에게 맡겼다."),
        ],
    },
    {
        "id": "lunch",
        "emoji": "🍱",
        "title": "오늘의 급식은 인기 메뉴",
        "text": "점심시간 종과 동시에 복도가 북적북적! 친구들이 같이 가자고 손짓한다.",
        "choices": [
            ("🏃 친구들과 바로 급식실로 간다", {"energy": 12, "relation": 10}, "맛있는 점심과 수다로 충전 완료!"),
            ("📚 10분만 더 공부하고 간다", {"study": 9, "energy": 5, "relation": -3}, "공부도 하고 밥도 챙겼다."),
            ("🌿 조용한 곳에서 천천히 쉰다", {"mental": 14, "energy": 8}, "잠시 혼자만의 평화를 누렸다."),
        ],
    },
    {
        "id": "group",
        "emoji": "🧩",
        "title": "조별 활동 역할 정하기",
        "text": "아무도 발표자를 정하지 못하고 서로 눈치만 보는 중이다.",
        "choices": [
            ("🎤 내가 발표를 맡는다", {"study": 9, "relation": 12, "energy": -8}, "조원들이 안도의 미소를 지었다."),
            ("📊 자료 조사를 꼼꼼히 맡는다", {"study": 16, "energy": -7, "relation": 5}, "믿을 만한 자료 담당이 되었다."),
            ("🗂️ 역할을 공평하게 나누자고 제안한다", {"mental": 6, "relation": 15}, "모두 납득할 만한 계획이 완성됐다."),
        ],
    },
    {
        "id": "class_president",
        "emoji": "📢",
        "title": "반장 긴급 임무",
        "text": "담임 선생님이 오늘 안에 반 친구들의 의견을 모아 달라고 부탁하셨다.",
        "choices": [
            ("📋 설문을 만들어 빠르게 정리한다", {"study": 8, "relation": 13, "energy": -6}, "깔끔한 정리에 칭찬을 받았다."),
            ("👥 친구들과 업무를 나누어 처리한다", {"relation": 16, "mental": 5}, "역시 함께하면 일이 빨라진다."),
            ("⏰ 쉬는 시간마다 직접 물어본다", {"relation": 10, "energy": -13, "mental": -4}, "전원의 의견을 모았지만 조금 지쳤다."),
        ],
    },
    {
        "id": "night_study",
        "emoji": "🌙",
        "title": "야간 자율학습의 유혹",
        "text": "창밖은 어둡고 책상은 포근하다. 오늘 목표까지는 딱 두 단원 남았다.",
        "choices": [
            ("🎯 한 단원만 완벽히 끝낸다", {"study": 17, "energy": -9, "mental": 2}, "현실적인 목표 달성!"),
            ("☕ 자리에서 스트레칭하고 계속한다", {"study": 12, "energy": -3}, "잠이 조금 달아났다."),
            ("🏠 컨디션을 위해 일찍 귀가한다", {"energy": 17, "mental": 9, "study": -5}, "내일을 위한 재충전이다."),
        ],
    },
    {
        "id": "sports",
        "emoji": "🏃",
        "title": "체육대회 작전 회의",
        "text": "우리 반이 단합할 절호의 기회! 어떤 역할을 맡을까?",
        "choices": [
            ("🎽 계주 선수에 도전한다", {"energy": -10, "mental": 11, "relation": 14}, "응원 소리에 힘이 솟았다!"),
            ("📣 열정적인 응원단이 된다", {"mental": 10, "relation": 16}, "목소리는 쉬었지만 추억은 남았다."),
            ("🧃 물과 간식을 챙기는 지원팀", {"relation": 18, "energy": -4}, "모두가 고맙다며 엄지를 들었다."),
        ],
    },
    {
        "id": "rain",
        "emoji": "☔",
        "title": "하교 시간 갑작스러운 비",
        "text": "우산은 하나인데 같은 방향인 친구가 곤란한 표정으로 서 있다.",
        "choices": [
            ("🌂 우산을 같이 쓴다", {"relation": 14, "mental": 7, "energy": -3}, "조금 젖었지만 즐거운 하굣길이었다."),
            ("🏫 비가 약해질 때까지 학교에서 공부한다", {"study": 11, "energy": -5}, "빗소리가 좋은 집중 음악이 되었다."),
            ("🚌 여분 우산이 있는지 먼저 알아본다", {"relation": 8, "study": 4}, "문제를 차분하게 해결했다."),
        ],
    },
    {
        "id": "festival",
        "emoji": "🎪",
        "title": "학교 축제 부스 준비",
        "text": "아이디어 회의가 길어지는데 마감은 다가온다. 이제 결정이 필요하다!",
        "choices": [
            ("💡 새로운 체험 부스를 제안한다", {"relation": 11, "mental": 9, "energy": -7}, "참신하다는 반응이 쏟아졌다."),
            ("🛠️ 실행 가능한 계획으로 정리한다", {"study": 8, "relation": 14}, "복잡했던 회의가 깔끔하게 끝났다."),
            ("🎨 안내판 디자인을 맡는다", {"mental": 12, "relation": 8, "energy": -5}, "복도가 귀여운 안내판으로 밝아졌다."),
        ],
    },
    {
        "id": "career",
        "emoji": "🧭",
        "title": "진로 고민이 찾아온 밤",
        "text": "잘하고 있는 걸까? 생각이 많아져 책장이 눈에 들어오지 않는다.",
        "choices": [
            ("🗒️ 지금까지 해낸 일을 적어 본다", {"mental": 14, "study": 4}, "생각보다 많이 성장했다는 걸 발견했다."),
            ("👩‍🏫 선생님께 상담을 신청한다", {"mental": 10, "relation": 8}, "막연했던 고민이 구체적인 질문으로 바뀌었다."),
            ("🚶 잠깐 산책하고 오늘 할 일에 집중한다", {"mental": 9, "energy": 8, "study": 5}, "한 걸음씩 가기로 했다."),
        ],
    },
    {
        "id": "late",
        "emoji": "⏰",
        "title": "아슬아슬한 등교",
        "text": "알람을 끄고 10분 더 자 버렸다! 지각까지 남은 시간은 단 15분.",
        "choices": [
            ("🚶 안전하게 서둘러 간다", {"energy": -5, "mental": -3}, "종 치기 직전에 교실 도착!"),
            ("📞 학교에 늦을 수 있다고 먼저 알린다", {"mental": 5, "relation": 4}, "솔직하게 알리고 침착하게 이동했다."),
            ("🎒 준비물을 다시 확인하고 출발한다", {"study": 4, "mental": 3, "energy": -4}, "늦을 뻔했지만 준비물은 완벽하다."),
        ],
    },
    {
        "id": "weekend",
        "emoji": "🌤️",
        "title": "기적 같은 한가한 주말",
        "text": "이번 주말에는 급한 일정이 없다. 무엇을 하며 보낼까?",
        "choices": [
            ("📚 다음 주 공부를 미리 해 둔다", {"study": 18, "mental": 3, "energy": -6}, "월요일의 내가 고마워할 선택이다."),
            ("😴 푹 쉬며 체력을 회복한다", {"energy": 23, "mental": 8}, "충전 게이지가 가득 찼다."),
            ("🧁 친구와 만나 즐겁게 논다", {"relation": 16, "mental": 13, "energy": 3}, "좋은 추억이 하나 더 생겼다."),
        ],
    },
]


def clamp(value):
    return max(0, min(100, int(round(value))))


def setup_state():
    defaults = {
        "page": "start",
        "turn": 0,
        "stats": {"study": 50, "energy": 55, "mental": 55, "relation": 50},
        "history": [],
        "inventory": ["🍪 행복 간식"],
        "used_items": [],
        "seen_events": [],
        "current_event": None,
        "message": "",
        "achievements": [],
        "late_count": 0,
        "group_help": 0,
        "assignment_power": 0,
        "profile": {},
        "ending_counts": {},
        "ending": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_game(keep_ranking=True):
    counts = st.session_state.get("ending_counts", {}) if keep_ranking else {}
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    setup_state()
    st.session_state.ending_counts = counts


def apply_delta(delta):
    adjusted = dict(delta)
    specialty = st.session_state.profile.get("specialty", "")
    if specialty == "🧘 멘탈 회복" and adjusted.get("mental", 0) < 0:
        adjusted["mental"] = int(round(adjusted["mental"] * 0.8))
    if specialty == "🗣️ 친구와 소통" and adjusted.get("relation", 0) > 0:
        adjusted["relation"] += 3
    for stat, change in adjusted.items():
        st.session_state.stats[stat] = clamp(st.session_state.stats[stat] + change)
    return adjusted


def format_delta(delta):
    parts = []
    for key, value in delta.items():
        emoji, label = STAT_INFO[key]
        sign = "+" if value >= 0 else ""
        parts.append(f"{emoji} {label} {sign}{value}")
    return " · ".join(parts)


def pick_event():
    available = [event for event in EVENTS if event["id"] not in st.session_state.seen_events]
    if not available:
        st.session_state.seen_events = []
        available = EVENTS[:]
    event = random.choice(available)
    st.session_state.current_event = event


def unlock_achievements():
    stats = st.session_state.stats
    history = st.session_state.history
    candidates = []
    if st.session_state.late_count == 0 and st.session_state.turn >= 8:
        candidates.append("⏰ 지각 0회")
    if st.session_state.group_help >= 2:
        candidates.append("🧩 조별 활동 캐리")
    if stats["study"] >= 90:
        candidates.append("📚 공부 게이지 MAX")
    if stats["relation"] >= 90:
        candidates.append("🫶 교실의 마당발")
    if stats["mental"] >= 85:
        candidates.append("🌈 흔들리지 않는 마음")
    if len(st.session_state.used_items) >= 3:
        candidates.append("🎒 아이템 활용의 달인")
    if len(history) >= 10 and min(stats.values()) >= 45:
        candidates.append("⚖️ 균형의 수호자")
    for achievement in candidates:
        if achievement not in st.session_state.achievements:
            st.session_state.achievements.append(achievement)


def reward_item():
    if st.session_state.turn in (4, 8, 12):
        candidates = [item for item in ITEMS if item not in st.session_state.inventory and item not in st.session_state.used_items]
        if candidates:
            item = random.choice(candidates)
            st.session_state.inventory.append(item)
            st.toast(f"🎁 새 아이템 획득: {item}")


def process_choice(index):
    event = st.session_state.current_event
    choice = event["choices"][index]
    label, delta, result = choice[0], dict(choice[1]), choice[2]

    if len(choice) == 4 and choice[3] == "teacher":
        if random.random() < 0.65:
            delta.update({"study": 12, "relation": 5})
            result = "선생님이 짧은 보완 시간을 주셨다! 솔직한 설명이 통했다."
        else:
            delta.update({"study": -8, "mental": -3})
            result = "기한은 그대로였다. 그래도 해야 할 일을 분명히 알게 됐다."

    if (
        st.session_state.profile.get("specialty") == "📝 수행평가 정리"
        and event["id"] == "assignment"
        and st.session_state.assignment_power == 0
        and delta.get("study", 0) > 0
    ):
        delta["study"] += 5
        st.session_state.assignment_power = 1
        result += " 특기 효과로 공부 +5!"

    applied = apply_delta(delta)
    st.session_state.turn += 1
    st.session_state.seen_events.append(event["id"])
    if event["id"] == "group":
        st.session_state.group_help += 1
    if event["id"] == "late" and index == 1:
        st.session_state.late_count += 1

    st.session_state.history.append(
        {
            "턴": st.session_state.turn,
            "사건": f'{event["emoji"]} {event["title"]}',
            "선택": label,
            "결과": result,
            **{STAT_INFO[k][1]: v for k, v in st.session_state.stats.items()},
        }
    )
    st.session_state.message = f"✨ {result}\n\n{format_delta(applied)}"
    unlock_achievements()
    reward_item()
    if min(st.session_state.stats.values()) <= 0:
        finish_game(early=True)
    elif st.session_state.turn >= MAX_TURNS:
        finish_game()
    else:
        pick_event()


def use_item(item):
    delta = dict(ITEMS[item]["delta"])
    if item == "😴 낮잠권" and st.session_state.profile.get("specialty") == "⚡ 초고속 낮잠":
        delta["energy"] += 10
    applied = apply_delta(delta)
    st.session_state.inventory.remove(item)
    st.session_state.used_items.append(item)
    st.session_state.message = f"🎒 {item} 사용 완료!\n\n{format_delta(applied)}"
    unlock_achievements()


def determine_ending(early=False):
    s = st.session_state.stats
    avg = sum(s.values()) / 4
    if early:
        return {
            "key": "재정비 엔딩",
            "emoji": "🌱",
            "title": "잠깐 멈추고 재정비!",
            "desc": "한 능력치가 바닥나 잠시 쉬어 가기로 했다. 고3 생활은 속도보다 지속 가능성이 중요하다.",
            "color": "#ccefdc",
        }
    if min(s.values()) >= 72:
        return {"key": "완벽한 계획형 인간", "emoji": "🏆", "title": "완벽한 계획형 인간", "desc": "공부도 관계도 건강하게 챙기며 졸업에 도착했다. 균형 감각이 최고의 능력!", "color": "#ffe59d"}
    if s["study"] >= 88 and s["energy"] <= 35:
        return {"key": "성적은 올랐지만 체력은 사라짐", "emoji": "📚", "title": "성적은 올랐지만 체력은 사라짐", "desc": "학업 성취는 눈부셨지만 충전이 필요하다. 다음 챕터의 첫 일정은 충분한 휴식!", "color": "#d9d5ff"}
    if s["relation"] >= 88:
        return {"key": "모두가 찾는 해결사", "emoji": "🤝", "title": "모두가 찾는 해결사", "desc": "조별 활동부터 반 행사까지 믿고 맡기는 사람으로 졸업했다.", "color": "#c8f1e8"}
    if s["energy"] >= 85 and s["study"] <= 45:
        return {"key": "학교에서 잠만 잔 전설", "emoji": "🛌", "title": "학교에서 잠만 잔 전설", "desc": "체력 관리는 완벽했다! 이제 충전한 에너지를 공부에도 조금 나눠 보자.", "color": "#cde5ff"}
    assignment_count = sum("수행평가" in row["사건"] for row in st.session_state.history)
    if s["study"] >= 75 or assignment_count >= 2:
        return {"key": "수행평가 불사조", "emoji": "🔥", "title": "수행평가 불사조", "desc": "마감이 다가올수록 집중력이 살아나는 전설적인 생존자!", "color": "#ffd3c5"}
    if s["mental"] >= 82:
        return {"key": "긍정 에너지 발전소", "emoji": "🌈", "title": "긍정 에너지 발전소", "desc": "예상치 못한 사건에도 나만의 속도를 지키며 졸업했다.", "color": "#ffd9ef"}
    if avg >= 60:
        return {"key": "균형 잡힌 생존왕", "emoji": "⚖️", "title": "균형 잡힌 생존왕", "desc": "완벽하지 않아도 매 순간 현실적인 선택으로 끝까지 완주했다.", "color": "#e5dcff"}
    return {"key": "우당탕탕 졸업 성공", "emoji": "🎓", "title": "우당탕탕 졸업 성공", "desc": "계획대로 되지 않은 날도 있었지만 결국 졸업식에 도착했다!", "color": "#ffdfec"}


def finish_game(early=False):
    ending = determine_ending(early)
    st.session_state.ending = ending
    st.session_state.ending_counts[ending["key"]] = st.session_state.ending_counts.get(ending["key"], 0) + 1
    st.session_state.page = "ending"
    st.balloons()


def stat_bar(key):
    emoji, label = STAT_INFO[key]
    value = st.session_state.stats[key]
    color = {"study": "#a88bf2", "energy": "#65d2b8", "mental": "#ff8bb8", "relation": "#69aef6"}[key]
    st.markdown(f'<div class="stat-label">{emoji} {label} <span style="float:right">{value}/100</span></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="height:13px;background:#eeeaf3;border-radius:99px;margin:.25rem 0 .72rem;overflow:hidden">'
        f'<div style="height:100%;width:{value}%;background:{color};border-radius:99px"></div></div>',
        unsafe_allow_html=True,
    )


def render_header():
    st.markdown(
        """
        <div class="hero">
          <div class="hero-title">🎮 고3 생존 시뮬레이터 🎓</div>
          <div class="hero-sub">📚 공부도 챙기고, 💪 체력도 지키고, 🌈 멘탈도 사수하자!</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_start():
    render_header()
    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.markdown("### 🪄 나의 캐릭터 만들기")
        with st.form("character_form"):
            name = st.text_input("이름 또는 별명", placeholder="예: 졸업하고싶은감자")
            grade = st.selectbox("학년", ["고등학교 3학년", "고등학교 2학년", "고등학교 1학년"])
            personality = st.selectbox("성격", list(PERSONALITIES.keys()))
            specialty = st.selectbox("특기", list(SPECIALTIES.keys()), help="각 특기는 플레이 중 한 가지 보너스를 줘요.")
            st.caption(f"✨ {SPECIALTIES[specialty]}")
            submitted = st.form_submit_button("🚀 학교생활 시작하기!", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.warning("캐릭터의 이름이나 별명을 입력해 주세요! 🐣")
                else:
                    reset_game()
                    st.session_state.profile = {
                        "name": name.strip(),
                        "grade": grade,
                        "personality": personality,
                        "specialty": specialty,
                    }
                    for key, bonus in PERSONALITIES[personality].items():
                        st.session_state.stats[key] = clamp(st.session_state.stats[key] + bonus)
                    st.session_state.history.append(
                        {
                            "턴": 0, "사건": "🎒 새 학기",
                            "선택": f"{personality} / {specialty}",
                            "결과": "두근두근 학교생활 시작!",
                            **{STAT_INFO[k][1]: v for k, v in st.session_state.stats.items()},
                        }
                    )
                    st.session_state.page = "game"
                    pick_event()
                    st.rerun()
    with right:
        st.markdown(
            """
            <div class="cute-card">
              <h3>🌸 게임 방법</h3>
              <p>① 총 <b>16개의 학교생활 사건</b>을 해결해요.</p>
              <p>② 선택에 따라 네 가지 능력치가 달라져요.</p>
              <p>③ 아이템과 특기를 알맞게 활용해요.</p>
              <p>④ 마지막 능력치와 기록으로 엔딩이 정해져요!</p>
            </div>
            <div class="cute-card">
              <h3>🎁 포함된 기능</h3>
              <span class="tag">🎲 랜덤 사건</span>
              <span class="tag">🎒 아이템</span>
              <span class="tag">🏅 업적</span>
              <span class="tag">📈 기록 그래프</span>
              <span class="tag">🎓 멀티 엔딩</span>
              <span class="tag">🪪 결과 카드</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar():
    p = st.session_state.profile
    with st.sidebar:
        st.markdown(f"## 🐣 {p['name']}")
        st.caption(f"{p['grade']} · {p['personality']}")
        st.markdown(f"**특기:** {p['specialty']}")
        st.divider()
        st.markdown(f"### 📅 졸업까지 {MAX_TURNS - st.session_state.turn}턴")
        st.progress(st.session_state.turn / MAX_TURNS)
        for key in STAT_INFO:
            stat_bar(key)
        st.divider()
        st.markdown("### 🎒 아이템")
        if not st.session_state.inventory:
            st.caption("지금은 가방이 비어 있어요 🫧")
        for item in list(st.session_state.inventory):
            st.caption(f"{item} · {ITEMS[item]['description']}")
            if st.button(f"{item} 사용", key=f"use_{item}", use_container_width=True):
                use_item(item)
                st.rerun()
        st.divider()
        if st.button("🔄 처음부터 다시 하기", use_container_width=True):
            reset_game()
            st.rerun()


def render_game():
    render_sidebar()
    render_header()
    if st.session_state.message:
        st.success(st.session_state.message)
        st.session_state.message = ""

    top1, top2, top3, top4 = st.columns(4)
    for col, key in zip((top1, top2, top3, top4), STAT_INFO):
        emoji, label = STAT_INFO[key]
        col.metric(f"{emoji} {label}", st.session_state.stats[key])

    event = st.session_state.current_event
    st.markdown(
        f"""
        <div class="event-card">
          <div class="tiny">📍 {st.session_state.turn + 1}번째 사건 / {MAX_TURNS}</div>
          <div class="event-title">{event['emoji']} {event['title']}</div>
          <p>{event['text']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 💭 어떻게 할까?")
    choices = event["choices"]
    cols = st.columns(2)
    for idx, choice in enumerate(choices):
        with cols[idx % 2]:
            if st.button(choice[0], key=f"choice_{st.session_state.turn}_{idx}", use_container_width=True):
                process_choice(idx)
                st.rerun()
            st.caption(f"예상 변화: {format_delta(choice[1])}")

    with st.expander("📈 지금까지의 생존 기록 보기"):
        if len(st.session_state.history) > 1:
            df = pd.DataFrame(st.session_state.history)
            st.line_chart(df.set_index("턴")[["공부", "체력", "멘탈", "인간관계"]], height=280)
            st.dataframe(df[["턴", "사건", "선택", "결과"]], use_container_width=True, hide_index=True)
        else:
            st.info("첫 선택을 하면 기록 그래프가 나타나요! ✨")

    with st.expander(f"🏅 획득 업적 {len(st.session_state.achievements)}개"):
        if st.session_state.achievements:
            st.write("　".join(st.session_state.achievements))
        else:
            st.caption("아직 획득한 업적이 없어요. 플레이를 계속해 보세요! 🌱")


def result_summary():
    s = st.session_state.stats
    best_key = max(s, key=s.get)
    weak_key = min(s, key=s.get)
    best = f"{STAT_INFO[best_key][0]} {STAT_INFO[best_key][1]}"
    weak = f"{STAT_INFO[weak_key][0]} {STAT_INFO[weak_key][1]}"
    return f"가장 빛난 능력은 {best}, 가장 많이 돌봄이 필요한 능력은 {weak}이에요."


def render_ending():
    render_header()
    ending = st.session_state.ending
    name = st.session_state.profile["name"]
    st.markdown(
        f"""
        <div class="ending-card" style="background:linear-gradient(135deg, {ending['color']}, #fff)">
          <div class="ending-emoji">{ending['emoji']}</div>
          <div class="tiny">2026 고3 생존 결과 카드 · {datetime.now().strftime('%Y.%m.%d')}</div>
          <div class="ending-title">{ending['title']}</div>
          <h3>{name}의 졸업 엔딩</h3>
          <p>{ending['desc']}</p>
          <p><b>{result_summary()}</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📊 최종 능력치")
    cols = st.columns(4)
    for col, key in zip(cols, STAT_INFO):
        emoji, label = STAT_INFO[key]
        col.metric(f"{emoji} {label}", st.session_state.stats[key])

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("### 🏅 획득 업적")
        if st.session_state.achievements:
            for achievement in st.session_state.achievements:
                st.markdown(f"- {achievement}")
        else:
            st.caption("이번에는 숨은 업적을 찾지 못했어요. 다음 플레이에서 도전! 🔎")
    with right:
        st.markdown("### 🏆 엔딩 도감")
        counts = st.session_state.ending_counts
        total = sum(counts.values())
        for title, count in sorted(counts.items(), key=lambda x: -x[1]):
            st.write(f"**{title}** · {count}회 ({count / total * 100:.1f}%)")
        st.caption("비율은 현재 앱 실행 세션의 플레이 기록을 기준으로 계산돼요.")

    with st.expander("📜 나의 전체 선택 기록"):
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "💾 플레이 기록 CSV로 저장",
        data=pd.DataFrame(st.session_state.history).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{name}_고3생존기록.csv",
        mime="text/csv",
        use_container_width=True,
    )
    if st.button("🔁 다른 선택으로 다시 플레이", use_container_width=True):
        reset_game()
        st.rerun()


setup_state()
if st.session_state.page == "start":
    render_start()
elif st.session_state.page == "game":
    render_game()
else:
    render_ending()
