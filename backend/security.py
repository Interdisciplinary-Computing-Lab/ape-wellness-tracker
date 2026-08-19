from flask import request, session
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.signals import user_registered
from backend.extensions import db
from backend.models.entry import User, Role
from backend.utils.password_policy import AppPasswordUtil
from datetime import datetime

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()

def init_security(app):
    """Initialize Flask-Security with minimal configuration"""
    security.init_app(app, user_datastore, password_util_cls=AppPasswordUtil)
    
    # Only essential configurations - let Flask-Security handle the rest
    app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
    app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = False
    app.config['SECURITY_SEND_PASSWORD_RESET_EMAIL'] = False
    
    # Disable email confirmation requirement - auto-confirm users on registration
    app.config['SECURITY_CONFIRMABLE'] = False

    # Registration validates deliverability by default; disable DNS/MX checks for staff emails
    app.config['SECURITY_EMAIL_VALIDATOR_ARGS'] = {'check_deliverability': False}
    
    # Redirect after login
    app.config['SECURITY_POST_LOGIN_VIEW'] = '/dashboard'
    app.config['SECURITY_POST_LOGOUT_VIEW'] = '/'
    app.config['SECURITY_POST_REGISTER_VIEW'] = '/dashboard'
    
    # Custom templates for better user experience
    app.config['SECURITY_UNAUTHORIZED_VIEW'] = 'security.forbidden'

    @app.after_request
    def _discard_flashes_after_login_page(response):
        """Login shows no banners; discard flashes so they do not appear here or after sign-in."""
        if request.endpoint == 'security.login' and app.secret_key:
            session.pop('_flashes', None)
        return response

    # Register signal handler to auto-confirm and ensure user is saved
    @user_registered.connect_via(app)
    def on_user_registered(sender, user, confirm_token, **extra):
        """Auto-confirm user and ensure they are active and saved to database"""
        try:
            # Auto-confirm the user (set confirmed_at timestamp)
            # Flask-Security should handle this when SECURITY_CONFIRMABLE=False,
            # but we ensure it's set explicitly
            if not user.confirmed_at:
                user.confirmed_at = datetime.utcnow()
            user.active = True
            
            # Ensure the user is saved to the database
            # The user should already be in the session from Flask-Security,
            # but we ensure changes are committed
            db.session.commit()
            
            # Assign Researcher by default when optional registration is enabled
            researcher = Role.query.filter_by(name='Researcher').first()
            if researcher and researcher not in user.roles:
                user.roles.append(researcher)
                db.session.commit()

            print(f"[SUCCESS] User '{user.email}' registered and confirmed successfully")
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Failed to confirm user '{user.email}': {e}")
            # Re-raise to prevent silent failures
            raise
