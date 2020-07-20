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
    data = Category.query.all()
    categories = {}
    for category in data:
      categories[category.id] = category.type

    if len(data) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'categories': categories
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
    # get all questions and paginate
    selection = Question.query.all()
    total_questions = len(selection)
    current_questions = paginate_questions(request, selection)

    # get all categories
    categories = Category.query.all()
    categories_dict = {}
    for category in categories:
        categories_dict[category.id] = category.type

    # abort 404 if no questions
    if (len(current_questions) == 0):
        abort(404)

    # return data to view
    return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': total_questions,
        'categories': categories_dict
    })

  '''
  @Done: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:id>', methods=['GET','DELETE'])
  def delete_question(id):
    #delete the question with specified question id

    try:
      question = Question.query.get(id)

      if question is None:
        abort(404)

      question.delete()
      
      return jsonify({
        'success': True,
        'deleted': id
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
    data = request.get_json()

    new_question = data.get('question', None)
    insert_answer = data.get('answer', None)
    insert_category = data.get('category', None)
    insert_difficulty = data.get('difficulty', None)

    if (new_question is None) or (insert_answer is None) or (insert_category is None) or (insert_difficulty is None):
      abort(422)

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
      abort(500)

  '''
  @Done: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start.
  '''
  @app.route('/questions/search', methods=['GET','POST'])
  def search_questions():
    #search related question with input string

    data = request.get_json()

    search_term =data.get('searchTerm', '')

    if search_term is None:
      abort(422)

    try:
      related_questions = Question.query.filter(Question.question.ilike('%{}%'.format(search_term))).all()
      
      if related_questions is None:
        return jsonify({
          'success': True,
          'message': "Question not found"
        })

      output = paginate_questions(request, related_questions)

      return jsonify({
        'success': True,
        'questions': output,
        'total_questions': len(related_questions),
        'current_category': None
      })
    except:
      abort(422)

  '''
  @Done: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:id>/questions', methods=['GET'])
  def get_question_by_category(id):
    category = Category.query.get(id)
    if (category is None):
      abort(404)

    try:
      questions = Question.query.filter_by(category=category.id).all()
      
      current_questions = paginate_questions(request, questions)

      return jsonify({
        'success': True,
        'questions': current_questions,
        'current_category': category.type,
        'total_questions': len(questions)
      })
    except:
      abort(500)

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
  @app.route('/quizzes', methods=['POST'])
  def get_a_quiz_question():
    #given category id and ids of previous questions', output a random question

    data = request.get_json()

    category = data.get('quiz_category', '')
    previous_questions = data.get('previous_questions', '')

    try: 
      #if user selected a category
      if category['id'] != 0:
        questions = Question.query.filter_by(category=category['id']).all()
      #if user selected "All"
      else:
        questions = Question.query.all()

      length = len(questions)
      def get_random_question():
        return questions[random.randrange(0, length)]

      next_question = get_random_question()
      
      found = True
      while found:
        if next_question in previous_questions:
          return get_random_question()
        else:
          found = False
      return jsonify({
      'success': True,
      'question': next_question.format()
      })
    except:
      abort(500)

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
    