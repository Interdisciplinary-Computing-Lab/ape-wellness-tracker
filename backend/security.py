from flask_security import Security, SQLAlchemyUserDatastore
from backend.extensions import db
from backend.models.entry import User, Role

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()

def init_security(app):
    """Initialize Flask-Security with custom configuration"""
    security.init_app(app, user_datastore)
    
    # Configure security settings
    app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'security/login_user.html'
    app.config['SECURITY_REGISTER_USER_TEMPLATE'] = 'security/register_user.html'
    app.config['SECURITY_FORGOT_PASSWORD_TEMPLATE'] = 'security/forgot_password.html'
    app.config['SECURITY_RESET_PASSWORD_TEMPLATE'] = 'security/reset_password.html'
    app.config['SECURITY_CHANGE_PASSWORD_TEMPLATE'] = 'security/change_password.html'
    app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = False
    app.config['SECURITY_SEND_PASSWORD_RESET_EMAIL'] = False
    app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
    
    # Enable forgot password functionality
    app.config['SECURITY_RECOVERABLE'] = True
    app.config['SECURITY_RESETABLE'] = True