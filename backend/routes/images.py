"""
Image upload and serving routes for the Ape Wellness Tracker application.
"""

from flask import send_file, redirect, url_for, flash
from backend.extensions import db
from backend.models.entry import Apes, DEFAULT_APE_IMAGE
from backend.utils.file_utils import allowed_file, MAX_FILE_SIZE
from flask_security import login_required
from backend.utils.authz import ape_manage_required
from werkzeug.utils import secure_filename
from backend.routes import site
import io
import os


@site.route('/ape/<int:ape_id>/image')
@login_required
def ape_image(ape_id):
    """Serve ape image from BLOB data"""
    try:
        ape = Apes.query.get_or_404(ape_id)
        
        if ape.image_data and ape.image_mime_type:
            return send_file(
                io.BytesIO(ape.image_data),
                mimetype=ape.image_mime_type,
                as_attachment=False
            )
        else:
            # Fallback to static file if no BLOB data
            return redirect(url_for('static', filename=DEFAULT_APE_IMAGE))
    except Exception:
        return redirect(url_for('static', filename=DEFAULT_APE_IMAGE))


@site.route('/ape/<int:ape_id>/upload_image', methods=['POST'])
@login_required
@ape_manage_required
def upload_ape_image(ape_id):
    """Upload image for an ape"""
    from flask import request
    
    try:
        ape = Apes.query.get_or_404(ape_id)
        
        # Check if file was uploaded
        if 'image' not in request.files:
            flash('No image file selected', 'error')
            return redirect(url_for('site.ape_profile_page', ape_id=ape_id))
        
        file = request.files['image']
        
        # Check if file is empty
        if file.filename == '':
            flash('No image file selected', 'error')
            return redirect(url_for('site.ape_profile_page', ape_id=ape_id))
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            flash('Image file is too large. Maximum size is 5MB.', 'error')
            return redirect(url_for('site.ape_profile_page', ape_id=ape_id))
        
        # Check file extension
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload a PNG, JPG, JPEG, GIF, or WebP image.', 'error')
            return redirect(url_for('site.ape_profile_page', ape_id=ape_id))
        
        # Read file data
        image_data = file.read()
        mime_type = file.content_type or 'image/jpeg'
        
        # Update ape record with image data
        ape.image_data = image_data
        ape.image_mime_type = mime_type
        
        # Also update filename for backward compatibility
        filename = secure_filename(f"{ape.ape_name.lower().replace(' ', '_')}.jpg")
        ape.image_filename = filename
        
        db.session.commit()
        
        flash(f'Image uploaded successfully for {ape.ape_name}!', 'success')
        return redirect(url_for('site.ape_profile_page', ape_id=ape_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error uploading image: {str(e)}', 'error')
        return redirect(url_for('site.ape_profile_page', ape_id=ape_id))


@site.route('/ape/<int:ape_id>/remove_image', methods=['POST'])
@login_required
def remove_ape_image(ape_id):
    """Remove image from an ape"""
    try:
        ape = Apes.query.get_or_404(ape_id)
        
        # Clear image data
        ape.image_data = None
        ape.image_mime_type = None
        ape.image_filename = None
        
        db.session.commit()
        
        flash(f'Image removed successfully for {ape.ape_name}', 'success')
        return redirect(url_for('site.edit_ape', ape_id=ape_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing image: {str(e)}', 'error')
        return redirect(url_for('site.edit_ape', ape_id=ape_id))

