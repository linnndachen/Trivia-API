import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
def paginate_questions(request, questions):
  page = request.args.get('page', 1, type=int)
  start = (page-1) * QUESTIONS_PER_PAGE
  end = start+QUESTIONS_PER_PAGE 
  
  format_questions = [question.format() for question in questions]
  current_questions = format_questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @Done: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={"/": {"origins": "*"}})

  '''
  @Done: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PATCH, PUT, POST, DELETE, OPTIONS')
    return response

  '''
  @Done: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():
    #get all the categories
    categories = Category.query.all()
    data = {}
    for category in categories:
      data[category.id] = category.type

    if len(data) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'categories': data
    })

  '''
  @Done: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def get_questions():
    #get all the questions but display only 10 for each page

    all_questions = Question.query.all()
    current_questions = paginate_questions(request, all_questions)

    if len(current_questions) == 0:
      abort(404)
    
    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(all_questions)
    })

  '''
  @Done: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    #delete the question with specified question id

    try:
      question = Question.query.filter(Question.id==question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()

      all_questions = Question.query.all()
      current_questions = paginate_questions(request, all_questions)
      
      return jsonify({
        'success': True,
        'deleted': question_id,
        'questions': current_questions,
        'total_questions': len(all_questions)
      })
    except:
      abort(422)

  '''
  @Done: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()

    new_question = body.get('question', None)
    insert_answer = body.get('answer', None)
    insert_category = body.get('category', None)
    insert_difficulty = body.get('difficulty', None)

    if new_question|insert_answer|insert_category|insert_difficulty is None:
      return jsonify({
        'success': False,
        'message': "missing inormation"
      })

    try: 
      question = Question(
        question = new_question,
        answer = insert_answer,
        category=insert_category,
        difficulty=insert_difficulty
      )

      question.insert()
    
      all_questions = Question.query.all()
      current_questions = paginate_questions(request, all_questions)

      return jsonify({
        'success': True,
        'created': question.id,
        'questions': current_questions,
        'total_questions': len(all_questions)
      })
    except:
      abort(422)

  '''
  @Done: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start.
  '''
  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    #search related question with input string

    data = request.get_json()
    search_term =data.get('search', '')

    related_questions = Question.query.filter(Question.question.ilike('%{}%'.format(search_term))).all()

    if len(related_questions) == 0:
      return jsonify('question not found.')

    output = paginate_questions(request, related_questions)

    return jsonify({
      'success': True,
      'questions': output,
      'total_questions': len(Question.query.all())
    })

  '''
  @Done: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_question_by_category(category_id):
    questions = Category.query.filter(Question.category==category_id).all()

    if questions is None:
      abort(404)
    
    current_questions = paginate_questions(request, questions)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'category': category_id,
      'total_questions': len(Question.query.all())
    })

  '''
  @Done: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['GET'])
  def get_a_random_question():
    #given category id and ids of previous questions', output a random question

    data = request.get_json()

    category = data.get('quizCategory', '')
    previous_questions = data.get('previousQuestions', '')

    #if user selected a category
    if category:
      try: 
        questions = Question.query.filter(Question.category == category.id).all()
      except:
        return abort(500)
    #if user selected "All"
    else:
      questions = Question.query.all()

    all_questions = len(questions)

    if len(previous_questions)==all_questions:
      return jsonify({
        'success': True,
        'message': 'You have tried all the questions'
      })
      
    def get_random_question():
      return questions[random.randrange(0, len(questions), 1)]
    
    def check_if_used(question):
      used=False
      for q in previous_questions:
        if (q==question.id):
          used = True
      return used
    
    try:
      question = get_random_question()

      while (check_if_used(question)):
        question = get_random_question()

        return jsonify({
          'success': True,
          'question': question.format()
        })
        
    except:
      abort(422)

  '''
  @Done: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success': False,
      'error': 400,
      'message': 'Bad request'
    })

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': 'Resource not found. Input out of range.'
    })

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      'error': 422, 
      'message': 'unprocessable. Synax error.'
    })

  @app.errorhandler(500)
  def internal_server(error):
    return jsonify({
      'success': False,
      'error': 500, 
      'message': 'Sorry, the falut is us not you. Please try again later.'
    })

  return app

#if __name__ == 'main':
    #app.run


"""   if __name__ == '__main__':
      port = int(os.environ.get('PORT', 5000))
      app.run(host='0.0.0.0', port=port) """
    