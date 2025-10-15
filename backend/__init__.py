from flask import Flask
import os
from backend.extensions import db
from backend.security import init_security
from backend.routes.main import site
from backend.helpers import get_time_period_display

def create_app():
    app = Flask(__name__, instance_relative_config=True, static_folder='static', static_url_path='/static')

    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Ensure SQLite DB path resolves to the instance directory for cross-OS consistency
    db_path = os.path.join(app.instance_path, 'database.db').replace('\\', '/')
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "super-secret-key"
    app.config["SECURITY_PASSWORD_SALT"] = "super-salty-salt"
    app.config["SECURITY_PASSWORD_HASH"] = "bcrypt"
    app.config["SECURITY_REGISTERABLE"] = True
    app.config["SECURITY_SEND_REGISTER_EMAIL"] = False


    db.init_app(app)
    init_security(app)

    app.register_blueprint(site)
    
    # Add helper functions to template context
    @app.context_processor
    def utility_processor():
        return dict(get_time_period_display=get_time_period_display)

    with app.app_context():
        db.create_all()
        
        # Ensure standard apes exist when app starts
        ensure_standard_apes()

    return app

def ensure_standard_apes():
    """Ensure all standard apes exist in the database"""
    from backend.models.entry import Apes
    from datetime import date
    
    standard_apes = [
        {
            'ape_name': 'MAISHA',
            'birthday': date(2000, 5, 28),
            'weight': 42.5,
            'mother': 'Matata',
            'image_filename': 'maisha.jpg'
        },
        {
            'ape_name': 'TECO',
            'birthday': date(2010, 6, 1),
            'weight': 38.2,
            'mother': None,
            'image_filename': 'teco.jpg'
        },
        {
            'ape_name': 'NYOTA',
            'birthday': date(1998, 4, 4),
            'weight': 45.8,
            'mother': None,
            'image_filename': 'nyota.jpg'
        },
        {
            'ape_name': 'CLARA',
            'birthday': date(2010, 5, 27),
            'weight': 39.1,
            'mother': None,
            'image_filename': 'clara.jpg'
        },
        {
            'ape_name': 'MALI',
            'birthday': date(2007, 9, 4),
            'weight': 41.3,
            'mother': None,
            'image_filename': 'mali.jpg'
        },
        {
            'ape_name': 'ELIKYA',
            'birthday': date(1997, 6, 28),
            'weight': 44.7,
            'mother': 'Matata',
            'image_filename': 'elikya.jpg'
        }
    ]
    
    created_count = 0
    for ape_data in standard_apes:
        existing_ape = Apes.query.filter_by(ape_name=ape_data['ape_name']).first()
        if not existing_ape:
            new_ape = Apes(**ape_data)
            db.session.add(new_ape)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f"✅ Created {created_count} standard apes for new users")