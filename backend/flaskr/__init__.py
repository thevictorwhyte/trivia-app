import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    paginated_questions = questions[start:end]
    return paginated_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type, Authorization"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @app.route('/categories')
    def retrieve_categories():
        try:
            categories = Category.query.order_by(Category.id).all()
            return jsonify({
                'categories': {category.id:category.type for category in categories},
                'success': True,
                'total_categories': len(categories)
            }) 
        except Exception as e:
            print(e)
            abort(404)


    @app.route('/questions')
    def retrieve_questions():
        questions_selection = Question.query.order_by(Question.id).all()
        categories_selection = Category.query.order_by(Category.id).all()
        questions = paginate_questions(request, questions_selection)

        if len(questions) == 0:
            abort(404)
        
        return jsonify({
            'success': True,
            'questions': questions,
            'categories': {category.id:category.type for category in categories_selection},
            'total_questions': len(questions),
            'current_category': categories_selection[0].type
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            questions_selection = Question.query.order_by(Question.id).all()
            questions = paginate_questions(request, questions_selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': questions,
                'total_questions': len(questions_selection)
            })  
        except:
            db.session.rollback()
            abort(404)
        finally:
            db.session.close()

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        search_term = body.get('search', None)

        if new_question is None and search_term is None:
            abort(422)

        try:
            if search_term:
                questions_selection = Question.query.order_by(Question.id).filter(Question.question.ilike("%{}%".format(search_term))).all()
                questions = paginate_questions(request, questions_selection)

                return jsonify({
                    'success': True,
                    'questions': questions,
                    'total_questions': len(questions_selection)
                })
            else:
                question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
                question.insert()

                questions_selection = Question.query.order_by(Question.id).all()
                questions = paginate_questions(request, questions_selection)

                return jsonify({
                    'success': True,
                    'created': question.id,
                    'questions': questions,
                    'total_questions': len(questions_selection)
                }), 201
        except:
            db.session.rollback()
            abort(422)
        finally:
            db.session.close()

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "Resource Not Found"}),
            404
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (jsonify({"success": False, "error": 422, "message": "unprocessable"}), 422)
    
    @app.errorhandler(400)
    def bad_request(error):
        return (jsonify({"success": False, "error": 400, "message": "bad request"}), 400)

    return app

