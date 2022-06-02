import os
from turtle import title
import unittest
import json
from flask_sqlalchemy import SQLAlchemy


from flaskr import create_app, QUESTIONS_PER_PAGE
from models import setup_db, database_user, Question


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = os.environ["DATABASE_NAME_TEST"]
        self.database_password = os.environ["DATABASE_PASSWORD"]
        self.database_path = "postgresql://{}:{}@{}/{}".format(
            database_user, self.database_password, "localhost:5432", self.database_name
        )
        setup_db(self.app, self.database_path)
        self.new_question = {
            "question": "Test question",
            "answer": "Test answer",
            "difficulty": 5,
            "category": 4
        }
        self.new_question_422 = {
            "answer": "Test answer",
            "category": 4
        }

        self.search = {
            "searchTerm": "title"
        }

        self.quiz_422 = {
            "quiz_category": {},
            "previous_questions": {}
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['categories']), data['total_categories'])
        self.assertTrue(data['categories'])
        self.assertTrue(data['total_categories'])

    def test_get_paginated_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['questions']), QUESTIONS_PER_PAGE)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
    
    def test_404_beyond_valid_page(self):
        res = self.client().get('/questions?page=100')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Resource Not Found')

    def test_delete_question(self):
        question = Question.query.first()
        question = question.format()
        res = self.client().delete(f"/questions/{question['id']}")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["deleted"], question['id'])
        self.assertTrue(data["questions"])
        self.assertTrue(data["total_questions"])

    def test_404_not_found_delete_question(self):
        res = self.client().delete("/questions/1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Resource Not Found")

    def test_create_question(self):
        res = self.client().post("/questions", json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 201)
        self.assertEqual(data["success"], True)
        self.assertTrue(data['created'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])

    def test_422_unprocessable_create_question(self):
        res = self.client().post("/questions", json=self.new_question_422)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data['message'], "unprocessable")
        self.assertTrue(data['error'])
    
    def test_search_questions(self):
            res = self.client().post("/questions", json=self.search)
            data = json.loads(res.data)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(data["success"], True)
            self.assertTrue(data['questions'])
            self.assertTrue(data['total_questions'])
    
    def test_retrieve_category_questions(self):
        res = self.client().get("/categories/1/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['current_category'], "Science")
        self.assertEqual(data["success"], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])

    def test_404_not_found_retrieve_category_questions(self):
        res = self.client().get("/categories/100/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Resource Not Found")

    def test_retrieve_quizzes(self):
        quiz = {
            "quiz_category": {"id": 1, "type": "Science"},
            "previous_questions": [20, 21]
        }
        res = self.client().post("/quizzes", json=quiz)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['question'])
        self.assertNotEqual(data['question']['id'], 20)
        self.assertNotEqual(data['question']['id'], 21)
    
    def test_422_unprocessable_retrieving_quizzes(self):
        res = self.client().post("/quizzes", json=self.quiz_422)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data['message'], "unprocessable")
        self.assertTrue(data['error'])


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()