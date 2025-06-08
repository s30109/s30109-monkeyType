import os
import random
from datetime import datetime, UTC
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from flask import render_template


load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret')


mongo = PyMongo()
mongo.init_app(app)


with open('words.txt', 'r') as f:
    WORDS = [line.strip() for line in f if line.strip()]


#logika

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/game')
def game():
    random_words = random.sample(WORDS, 30)
    return jsonify({"words": random_words})

@app.route("/submit", methods=['POST'])
def submit():
    data = request.json
    username = data.get("username")
    typed_words = data.get("typed_words", [])
    expected_words = data.get("expected_words", [])
    time_taken = data.get("time", 30)

    correct = 0
    total_chars = 0
    for i, word in enumerate(typed_words):
        if i < len(expected_words) and word == expected_words[i]:
            correct += 1
        total_chars += len(word)

    wpm = round((total_chars / 5) / (time_taken / 60), 2)
    accuracy = round((correct / len(typed_words)) * 100, 2) if typed_words else 0.0



    user = mongo.db.users.find_one({"username": username})
    if not user:
        user_id = mongo.db.users.insert_one({"username": username}).inserted_id
    else:
        user_id = user["_id"]

    mongo.db.results.insert_one({
        "user_id": user_id,
        "username": username,
        "wpm": wpm,
        "accuracy": accuracy,
        "correct": correct,
        "total_words": len(typed_words),
        "timestamp": datetime.now(UTC)
    })

    return jsonify({"status": "ok", "wpm": wpm, "accuracy": accuracy})

# Global highscores (top 10 WPM)
@app.route("/highscores")
def highscores():
    scores = list(mongo.db.results.find({}, {"_id": 0, "username": 1, "wpm": 1, "accuracy": 1})
                  .sort("wpm", -1).limit(10))
    return jsonify(scores)

@app.route("/my_highscores")
def my_highscores():
    username = request.args.get('username')
    if not username:
        return jsonify([])
    scores = list(mongo.db.results.find({"username": username}, {"_id": 0, "username": 1, "wpm": 1, "accuracy": 1})
                  .sort("wpm", -1).limit(10))
    return jsonify(scores)

if __name__ == '__main__':
    app.run(debug=True)