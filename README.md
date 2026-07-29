# Online Quiz & Proctored Examination System

This is a web-based quiz application built using Python, Flask, HTML, CSS, and JavaScript.

The project allows users to upload a PDF and generate quiz questions from its content. It also includes basic proctoring-related features like tab-switch detection and fullscreen warnings during the quiz.

I built this project to learn:

* Flask backend development
* handling file uploads
* working with PDFs in Python
* REST APIs
* frontend-backend interaction
* basic exam monitoring features

---

## Features

* Upload PDF files
* Generate MCQ and True/False questions
* Quiz timer
* Automatic score calculation
* Tab-switch detection
* Fullscreen warning during quiz
* Result page with score and answer review

---

## Tech Used

### Backend

* Python
* Flask
* PyPDF2

### Frontend

* HTML
* CSS
* JavaScript

---

## Project Structure

```text
quiz-exam-system/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── uploads/
│
└── frontend/
    ├── index.html
    ├── quiz.html
    ├── results.html
    │
    ├── css/
    └── js/
```

---

## Setup

### Clone the repository

```bash
git clone https://github.com/harsh25120/quiz-exam-system.git
cd quiz-exam-system
```

### Create virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## Run the project

```bash
python app.py
```

Then open:

```text
http://localhost:5000
```

in your browser.

---

## Notes

* The project works best with text-based PDFs.
* Question generation is rule-based and intentionally simple.
* Uploaded PDFs are stored temporarily in the uploads folder.

---

## Future Improvements

* Better NLP-based question generation
* User login system
* Database support
* Export results as PDF
* More advanced proctoring features

---

## Author

Harsh Dwivedi