import os
import random
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for

from _classes import CardList

app = Flask(__name__)
app.secret_key = "examtopics-quiz-web"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RES_DIR = os.path.join(BASE_DIR, "res")
WRONG_ANSWERS_DIR = os.path.join(BASE_DIR, "wrong_answers")
os.makedirs(WRONG_ANSWERS_DIR, exist_ok=True)


def normalize_answer(answer: str) -> str:
    cleaned = "".join(ch for ch in str(answer or "").upper() if ch.isalpha())
    return "".join(sorted(set(cleaned)))


def build_quiz(question_count: int):
    cards = CardList(RES_DIR).cards_list
    if not cards:
        return []

    chosen_count = max(1, min(question_count or len(cards), len(cards)))
    quiz_cards = cards[:]
    random.shuffle(quiz_cards)
    return quiz_cards[:chosen_count]


def serialize_card(card):
    return {
        "question_number": card.question_number,
        "question": card.question,
        "answers": list(card.answers),
        "correct_answer": card.correct_answer,
    }


def write_wrong_answers_file(wrong_answers):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(WRONG_ANSWERS_DIR, f"wrong_answers_{timestamp}.txt")

    with open(filename, "w", encoding="utf-8") as wrong_file:
        for item in wrong_answers:
            wrong_file.write(f"{item['question_number']} {item['question']}\n")
            wrong_file.write("-" * 40 + "\n")
            for answer in item["answers"]:
                wrong_file.write(f"{answer}\n")
            wrong_file.write(f"Your answer: {item['submitted_answer']}\n")
            wrong_file.write(f"Correct answer: {item['correct_answer']}\n")
            wrong_file.write("-" * 40 + "\n\n")

    return filename


@app.route("/")
def index():
    total_questions = len(CardList(RES_DIR).cards_list) if os.path.isdir(RES_DIR) else 0
    return render_template("index.html", total_questions=total_questions)


@app.route("/start", methods=["POST"])
def start_quiz():
    question_count = int(request.form.get("question_count", 0) or 0)
    show_answer_immediately = request.form.get("show_immediately", "y").lower() == "y"

    cards = build_quiz(question_count)
    if not cards:
        return redirect(url_for("index"))

    session["cards"] = [serialize_card(card) for card in cards]
    session["current_index"] = 0
    session["score"] = 0
    session["wrong_answers"] = []
    session["show_answer_immediately"] = show_answer_immediately
    session["results_written"] = False
    session["last_result"] = None

    return redirect(url_for("quiz"))


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "cards" not in session:
        return redirect(url_for("index"))

    cards = session["cards"]
    index = session.get("current_index", 0)
    total_questions = len(cards)

    if request.method == "POST":
        action = request.form.get("action")

        if action in {"prev", "next"}:
            if action == "next" and index < total_questions - 1:
                session["current_index"] = index + 1
            elif action == "prev" and index > 0:
                session["current_index"] = index - 1

            session.pop("last_result", None)
            return redirect(url_for("quiz"))

        card = cards[index]
        selected_answers = request.form.getlist("answer")
        submitted = normalize_answer("".join(selected_answers))
        correct_answer = normalize_answer(card["correct_answer"])
        is_correct = submitted == correct_answer

        if is_correct:
            session["score"] = session.get("score", 0) + 1
        else:
            session["wrong_answers"].append({
                "question_number": card["question_number"],
                "question": card["question"],
                "answers": card["answers"],
                "submitted_answer": submitted or "(none)",
                "correct_answer": card["correct_answer"],
            })

        session["last_result"] = {
            "correct": is_correct,
            "submitted": submitted or "(none)",
            "correct_answer": card["correct_answer"],
        }

        return render_template(
            "question.html",
            card=card,
            index=index + 1,
            total=total_questions,
            show_answer_immediately=session.get("show_answer_immediately", True),
            last_result=session["last_result"],
        )

    card = cards[index]
    last_result = session.get("last_result")
    return render_template(
        "question.html",
        card=card,
        index=index + 1,
        total=total_questions,
        show_answer_immediately=session.get("show_answer_immediately", True),
        last_result=last_result,
    )


@app.route("/results")
def results():
    if "cards" not in session:
        return redirect(url_for("index"))

    if not session.get("results_written"):
        wrong_file = write_wrong_answers_file(session.get("wrong_answers", []))
        session["results_written"] = True
        session["wrong_file"] = wrong_file

    score = session.get("score", 0)
    total = len(session.get("cards", []))
    wrong_answers = session.get("wrong_answers", [])
    wrong_file = session.get("wrong_file")

    return render_template(
        "results.html",
        score=score,
        total=total,
        wrong_answers=wrong_answers,
        wrong_file=wrong_file,
    )


@app.route("/reset")
def reset_quiz():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
