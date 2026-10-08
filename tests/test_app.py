import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import app


class QuestionRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_directory.name) / "questions.sqlite3"
        app.config.update(TESTING=True, DATABASE=str(self.database))
        self.client = app.test_client()

    def tearDown(self):
        self.temp_directory.cleanup()

    def valid_question(self, **overrides):
        form = {
            "subject": "수학",
            "question_type": "객관식",
            "points": "3",
            "difficulty": "중상",
            "prompt": "문제 본문",
            "choices": "첫 번째\n두 번째\n세 번째",
            "topic": "확률과 통계",
            "keyword": "순열",
            "year": "2026",
            "page": "12",
            "source": "테스트 출처",
        }
        form.update(overrides)
        return form

    def test_empty_database_shows_no_fake_questions_or_count(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("표시할 문제가 없습니다.".encode(), response.data)
        self.assertNotIn(b"15,551", response.data)
        self.assertNotIn(b'class="result-count"', response.data)
        self.assertNotIn("광희중학교".encode(), response.data)
        self.assertTrue(self.database.exists())

    def test_registration_form_is_reachable_from_the_sidebar(self):
        database_response = self.client.get("/")
        form_response = self.client.get("/questions/new")

        self.assertEqual(database_response.status_code, 200)
        self.assertIn(b'href="/questions/new"', database_response.data)
        self.assertEqual(form_response.status_code, 200)
        self.assertIn('name="prompt"'.encode(), form_response.data)
        self.assertIn("문제 저장".encode(), form_response.data)

    def test_question_is_stored_and_shown_with_actual_count(self):
        response = self.client.post(
            "/questions/new",
            data=self.valid_question(),
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("문제를 등록했습니다.".encode(), response.data)
        self.assertIn('class="result-count">1</span>'.encode(), response.data)
        self.assertIn("문제 본문".encode(), response.data)

        connection = sqlite3.connect(self.database)
        try:
            row = connection.execute(
                """
                SELECT subject, question_type, points, prompt, choices,
                       difficulty, topic, keyword, year, page, source
                FROM questions
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(row[:4], ("수학", "객관식", 3, "문제 본문"))
        self.assertEqual(json.loads(row[4]), ["첫 번째", "두 번째", "세 번째"])
        self.assertEqual(row[5:], ("중상", "확률과 통계", "순열", 2026, 12, "테스트 출처"))

    def test_invalid_multiple_choice_is_not_saved(self):
        response = self.client.post(
            "/questions/new",
            data=self.valid_question(choices="선택지 하나"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("선택지를 2개 이상".encode(), response.data)
        self.assertFalse(self.database.exists())

    def test_subjective_question_can_be_registered_without_choices(self):
        response = self.client.post(
            "/questions/new",
            data=self.valid_question(question_type="주관식", choices=""),
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("문제 본문".encode(), response.data)
        connection = sqlite3.connect(self.database)
        try:
            choices = connection.execute("SELECT choices FROM questions").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(json.loads(choices), [])

    def test_question_text_is_html_escaped(self):
        self.client.post(
            "/questions/new",
            data=self.valid_question(prompt="<script>alert(1)</script>"),
        )

        response = self.client.get("/")
        self.assertIn(b"&lt;script&gt;alert(1)&lt;/script&gt;", response.data)
        self.assertNotIn(b"<script>alert(1)</script>", response.data)


if __name__ == "__main__":
    unittest.main()
