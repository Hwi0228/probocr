import json
import os
import sqlite3
from pathlib import Path

from flask import Flask, current_app, g, redirect, render_template, request, url_for

app = Flask(__name__, template_folder="static/templates")
app.config["DATABASE"] = os.path.join(app.instance_path, "probocr.sqlite3")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

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
            {"icon": "⇧", "label": "문제 DB 등록", "endpoint": "new_question"},
            {"icon": "▤", "label": "문제 DB", "active": True, "endpoint": "main"},
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
    {"icon": "▱", "label": "크레딧"},
    {"icon": "⚙", "label": "설정"},
    {"icon": "☏", "label": "채팅 문의"},
]

SUBJECTS = ["수학", "과학", "국어", "영어", "사회", "기타"]
QUESTION_TYPES = ["객관식", "주관식"]
DIFFICULTIES = ["하", "중", "중상", "상", "최상"]
POINT_VALUES = [2, 3, 4]

SCHEMA = """
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    question_type TEXT NOT NULL,
    points INTEGER NOT NULL CHECK (points > 0),
    prompt TEXT NOT NULL,
    choices TEXT NOT NULL,
    difficulty TEXT,
    topic TEXT NOT NULL DEFAULT '',
    keyword TEXT NOT NULL DEFAULT '',
    year INTEGER,
    page INTEGER,
    source TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def get_db():
    if "db" not in g:
        database = current_app.config["DATABASE"]
        Path(database).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        connection.executescript(SCHEMA)
        g.db = connection
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def render_question_form(form_data=None, errors=None, status=200):
    return (
        render_template(
            "question_form.html",
            nav_sections=NAV_SECTIONS,
            bottom_nav_items=BOTTOM_NAV_ITEMS,
            subjects=SUBJECTS,
            question_types=QUESTION_TYPES,
            difficulties=DIFFICULTIES,
            form_data=form_data or {},
            errors=errors or [],
        ),
        status,
    )


@app.route("/")
def main():
    rows = get_db().execute(
        """
        SELECT id, subject, question_type, points, prompt, choices, difficulty,
               topic, keyword, year, page, source
        FROM questions
        ORDER BY id DESC
        """
    ).fetchall()
    questions = []
    for row in rows:
        question = dict(row)
        question["choices"] = json.loads(question["choices"])
        questions.append(question)

    return render_template(
        "main.html",
        nav_sections=NAV_SECTIONS,
        bottom_nav_items=BOTTOM_NAV_ITEMS,
        subjects=SUBJECTS,
        selected_subject="수학",
        user_folders=[],
        questions=questions,
        point_values=POINT_VALUES,
        added=request.args.get("added") == "1",
    )


@app.route("/questions/new", methods=["GET", "POST"])
def new_question():
    if request.method == "GET":
        return render_question_form()

    form_data = request.form
    errors = []
    subject = form_data.get("subject", "").strip()
    question_type = form_data.get("question_type", "").strip()
    prompt = form_data.get("prompt", "").strip()
    difficulty = form_data.get("difficulty", "").strip()
    topic = form_data.get("topic", "").strip()
    keyword = form_data.get("keyword", "").strip()
    source = form_data.get("source", "").strip()
    choices = [choice.strip() for choice in form_data.get("choices", "").splitlines()]
    choices = [choice for choice in choices if choice]

    if subject not in SUBJECTS:
        errors.append("과목을 선택해 주세요.")
    if question_type not in QUESTION_TYPES:
        errors.append("문제 유형을 선택해 주세요.")
    if not prompt:
        errors.append("문제 내용을 입력해 주세요.")
    if len(prompt) > 10000:
        errors.append("문제 내용은 10,000자 이내로 입력해 주세요.")
    if question_type == "객관식" and len(choices) < 2:
        errors.append("객관식 문제의 선택지를 2개 이상 입력해 주세요.")
    if question_type == "주관식" and choices:
        errors.append("주관식 문제는 선택지를 비워 두세요.")
    if len(choices) > 5:
        errors.append("선택지는 5개 이하로 입력해 주세요.")
    if difficulty and difficulty not in DIFFICULTIES:
        errors.append("난이도를 목록에서 선택해 주세요.")

    try:
        points = int(form_data.get("points", ""))
        if not 1 <= points <= 100:
            raise ValueError
    except ValueError:
        points = 0
        errors.append("배점은 1에서 100 사이의 정수로 입력해 주세요.")

    optional_numbers = {}
    for field, label, maximum in (
        ("year", "연도", 2200),
        ("page", "페이지", 10000),
    ):
        value = form_data.get(field, "").strip()
        if not value:
            optional_numbers[field] = None
            continue
        try:
            number = int(value)
            if not 1 <= number <= maximum:
                raise ValueError
        except ValueError:
            errors.append(f"{label}는 1에서 {maximum} 사이의 정수로 입력해 주세요.")
            optional_numbers[field] = None
        else:
            optional_numbers[field] = number

    for value, label, maximum in (
        (topic, "단원", 200),
        (keyword, "유형", 200),
        (source, "출처", 300),
    ):
        if len(value) > maximum:
            errors.append(f"{label}은 {maximum}자 이내로 입력해 주세요.")

    if errors:
        return render_question_form(form_data, errors, 400)

    get_db().execute(
        """
        INSERT INTO questions (
            subject, question_type, points, prompt, choices, difficulty,
            topic, keyword, year, page, source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            subject,
            question_type,
            points,
            prompt,
            json.dumps(choices, ensure_ascii=False),
            difficulty or None,
            topic,
            keyword,
            optional_numbers["year"],
            optional_numbers["page"],
            source,
        ),
    )
    get_db().commit()
    return redirect(url_for("main", added=1))


if __name__ == "__main__":
    app.run(debug=True)
