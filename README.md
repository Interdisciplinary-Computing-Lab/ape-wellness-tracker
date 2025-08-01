# Ape Diet & Wellness Tracker App
A full-stack diet and wellness tracking app for Ape Initiative, built with Flask, HTML5, Bootstrap 4, Chart.js, and SQLite.

## 🔧 Project Status

✅ Core Backend and Authentication Implemented  
✅ Frontend Integration and Styling Completed  
✅ Prototype Ready - Professional UI/UX  

🚧 Production Configuration Needed  
📌 Deployment Setup and Final Testing Pending

## 🗂 Project Structure

This app uses Flask to serve both backend logic and frontend UI. All app code lives inside the `backend/` folder, while the database and configuration files live at the root level.
```
ape-wellness-tracker/
├── backend/                 # Flask app logic and structure
│   ├── init.py              # App factory that initializes Flask
│   ├── routes/              # Flask route handlers (views)
│   ├── templates/           # HTML templates rendered by Flask
│   ├── static/              # CSS, JS, and image assets
│   ├── models/              # Database models
│   └── forms/               # Form classes using Flask-WTF
│
├── data/                    # SQLite database and Superset config
│   └── app.db               # SQLite DB file
│
├── run.py                   # Main entry point to start the Flask app
├── requirements.txt         # Python dependencies
