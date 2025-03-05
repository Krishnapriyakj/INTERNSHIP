import json

def load_ncd_questions():
    with open("data/ncd_questions.json", "r") as f:
        return json.load(f)

def load_ncd_risks_recommendations():
    with open("data/ncd_risks_recommendations.json", "r") as f:
        return json.load(f)

ncd_questions = load_ncd_questions()
ncd_risks_recommendations = load_ncd_risks_recommendations()
