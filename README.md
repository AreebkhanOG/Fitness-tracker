# FitTrack - Simple Fitness Tracker

A beginner-friendly fitness tracking website made with:

- HTML
- CSS
- JavaScript
- Python Flask
- SQLite

## Features

- Enter your name, age, height, and weight
- Automatic BMI calculation
- Daily water tracker from 0/8 to 8/8 glasses
- Steps, active minutes, and calories tracking
- Weight updates and progress chart
- Motivational quotes
- Dark blue and black gradient interface
- Data saved locally in SQLite

## Project structure

```text
fittrack_project/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── welcome.html
│   └── dashboard.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

The `fitness.db` database file will be created automatically when you run the project.

## How to run it

### 1. Open a terminal inside the project folder

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Linux / macOS:

```bash
python3 -m venv venv
```

### 3. Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

### 4. Install Flask

```bash
pip install -r requirements.txt
```

### 5. Start the website

```bash
python app.py
```

On some Linux systems use:

```bash
python3 app.py
```

### 6. Open it in your browser

```text
http://127.0.0.1:5000
```

That's it. Everything runs locally on your computer.
