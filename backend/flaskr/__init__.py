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

def generate_valid_random_number(selection):
    num = random.randint(0 , len(selection) - 1)
    return num

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
        except:
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
            'total_questions': len(questions_selection),
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

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', '')
        new_answer = body.get('answer', '')
        new_category = body.get('category', 1)
        new_difficulty = body.get('difficulty', 1)
        search_term = body.get('searchTerm', None)

        if (new_question == '' or new_answer == '') and search_term is None:
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

    @app.route('/categories/<int:category_id>/questions')
    def retrieve_category_questions(category_id):
        try:
            category = Category.query.filter(Category.id == category_id).one_or_none()

            if category is None:
                abort(404)

            questions_selection = Question.query.order_by(Question.id).filter(Question.category == category_id).all()
            questions = paginate_questions(request, questions_selection)

            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(questions_selection),
                'current_category': category.type
            })
        except:
            abort(404)


    @app.route("/quizzes", methods=["POST"])
    def retrieve_quizzes():
        body = request.get_json()
        quiz_category = body.get('quiz_category')
        previous_questions = body.get('previous_questions')
        random_question = None

        try:
            if quiz_category is None or quiz_category['id'] == 0:
                valid_questions_selection = [question.format() for question in Question.query.all()]
            else:
                valid_questions_selection = [question.format() for question in Question.query.filter(Question.category == quiz_category['id']).all()]
                        
            valid_questions = []
            for question in valid_questions_selection:
                if question['id'] not in previous_questions:
                    valid_questions.append(question)
                
            if (len(valid_questions) > 0):
                random_question = random.choice(valid_questions)
                    
            return jsonify({
                'success': True,
                'question': random_question,
                'previous_questions': previous_questions
            })   
        except:
            abort(422)



# ERROR HANDLERS
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

    @app.errorhandler(500)
    def bad_request(error):
        return (jsonify({"success": False, "error": 500, "message": "Internal server error"}), 500)

    return app

