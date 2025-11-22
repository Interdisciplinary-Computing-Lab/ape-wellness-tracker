# Ape Diet & Wellness Tracker App
A full-stack diet and wellness tracking app for Ape Initiative, built with Flask, HTML5, Bootstrap 4, Chart.js, and SQLite.

## 🔧 Project Status

✅ Core Backend and Authentication Implemented  
✅ Frontend Integration and Styling Completed  
✅ Prototype Ready - Professional UI/UX  

🚧 Production Configuration Needed  
📌 Deployment Setup and Final Testing Pending

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ape-wellness-tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   The database will be automatically created in the `instance/` folder when you first run the app. However, if you want to explicitly initialize it:
   ```bash
   python init_db.py
   ```

4. **Run the application**
   ```bash
   python run.py
   ```
   
   The app will be available at `http://localhost:5003`

### First Time Setup

After starting the app for the first time, you may want to:
- Create an admin user: `python create_admin.py`
- Create a test user: `python create_user.py`
- Seed sample data: `python seed_data.py`

## 🗂 Project Structure

This app uses Flask to serve both backend logic and frontend UI. All app code lives inside the `backend/` folder, while the database and configuration files live in the `instance/` folder.
```
ape-wellness-tracker/
├── backend/                 # Flask app logic and structure
│   ├── __init__.py          # App factory that initializes Flask
│   ├── routes/              # Flask route handlers (views)
│   ├── templates/           # HTML templates rendered by Flask
│   ├── static/              # CSS, JS, and image assets
│   ├── models/              # Database models
│   └── forms/               # Form classes using Flask-WTF
│
├── instance/                # Instance-specific files (created automatically)
│   └── database.db          # SQLite database file
│
├── run.py                   # Main entry point to start the Flask app
├── init_db.py               # Database initialization script
├── requirements.txt         # Python dependencies
