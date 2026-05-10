"""
app.py
------
Main Flask server for the Online Quiz & Examination System.

This file handles:
  1. Serving the frontend HTML pages
  2. Accepting PDF uploads from the user
  3. Extracting text from the uploaded PDF
  4. Generating quiz questions from that text using simple NLP logic
  5. Returning the quiz as a JSON response

We keep it intentionally simple — no database, no user accounts.
Everything happens in memory during a single session.
"""

import os
import re
import json
import random
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Try to import PyPDF2 for PDF reading
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("WARNING: PyPDF2 not installed. PDF upload will use dummy text.")

app = Flask(__name__, static_folder="frontend", static_url_path="")

# -------------------------
# Configuration
# -------------------------
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
MAX_QUESTIONS = 10      # Maximum questions we'll generate per quiz
MIN_SENTENCE_LEN = 40   # Sentences shorter than this are ignored for questions

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB max upload size


# -------------------------
# Helper: Check file type
# -------------------------
def allowed_file(filename):
    """Returns True if the file has a .pdf extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------------
# Helper: Extract text from PDF
# -------------------------
def extract_text_from_pdf(filepath):
    """
    Opens a PDF file and extracts all readable text from it.
    Returns the raw text as a single string.
    
    PyPDF2 reads PDFs page by page — we loop through and collect all text.
    """
    if not PDF_SUPPORT:
        # Fallback dummy text for testing without a real PDF
        return """
        Python is a high-level programming language that is widely used in web development.
        Machine learning is a subset of artificial intelligence that uses statistical techniques.
        Data structures are specialized formats for organizing, processing, and storing data.
        Algorithms are step-by-step procedures for solving computational problems efficiently.
        Object-oriented programming is a paradigm based on the concept of objects and classes.
        The Internet is a global network connecting millions of computers worldwide.
        Databases store and manage structured collections of data for applications.
        Operating systems manage computer hardware and software resources for users.
        Networking involves transmitting data between computers over communication channels.
        Cybersecurity protects computer systems and networks from digital attacks and damage.
        """

    text = ""
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


# -------------------------
# Helper: Clean and split text into sentences
# -------------------------
def get_sentences(text):
    """
    Splits raw text into individual sentences.
    Filters out very short sentences (headers, page numbers, etc.)
    that are not useful for generating questions.
    """
    # Split on '. ', '! ', '? ' (basic sentence boundary detection)
    raw = re.split(r'(?<=[.!?])\s+', text)
    sentences = []
    for s in raw:
        s = s.strip()
        # Only keep sentences that are long enough and contain real words
        if len(s) >= MIN_SENTENCE_LEN and re.search(r'[a-zA-Z]{4,}', s):
            sentences.append(s)
    return sentences


# -------------------------
# Helper: Generate True/False questions
# -------------------------
def generate_true_false(sentences):
    """
    Given a list of sentences from the PDF, creates True/False questions.
    
    Strategy:
      - For TRUE questions: use a sentence directly as a statement
      - For FALSE questions: pick a sentence and swap a key word with a 
        random word from a different sentence to make it incorrect
    
    This is a very basic approach — good enough to demonstrate the concept!
    In a real system you'd use an NLP model like spaCy or transformers.
    """
    questions = []
    # Grab up to 20 random sentences to work with
    pool = random.sample(sentences, min(20, len(sentences)))

    for i, sentence in enumerate(pool):
        if len(questions) >= MAX_QUESTIONS:
            break

        # Decide randomly: make it a TRUE or FALSE question
        is_true = random.random() > 0.4  # Slightly more TRUE questions

        if is_true:
            questions.append({
                "type": "true_false",
                "question": f"True or False: {sentence.rstrip('.')}.",
                "answer": "True",
                "explanation": "This statement is directly supported by the document."
            })
        else:
            # Create a FALSE version by replacing a noun/word with something else
            words = sentence.split()
            if len(words) < 6:
                continue

            # Pick a random word from a DIFFERENT sentence to swap in
            other_sentences = [s for s in pool if s != sentence]
            if not other_sentences:
                continue
            other_words = random.choice(other_sentences).split()
            if not other_words:
                continue

            # Replace a random word in the middle of the sentence
            swap_idx = random.randint(2, len(words) - 2)
            swap_word = random.choice(other_words)
            words[swap_idx] = swap_word
            false_sentence = " ".join(words)

            questions.append({
                "type": "true_false",
                "question": f"True or False: {false_sentence.rstrip('.')}.",
                "answer": "False",
                "explanation": f"The original text states: '{sentence}'"
            })

    return questions


# -------------------------
# Helper: Generate MCQ questions
# -------------------------
def generate_mcq(sentences):
    """
    Creates multiple-choice questions from the sentences.
    
    Strategy:
      - Pick a sentence and blank out a key word (the 'answer')
      - Generate 3 wrong options by picking words from other sentences
      - Shuffle all 4 options so the correct one isn't always first
    
    Again — basic but demonstrates the idea clearly for a portfolio project.
    """
    questions = []
    pool = random.sample(sentences, min(20, len(sentences)))

    for sentence in pool:
        if len(questions) >= MAX_QUESTIONS:
            break

        words = sentence.split()
        # Only work with sentences that have enough words
        if len(words) < 8:
            continue

        # Pick a "key word" to blank out (avoid short words like 'a', 'the', 'is')
        candidates = [
            (idx, w) for idx, w in enumerate(words)
            if len(w) > 4 and w.isalpha() and idx > 1
        ]
        if not candidates:
            continue

        blank_idx, correct_word = random.choice(candidates)

        # Create the question by replacing the word with "______"
        blanked = words.copy()
        blanked[blank_idx] = "______"
        question_text = " ".join(blanked)

        # Gather wrong options from other sentences
        other_sentences = [s for s in pool if s != sentence]
        wrong_words = set()
        for other in other_sentences:
            for w in other.split():
                if len(w) > 4 and w.isalpha() and w.lower() != correct_word.lower():
                    wrong_words.add(w)
            if len(wrong_words) >= 3:
                break

        if len(wrong_words) < 3:
            continue

        wrong_options = random.sample(list(wrong_words), 3)
        options = wrong_options + [correct_word]
        random.shuffle(options)

        questions.append({
            "type": "mcq",
            "question": f"Fill in the blank: {question_text}",
            "options": options,
            "answer": correct_word,
            "explanation": f"The complete sentence reads: '{sentence}'"
        })

    return questions


# ============================
# ROUTES
# ============================

@app.route("/")
def index():
    """Serve the main landing/upload page."""
    return send_from_directory("frontend", "index.html")


@app.route("/quiz")
def quiz_page():
    """Serve the quiz taking page."""
    return send_from_directory("frontend", "quiz.html")


@app.route("/results")
def results_page():
    """Serve the results page."""
    return send_from_directory("frontend", "results.html")


@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    """
    API endpoint: Accepts a PDF upload and returns generated quiz questions.
    
    Steps:
    1. Validate the uploaded file
    2. Save it to the uploads/ folder
    3. Extract text from the PDF
    4. Generate a mix of MCQ and True/False questions
    5. Return the questions as JSON
    """
    if "pdf" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["pdf"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    # Save the file safely (secure_filename prevents path traversal attacks)
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Extract text
    text = extract_text_from_pdf(filepath)
    if not text.strip():
        return jsonify({"error": "Could not extract text from PDF. Try a text-based PDF."}), 422

    # Get sentences
    sentences = get_sentences(text)
    if len(sentences) < 5:
        return jsonify({"error": "PDF has too little readable text to generate questions."}), 422

    # Generate questions: half MCQ, half True/False
    random.shuffle(sentences)
    half = len(sentences) // 2
    mcq_questions = generate_mcq(sentences[:half])
    tf_questions = generate_true_false(sentences[half:])

    # Mix and cap at MAX_QUESTIONS total
    all_questions = mcq_questions[:5] + tf_questions[:5]
    random.shuffle(all_questions)
    all_questions = all_questions[:MAX_QUESTIONS]

    # Add question numbers
    for i, q in enumerate(all_questions):
        q["id"] = i + 1

    return jsonify({
        "success": True,
        "total": len(all_questions),
        "questions": all_questions,
        "filename": filename
    })


@app.route("/api/submit", methods=["POST"])
def submit_quiz():
    """
    API endpoint: Accepts submitted answers and returns the score.
    
    Expects JSON body:
    {
      "questions": [...],   // original questions with answers
      "responses": {        // user's answers, keyed by question id
        "1": "True",
        "2": "Python",
        ...
      }
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    questions = data.get("questions", [])
    responses = data.get("responses", {})
    violations = data.get("violations", 0)

    score = 0
    results = []

    for q in questions:
        qid = str(q["id"])
        user_answer = responses.get(qid, "")
        correct = q["answer"]
        is_correct = user_answer.strip().lower() == correct.strip().lower()

        if is_correct:
            score += 1

        results.append({
            "id": q["id"],
            "question": q["question"],
            "user_answer": user_answer,
            "correct_answer": correct,
            "is_correct": is_correct,
            "explanation": q.get("explanation", "")
        })

    total = len(questions)
    percentage = round((score / total) * 100) if total > 0 else 0

    # Proctoring note: penalise for tab switches (1 point per violation, max 3)
    penalty = min(violations, 3)
    final_score = max(0, score - penalty)
    final_percentage = round((final_score / total) * 100) if total > 0 else 0

    return jsonify({
        "score": final_score,
        "raw_score": score,
        "total": total,
        "percentage": final_percentage,
        "violations": violations,
        "penalty": penalty,
        "results": results
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
