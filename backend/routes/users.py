"""
User profile management routes for the Ape Wellness Tracker application.
"""

from flask import render_template, request, redirect, url_for, flash
from backend.extensions import db
from backend.models.entry import User
from flask_security import login_required, current_user, login_user
from flask_security.utils import hash_password, verify_password
from backend.security import user_datastore
from backend.routes import site


@site.route('/user_profile')
@login_required
def user_profile():
    """Display user profile page"""
    # Calculate user statistics
    total_meals = len(current_user.meals)
    
    # Calculate unique active days
    unique_dates = set()
    for meal in current_user.meals:
        unique_dates.add(meal.date.date())  # Use date() to get just the date part
    active_days = len(unique_dates)
    
    return render_template('user_profile.html', 
                         user=current_user,
                         total_meals=total_meals,
                         active_days=active_days)


@site.route('/user_profile/update', methods=['POST'])
@login_required
def update_profile():
    """Handle profile information updates"""
    try:
        new_email = request.form.get('email', '').strip()
        
        if not new_email:
            flash('Email address is required.', 'error')
            return redirect(url_for('site.user_profile'))
        
        # Check if email is different from current
        if new_email != current_user.email:
            # Check if email already exists
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != current_user.id:
                flash('This email address is already in use.', 'error')
                return redirect(url_for('site.user_profile'))
            
            # Update email
            current_user.email = new_email
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        else:
            flash('No changes were made.', 'info')
        
        return redirect(url_for('site.user_profile'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {str(e)}', 'error')
        return redirect(url_for('site.user_profile'))


def _password_change_redirect(**params):
    return redirect(url_for('site.user_profile', **params))


@site.route('/user_profile/change_password', methods=['POST'])
@login_required
def change_password():
    """Handle password change requests"""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        user = user_datastore.find_user(id=current_user.id)
        if not user:
            return _password_change_redirect(password_error='account')

        if not all([current_password, new_password, confirm_password]):
            return _password_change_redirect(password_error='required')

        if new_password != confirm_password:
            return _password_change_redirect(password_error='mismatch')

        from backend.utils.password_policy import validate_password
        policy_errors = validate_password(new_password)
        if policy_errors:
            return _password_change_redirect(
                password_error='policy',
                password_error_detail='; '.join(policy_errors),
            )

        if not verify_password(current_password, user.password):
            return _password_change_redirect(password_error='incorrect')

        user.password = hash_password(new_password)
        db.session.commit()
        login_user(user)

        return _password_change_redirect(password_changed=1)

    except Exception as e:
        db.session.rollback()
        return _password_change_redirect(password_error='server', password_error_detail=str(e))


@site.route('/forbidden')
@login_required
def forbidden():
    """Custom forbidden page with navigation options"""
    return render_template('security/forbidden.html')

