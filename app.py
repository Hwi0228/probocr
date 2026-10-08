from flask import Flask, render_template

app = Flask(__name__, template_folder="static/templates")

NAV_SECTIONS = [
    {
        "label": None,
        "items": [
            {"icon": "⌂", "label": "홈"},
            {"icon": "▣", "label": "문제 상점"},
        ],
    },
    {
        "label": "문제 관리",
        "items": [
            {"icon": "⇧", "label": "문제 DB 등록"},
            {"icon": "▤", "label": "문제 DB", "active": True, "count": "2.2만문항"},
            {"icon": "▧", "label": "문제지"},
            {"icon": "✧", "label": "AI 변형문제"},
            {"icon": "⌕", "label": "출처 분석"},
        ],
    },
    {
        "label": "학습 관리",
        "items": [
            {"icon": "♙", "label": "학생 관리"},
            {"icon": "♧", "label": "클래스 관리"},
            {"icon": "✓", "label": "오답 학습"},
        ],
    },
]

BOTTOM_NAV_ITEMS = [
    {"icon": "▱", "label": "크레딧", "count": "0"},
    {"icon": "⚙", "label": "설정"},
    {"icon": "☏", "label": "채팅 문의"},
]

SUBJECTS = ["수학", "과학", "국어", "영어", "사회", "기타"]
FREE_FOLDERS = ["모의고사/수능", "경찰대/사관학교", "중등 수학"]
PERSONAL_FOLDERS = [
    "미분류",
    "광희중학교 2025학년도 2학기 중간고사",
    "광희중학교 2025학년도 2학기 기말고사",
]
DIFFICULTIES = [
    {"label": "하", "count": 1, "total": 842},
    {"label": "중", "count": 4, "total": 3132},
    {"label": "중상", "count": 11, "total": 8920},
    {"label": "상", "count": 3, "total": 2170},
    {"label": "최상", "count": 1, "total": 415},
]
POINT_VALUES = [2, 3, 4]
SCHOOL_LEVELS = [
    {"label": "중등", "count": "7,748"},
    {"label": "고등", "count": "7,803"},
    {"label": "확률과 통계", "count": "2,306", "nested": True},
]

QUESTIONS = [
    {
        "subject": "수학",
        "type": "객관식",
        "points": 2,
        "prompt": "세 개의 숫자 1, 2, 3 중에서 중복을 허락하여 4개를 택해 일렬로 나열하는 경우의 수는?",
        "choices": ["54", "63", "72", "81", "96"],
        "difficulty": "하",
        "difficulty_score": 1,
        "topic": "확률과 통계",
        "keyword": "문자를 나열하는 중복순열",
        "year": 23,
        "page": 1,
        "source": "(2026년 시행) 2027학년도 수능",
    },
    {
        "subject": "수학",
        "type": "객관식",
        "points": 3,
        "prompt": "다항식 (x² + a)(x + 2)⁵의 전개식에서 x⁴의 계수가 10일 때, 상수 a의 값은?",
        "choices": ["−9", "−8", "−7", "−6", "−5"],
        "difficulty": "중상",
        "difficulty_score": 5,
        "topic": "확률과 통계",
        "keyword": "(a + b)(c + d)의 전개",
        "year": 24,
        "page": 1,
        "source": "(2026년 시행) 2027학년도 수능",
    },
    {
        "subject": "수학",
        "type": "객관식",
        "points": 3,
        "prompt": "2개의 동전과 2개의 주사위를 동시에 던질 때, 2개의 동전 모두 앞면이 나오거나 2개의 주사위 중 한 개의 주사위 눈의 수만 3의 배수일 확률은?",
        "choices": ["17/36", "1/2", "5/8"],
        "difficulty": "중상",
        "difficulty_score": 5,
        "topic": "확률과 통계",
        "keyword": "배반사건이 아닌 확률",
        "year": 25,
        "page": 2,
        "source": "(2026년 시행) 2027학년도 수능",
    },
    {
        "subject": "수학",
        "type": "객관식",
        "points": 3,
        "prompt": "평균이 m이고 표준편차가 20인 정규분포를 따르는 모집단에서 크기가 196인 표본을 임의추출하여 얻은 표본평균이 a일 때, 모평균 m에 대한 신뢰도 95%의 신뢰구간이 a ≤ m ≤ 76.5이다. a + m의 값은? 단, P(|Z| ≤ 1.96) = 0.95로 계산한다.",
        "choices": ["132", "140"],
        "difficulty": "중상",
        "difficulty_score": 5,
        "topic": "확률과 통계",
        "keyword": "모평균의 신뢰구간 이용하기",
        "year": 26,
        "page": 3,
        "source": "(2026년 시행) 2027학년도 수능",
    },
]


@app.route("/")
def main():
    return render_template(
        "main.html",
        nav_sections=NAV_SECTIONS,
        bottom_nav_items=BOTTOM_NAV_ITEMS,
        subjects=SUBJECTS,
        selected_subject="수학",
        free_folders=FREE_FOLDERS,
        personal_folders=PERSONAL_FOLDERS,
        result_count=15551,
        sort_options=["출처순", "최신순", "난이도순"],
        questions=QUESTIONS,
        difficulties=DIFFICULTIES,
        point_values=POINT_VALUES,
        school_levels=SCHOOL_LEVELS,
    )


if __name__ == "__main__":
  app.run(debug=True)
