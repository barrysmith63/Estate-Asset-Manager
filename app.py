"""
Estate Asset Manager - Flask Application
Optimized with connection pooling, pagination, and caching
"""
from flask import Flask, render_template, request, redirect, jsonify
from functools import wraps
import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename

from config import Config
from db import init_db_pool, execute_query, execute_procedure, DatabaseContextManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize database pool
if not init_db_pool():
    logger.warning("Failed to initialize database pool at startup")


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def validate_request_data(required_fields):
    """Decorator to validate required POST data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            for field in required_fields:
                if field not in request.form:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/')
def index():
    """Home page"""
    return redirect('/videos')


@app.route('/videos')
def videos_page():
    """Videos listing page"""
    return render_template('videos.html')


@app.route('/videos/data', methods=['GET'])
def videos_data():
    """API endpoint to fetch videos with pagination
    
    Query Parameters:
        - archived: '0' (default, active) or '1' (archived)
        - page: Page number (default 1)
        - per_page: Items per page (default from config)
        - search: Search term for title/description
    """
    try:
        show_archived = request.args.get('archived', '0') == '1'
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, int(request.args.get('per_page', Config.ITEMS_PER_PAGE)))
        search_term = request.args.get('search', '').strip()
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Build query
        if show_archived:
            view_name = 'v_video_assets_archived'
        else:
            view_name = 'v_video_assets_active'
        
        # Count total records
        count_query = f"SELECT COUNT(*) as total FROM {view_name}"
        if search_term:
            count_query += " WHERE title LIKE %s OR description LIKE %s"
            total_result = execute_query(count_query, [f'%{search_term}%', f'%{search_term}%'])
        else:
            total_result = execute_query(count_query)
        
        total_count = total_result[0]['total'] if total_result else 0
        
        # Fetch paginated results
        query = f"""
            SELECT 
                asset_id, title, description, location_name, value,
                disposition, format, created_at, updated_at
            FROM {view_name}
        """
        
        if search_term:
            query += " WHERE title LIKE %s OR description LIKE %s"
            query += " ORDER BY title"
            query += f" LIMIT {per_page} OFFSET {offset}"
            rows = execute_query(query, [f'%{search_term}%', f'%{search_term}%'])
        else:
            query += " ORDER BY title"
            query += f" LIMIT {per_page} OFFSET {offset}"
            rows = execute_query(query)
        
        return jsonify({
            'success': True,
            'data': rows or [],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/videos/add', methods=['GET', 'POST'])
def add_video():
    """Add new video asset"""
    if request.method == 'GET':
        # Fetch locations for dropdown
        locations = execute_query(
            "SELECT location_id, location_name FROM locations ORDER BY location_name",
            dictionary=True
        )
        return render_template('add_video.html', locations=locations or [])
    
    # POST request
    try:
        with DatabaseContextManager(dictionary=False) as (conn, cursor):
            if conn is None:
                return jsonify({'error': 'Database connection failed'}), 500
            
            # Get form data
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            location_id = request.form.get('location_id') or None
            value = request.form.get('value') or None
            disposition = request.form.get('disposition') or None
            notes = request.form.get('notes') or None
            format_ = request.form.get('format') or None
            upc = request.form.get('upc') or None
            cover_image_url = request.form.get('cover_image_url') or None
            
            # Validate required fields
            if not title or not description:
                return jsonify({'error': 'Title and description are required'}), 400
            
            # Handle image upload
            image_url = None
            image_file = request.files.get('image_file')
            
            if image_file and image_file.filename and allowed_file(image_file.filename):
                try:
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    filename = secure_filename(image_file.filename)
                    # Add timestamp to filename for uniqueness
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    filename = timestamp + filename
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(save_path)
                    image_url = '/uploads/images/' + filename
                    logger.info(f"Image uploaded: {filename}")
                except Exception as e:
                    logger.error(f"Image upload failed: {e}")
                    return jsonify({'error': f'Image upload failed: {e}'}), 400
            
            # Call stored procedure
            try:
                cursor.callproc('add_video_asset', [
                    description,
                    int(location_id) if location_id else None,
                    float(value) if value else None,
                    disposition,
                    image_url,
                    notes,
                    title,
                    format_,
                    upc,
                    cover_image_url
                ])
                conn.commit()
                logger.info(f"Video asset added: {title}")
                return redirect('/videos')
            
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to add video: {e}")
                return jsonify({'error': f'Failed to add video: {e}'}), 500
    
    except Exception as e:
        logger.error(f"Error in add_video: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/videos/<int:asset_id>/edit', methods=['GET', 'POST'])
def edit_video(asset_id):
    """Edit existing video asset"""
    if request.method == 'GET':
        # Fetch video details
        video = execute_query(
            """
            SELECT 
                asset_id, title, description, location_id, value,
                disposition, format, upc, cover_image_url, image_url, notes
            FROM v_video_assets
            WHERE asset_id = %s
            """,
            [asset_id],
            fetch_one=True
        )
        
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        # Fetch locations
        locations = execute_query(
            "SELECT location_id, location_name FROM locations ORDER BY location_name"
        )
        
        return render_template('edit_video.html', video=video, locations=locations or [])
    
    # POST request
    try:
        with DatabaseContextManager(dictionary=False) as (conn, cursor):
            if conn is None:
                return jsonify({'error': 'Database connection failed'}), 500
            
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            location_id = request.form.get('location_id') or None
            value = request.form.get('value') or None
            disposition = request.form.get('disposition') or None
            notes = request.form.get('notes') or None
            format_ = request.form.get('format') or None
            upc = request.form.get('upc') or None
            cover_image_url = request.form.get('cover_image_url') or None
            
            if not title or not description:
                return jsonify({'error': 'Title and description are required'}), 400
            
            # Handle image upload
            image_url = request.form.get('existing_image_url') or None
            image_file = request.files.get('image_file')
            
            if image_file and image_file.filename and allowed_file(image_file.filename):
                try:
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    filename = secure_filename(image_file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    filename = timestamp + filename
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(save_path)
                    image_url = '/uploads/images/' + filename
                except Exception as e:
                    logger.error(f"Image upload failed: {e}")
                    return jsonify({'error': f'Image upload failed: {e}'}), 400
            
            try:
                cursor.callproc('update_video_asset', [
                    asset_id,
                    description,
                    int(location_id) if location_id else None,
                    float(value) if value else None,
                    disposition,
                    image_url,
                    notes,
                    title,
                    format_,
                    upc,
                    cover_image_url
                ])
                conn.commit()
                logger.info(f"Video asset updated: {title} (ID: {asset_id})")
                return redirect('/videos')
            
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to update video: {e}")
                return jsonify({'error': f'Failed to update video: {e}'}), 500
    
    except Exception as e:
        logger.error(f"Error in edit_video: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/videos/<int:asset_id>/delete', methods=['POST'])
def delete_video(asset_id):
    """Delete video asset (soft delete via archive)"""
    try:
        execute_procedure('delete_video_asset', [asset_id])
        logger.info(f"Video asset deleted: ID {asset_id}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Failed to delete video: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/videos/<int:asset_id>/archive', methods=['POST'])
def archive_video(asset_id):
    """Archive video asset"""
    try:
        execute_procedure('archive_asset', [asset_id])
        logger.info(f"Video asset archived: ID {asset_id}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Failed to archive video: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """Health check endpoint"""
    result = execute_query("SELECT 1")
    if result:
        return jsonify({'status': 'healthy', 'database': 'connected'})
    return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 503


@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Create example config if it doesn't exist
    if not os.path.exists('project_config.json'):
        logger.info("Creating project_config.example.json")
        Config.create_example_config_file()
        logger.warning("Please copy project_config.example.json to project_config.json and update with your settings")
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Run app
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
