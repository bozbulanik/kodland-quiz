from models import db, Question
from app import app
import json

data = []

with open("questions.json", 'r', encoding='utf-8') as file:
    data = json.load(file)

questions_list = []
for q in data['questions']:
    question = Question(
        text=q['question_text'],
        option_a=q['options']['a'],
        option_b=q['options']['b'],
        option_c=q['options']['c'],
        option_d=q['options']['d'],
        correct_option=q['answer']
    )
    questions_list.append(question)


with app.app_context():
    db.create_all()
    db.session.bulk_save_objects(questions_list)
    db.session.commit()
