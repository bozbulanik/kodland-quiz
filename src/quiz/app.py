from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, QuizResult, Question
from datetime import datetime
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'key'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.before_request
def set_user():
    if 'user_id' not in session:
        user = User()
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
    else:
        user = User.query.get(session['user_id'])
        if user is None:
            user = User()
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            
@app.context_processor
def inject_scores():
    scores = {
        'overall_highest': db.session.query(db.func.max(QuizResult.score)).scalar() or 0,
        'user_highest': 0
    }
    
    if 'user_id' in session:
        user_highest = db.session.query(db.func.max(QuizResult.score))\
            .filter_by(user_id=session['user_id']).scalar()
        scores['user_highest'] = user_highest or 0
    
    return scores

@app.route('/')
def index():
    user = User.query.get(session['user_id'])
    if user is None:
        return redirect(url_for('set_user'))
        
    questions = Question.query.all()
    max_questions = 15
    selected_questions = Question.query.order_by(func.random()).limit(max_questions).all()
    
    formatted_questions = [
        {
            'enumerated_id': i + 1,
            'id': str(q.id),
            'question': q.text,
            'options': {
                'a': q.option_a,
                'b': q.option_b,
                'c': q.option_c,
                'd': q.option_d
            },
            'correct': q.correct_option
        } for i, q in enumerate(selected_questions)
    ]
    return render_template('index.html', questions=formatted_questions, current_username=user.username)

@app.route('/submit', methods=['POST'])
def submit():
    user = User.query.get(session['user_id'])
    if user is None:
        return redirect(url_for('index'))

    new_username = request.form.get('username')
    if new_username and new_username != user.username:
        user.username = new_username
        db.session.commit()
        
    questions = Question.query.all()
    correct_answers = {str(q.id): q.correct_option for q in questions}

    score = sum(1 for qid in correct_answers if request.form.get(qid) == correct_answers[qid])
    score = int((score / len(correct_answers)) * 100) if correct_answers else 0

    new_result = QuizResult(
        user_id = session['user_id'],
        score=score
    )
    db.session.add(new_result)
    db.session.commit()

    return redirect(url_for('result', score=score))

@app.route('/result')
def result():
    score = request.args.get('score', type=int)
    user = User.query.get(session['user_id'])
    return render_template('result.html', score=score, username=user.username)

if __name__ == '__main__':
    app.run(debug=True)
