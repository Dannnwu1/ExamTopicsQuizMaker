import unittest

from app import app


class AppWebTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_homepage_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ExamTopics Quiz", response.data)

    def test_start_route_starts_quiz(self):
        response = self.client.post("/start", data={"question_count": 1, "show_immediately": "y"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/quiz", response.headers["Location"])

    def test_answer_reveals_result_on_same_question_page(self):
        self.client.post("/start", data={"question_count": 2, "show_immediately": "y"})
        response = self.client.post("/quiz", data={"answer": ["A"]})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Correct answer:", response.data)
        self.assertIn(b"Next question", response.data)


if __name__ == "__main__":
    unittest.main()
