from flask_security import Security, SQLAlchemyUserDatastore
from backend.extensions import db
from backend.models.entry import User, Role

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()

def init_security(app):
    """Initialize Flask-Security with minimal configuration"""
    security.init_app(app, user_datastore)
    
    # Only essential configurations - let Flask-Security handle the rest
    app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
    app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = False
    app.config['SECURITY_SEND_PASSWORD_RESET_EMAIL'] = False
    
    # Custom templates for better user experience
    app.config['SECURITY_UNAUTHORIZED_VIEW'] = 'security.forbidden'