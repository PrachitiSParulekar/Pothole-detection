from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_mail import Mail, Message
import os
import json
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import psycopg2
import psycopg2.extras
from geopy.geocoders import Nominatim
from config import config
from ultralytics import YOLO
import cv2
import numpy as np
from src.mumbai_ward_offices import MumbaiWardOffices
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from whatsapp_api_client_python import API
except ImportError:
    logger.warning("Green API client not installed. WhatsApp functionality disabled.")
    API = None

app = Flask(__name__)
app.config.from_object(config['default'])
mail = Mail(app)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', code=404, title="Page Not Found", 
                          message="The page you are looking for doesn't exist or has been moved."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', code=500, title="Internal Server Error", 
                          message="Something went wrong on our end. Please try again later."), 500

# Global variables for AI model and services
model = None
greenapi = None
parser = None

def initialize_greenapi():
    """Initialize Green API client for WhatsApp"""
    global greenapi
    try:
        if API and hasattr(config['default'], 'GREENAPI_ID_INSTANCE'):
            greenapi = API.GreenAPI(
                config['default'].GREENAPI_ID_INSTANCE, 
                config['default'].GREENAPI_API_TOKEN
            )
            logger.info("Green API WhatsApp client initialized successfully")
            return True
    except Exception as e:
        logger.warning(f"Failed to initialize Green API: {e}")
    return False

def send_whatsapp_notification(phone_number, message):
    """Send WhatsApp notification using Green API"""
    global greenapi
    
    if not greenapi:
        logger.warning("Green API not initialized")
        return False
        
    try:
        # Format phone number for WhatsApp (remove + and add @c.us)
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        # Remove any spaces or special characters except digits
        phone_number = ''.join(filter(str.isdigit, phone_number))
        whatsapp_id = f"{phone_number}@c.us"
        
        # Send WhatsApp message
        result = greenapi.sending.sendMessage(whatsapp_id, message)
        
        if result.code == 200:
            logger.info(f"✅ WhatsApp notification sent to {phone_number}")
            return result.data.get('idMessage', True)
        else:
            logger.error(f"❌ Failed to send WhatsApp: {result.data}")
            return False
            
    except Exception as e:
        logger.error(f"❌ WhatsApp notification error: {e}")
        return False

def log_notification(complaint_id, notification_type, recipient, message_id=None, status='sent', error_message=None):
    """Log notification to database"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notification_logs (complaint_id, notification_type, recipient, message_id, status, error_message)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (complaint_id, notification_type, recipient, message_id, status, error_message))
            conn.commit()
            conn.close()
            logger.info(f"Notification logged: {notification_type} to {recipient}")
    except Exception as e:
        logger.error(f"Failed to log notification: {e}")

def get_db_connection():
    """Get database connection"""
    try:
        db_config = config['default'].DATABASE_CONFIG
        conn = psycopg2.connect(
            host=db_config['host'],
            database=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password'],
            port=db_config['port']
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def init_database():
    """Initialize database tables"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Cannot initialize database - connection failed")
            return False
            
        cursor = conn.cursor()
        
        # Create complaints table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id VARCHAR(255) PRIMARY KEY,
                description TEXT NOT NULL,
                category VARCHAR(100) DEFAULT 'pothole',
                location TEXT,
                longitude DECIMAL(10, 8),
                latitude DECIMAL(10, 8),
                photo_path VARCHAR(500),
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                citizen_name VARCHAR(255),
                citizen_phone VARCHAR(20),
                citizen_email VARCHAR(255)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

# Route handlers
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Serve favicon.ico"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/heatmap')
def heatmap():
    """Display heatmap with all complaints"""
    return render_template('heatmap.html')

@app.route('/api/complaints/heatmap')
def get_heatmap_data():
    """API endpoint to get complaint data for heatmap visualization with filtering"""
    try:
        # Get query parameters for filtering
        days = request.args.get('days', default=90, type=int)  # Default last 90 days
        status_filter = request.args.get('status')  # Filter by status
        category_filter = request.args.get('category')  # Filter by category
        severity_filter = request.args.get('severity', type=int)  # Filter by severity
        start_date = request.args.get('start_date')  # Custom start date
        end_date = request.args.get('end_date')  # Custom end date
        
        # Build the base query with enhanced data for better visualization
        query = """
            SELECT 
                ST_X(location::geometry) as longitude,
                ST_Y(location::geometry) as latitude,
                category,
                status,
                severity,
                created_at,
                SUBSTRING(id::text, 1, 8) as short_id,
                assigned_ward_office,
                detection_info,
                EXTRACT(DAYS FROM NOW() - created_at) as age_days,
                citizen_name,
                citizen_phone
            FROM complaints 
            WHERE location IS NOT NULL
        """
        
        params = []
        
        # Add date filtering
        if start_date and end_date:
            # Custom date range
            query += " AND created_at BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        else:
            # Default to last N days
            query += " AND created_at >= NOW() - INTERVAL '%s days'"
            params.append(days)
        
        # Add status filtering
        if status_filter:
            query += " AND status = %s"
            params.append(status_filter)
        
        # Add category filtering
        if category_filter:
            query += " AND category = %s"
            params.append(category_filter)
        
        # Add severity filtering
        if severity_filter is not None:
            query += " AND severity = %s"
            params.append(severity_filter)
        
        # Order by most recent first and limit for performance
        query += " ORDER BY created_at DESC LIMIT 1000"
        
        # Execute query
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Format data for frontend with enhanced information
        complaints = []
        for row in results:
            longitude, latitude, category, status, severity, created_at, short_id, assigned_ward_office, detection_info, age_days, citizen_name, citizen_phone = row
            
            # Parse ward office data if available
            ward_info = None
            if assigned_ward_office:
                try:
                    if isinstance(assigned_ward_office, str):
                        ward_info = json.loads(assigned_ward_office)
                    else:
                        ward_info = assigned_ward_office
                except:
                    ward_info = None
            
            # Parse detection info if available
            detection_data = None
            if detection_info:
                try:
                    if isinstance(detection_info, str):
                        detection_data = json.loads(detection_info)
                    else:
                        detection_data = detection_info
                except:
                    detection_data = None
            
            # Determine complaint age category
            age_days_int = int(age_days) if age_days else 0
            if age_days_int <= 7:
                age_category = 'recent'
            elif age_days_int <= 30:
                age_category = 'medium'
            else:
                age_category = 'old'
            
            complaints.append({
                'id': short_id,  # Anonymized ID
                'latitude': float(latitude) if latitude else None,
                'longitude': float(longitude) if longitude else None,
                'category': category,
                'status': status or 'pending',
                'severity': severity or 1,
                'created_at': created_at.isoformat() if created_at else None,
                'timestamp': int(created_at.timestamp() * 1000) if created_at else None,
                'age_days': age_days_int,
                'age_category': age_category,
                'ward_info': ward_info,
                'detection_data': detection_data,
                'has_citizen_contact': bool(citizen_name or citizen_phone)
            })
        
        cursor.close()
        conn.close()
        
        # Return response with metadata
        response_data = {
            'complaints': complaints,
            'total_count': len(complaints),
            'filters_applied': {
                'days': days if not (start_date and end_date) else None,
                'status': status_filter,
                'category': category_filter,
                'severity': severity_filter,
                'date_range': f"{start_date} to {end_date}" if start_date and end_date else None
            },
            'summary': {
                'categories': {},
                'statuses': {},
                'severities': {}
            }
        }
        
        # Generate summary statistics
        for complaint in complaints:
            # Category count
            cat = complaint['category']
            response_data['summary']['categories'][cat] = response_data['summary']['categories'].get(cat, 0) + 1
            
            # Status count
            status = complaint['status']
            response_data['summary']['statuses'][status] = response_data['summary']['statuses'].get(status, 0) + 1
            
            # Severity count
            sev = complaint['severity']
            response_data['summary']['severities'][sev] = response_data['summary']['severities'].get(sev, 0) + 1
        
        logger.info(f"🗺️ Heatmap data request: {len(complaints)} complaints returned")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting heatmap data: {e}")
        return jsonify({'error': 'Failed to fetch heatmap data'}), 500

@app.route('/notifications')
def notifications():
    """Display notifications page"""
    return render_template('notifications.html')

@app.route('/success')
def success_page():
    """Display success page after complaint submission"""
    # Get parameters from query string
    complaint_id = request.args.get('complaint_id')
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    
    if not complaint_id:
        flash('No complaint ID provided', 'error')
        return redirect(url_for('index'))
    
    # Fetch complaint data from database
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, description, category, location_text, 
                       photo_path, status, created_at, citizen_name, citizen_phone, citizen_email,
                       processed_image_path, detection_info
                FROM complaints WHERE id = %s
                ''', (complaint_id,))
            
            complaint = cursor.fetchone()
            conn.close()
            
            if complaint:
                # Create complaint_data object for template
                complaint_data = {
                    'complaint_id': complaint[0],
                    'description': complaint[1],
                    'category': complaint[2],
                    'location': complaint[3],
                    'photo_path': complaint[4],
                    'status': complaint[5],
                    'created_at': complaint[6].strftime('%Y-%m-%d %H:%M:%S') if complaint[6] else 'N/A',
                    'citizen_name': complaint[7],
                    'citizen_phone': complaint[8],
                    'citizen_email': complaint[9],
                    'processed_image_path': complaint[10],
                    'detection_info': json.loads(complaint[11]) if complaint[11] and isinstance(complaint[11], str) else complaint[11]
                }
                
                # Use provided coordinates or default to Mumbai center
                latitude = float(lat) if lat else 19.0760
                longitude = float(lng) if lng else 72.8777
                
                return render_template('success.html', 
                                     complaint_data=complaint_data,
                                     complaint_id=complaint_id,
                                     latitude=latitude,
                                     longitude=longitude)
            else:
                flash('Complaint not found', 'error')
                return redirect(url_for('index'))
        else:
            flash('Database connection failed', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        logger.error(f"Error fetching complaint data: {e}")
        flash('Error loading complaint details', 'error')
        return redirect(url_for('index'))

@app.route('/api/complaints', methods=['GET', 'POST'])
def api_complaints():
    """Unified complaints API - handles both AJAX and traditional form submissions"""
    if request.method == 'POST':
        return handle_complaint_unified()
    else:
        return get_complaints()

# Backward compatibility route - redirects to unified handler
@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    """Legacy route - redirects to unified complaints API"""
    return handle_complaint_unified()

def handle_complaint_unified():
    """Unified complaint handler supporting both AJAX and traditional form submissions"""
    try:
        # Smart content detection and data extraction
        is_ajax_request = (
            request.is_json or 
            request.headers.get('Content-Type', '').startswith('application/json') or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        )
        
        logger.info(f"📥 Processing complaint - AJAX: {is_ajax_request}")
        
        # Extract data based on request type
        if is_ajax_request and request.is_json:
            # Pure JSON request
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400
            files = {}  # No files in JSON requests
        else:
            # Form data request (multipart or traditional)
            data = request.form.to_dict()
            files = request.files
            if not data and not files:
                return jsonify({'status': 'error', 'message': 'No form data provided'}), 400
        
        # Process the complaint using shared logic
        result = process_complaint_shared(data, files, is_ajax_request)
        
        # Return appropriate response based on request type
        if is_ajax_request:
            # Return JSON for AJAX requests
            return jsonify(result['response']), result['status_code']
        else:
            # Handle traditional form submissions
            if result['status_code'] == 201:
                # Success - redirect to success page
                flash(f'✅ Complaint successfully submitted! ID: {result["response"]["complaint_id"]}', 'success')
                return redirect(url_for('success_page', 
                                      complaint_id=result['response']['complaint_id'],
                                      lat=result['response'].get('latitude'),
                                      lng=result['response'].get('longitude')))
            else:
                # Error - flash message and redirect back
                error_msg = result['response'].get('message', 'An error occurred')
                flash(f'❌ Error: {error_msg}', 'error')
                return redirect(url_for('index'))
                
    except Exception as e:
        logger.error(f"Error in unified complaint handler: {e}")
        error_response = {'status': 'error', 'message': f'Server error: {str(e)}'}
        
        if is_ajax_request:
            return jsonify(error_response), 500
        else:
            flash(f'❌ Server error: {str(e)}', 'error')
            return redirect(url_for('index'))

def process_complaint_shared(data, files, is_ajax_request):
    """Shared complaint processing logic for both AJAX and traditional submissions"""
    try:
        # Extract and validate required fields
        description = data.get('description', '').strip()
        location_text = data.get('location', '').strip()
        
        if not description and not files.get('photo'):
            return {
                'response': {'status': 'error', 'message': 'Either description or photo is required'},
                'status_code': 400
            }
        
        # Handle file upload and processing
        photo_path = None
        processed_image_path = None
        detection_info = None
        complaint_id = str(uuid.uuid4())
        
        if files and 'photo' in files:
            file = files['photo']
            if file and file.filename:
                filename = secure_filename(f"{complaint_id}_{file.filename}")
                full_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(full_photo_path)
                photo_path = f"uploads/{filename}"
                
                # Process image with YOLO if model is available
                try:
                    processed_image_path, detection_info = process_pothole_image(full_photo_path)
                    
                    # Update description with detection info if available
                    if detection_info and detection_info['detected']:
                        confidence_pct = detection_info['confidence'] * 100
                        area_val = detection_info['area_m2']
                        if not description:
                            description = f"Pothole detected - Confidence: {confidence_pct:.1f}%, Severity: {detection_info['severity']}, Area: {area_val:.4f} m²"
                except Exception as e:
                    logger.warning(f"Image processing failed: {e}")
        
        # Default description if none provided
        if not description:
            description = "Pothole detected via image upload"
        
        # Enhanced geocoding with fallback strategies
        latitude, longitude = None, None
        if location_text:
            try:
                lat, lng, is_fallback = enhanced_geocode_location(location_text)
                if lat is not None and lng is not None:
                    latitude, longitude = lat, lng
                    if is_fallback:
                        logger.info(f"📍 Used fallback geocoding: {latitude}, {longitude}")
                    else:
                        logger.info(f"✅ Successfully geocoded: {latitude}, {longitude}")
                else:
                    # Use Mumbai center as fallback
                    latitude, longitude = 19.0760, 72.8777
                    logger.info(f"🔄 Using Mumbai center coordinates as fallback")
            except Exception as e:
                logger.warning(f"Geocoding failed: {e}")
                latitude, longitude = 19.0760, 72.8777
                logger.info(f"🆘 Using emergency coordinates")
        else:
            # No location provided - use Mumbai center
            latitude, longitude = 19.0760, 72.8777
            location_text = "Location not specified"
            logger.info(f"🔄 No location provided, using Mumbai center")
        
        # Extract citizen contact information
        citizen_name = data.get('citizen_name', '').strip()
        citizen_phone = data.get('citizen_phone', '').strip()
        citizen_email = data.get('citizen_email', '').strip()
        category = data.get('category', 'pothole')
        status = 'pending'
        
        # Insert complaint into database
        db_response = insert_complaint_to_db(
            complaint_id, description, category, location_text,
            longitude, latitude, photo_path, status,
            citizen_name, citizen_phone, citizen_email,
            processed_image_path, detection_info
        )
        
        # Parse database response
        if isinstance(db_response, tuple):
            db_data, db_status = db_response
            if hasattr(db_data, 'get_json'):
                response_data = db_data.get_json()
            else:
                response_data = db_data
        else:
            response_data = db_response.get_json() if hasattr(db_response, 'get_json') else db_response
            db_status = 201
        
        if db_status == 201:
            # Success response
            success_response = {
                'status': 'success',
                'message': response_data.get('message', 'Complaint submitted successfully!'),
                'complaint_id': complaint_id,
                'latitude': latitude,
                'longitude': longitude,
                'location_text': location_text,
                'processed_image': processed_image_path,
                'detection_info': detection_info,
                'success': True  # For backward compatibility with existing AJAX code
            }
            
            return {
                'response': success_response,
                'status_code': 201
            }
        else:
            # Database error
            error_msg = response_data.get('error', 'Database error occurred')
            return {
                'response': {'status': 'error', 'message': error_msg},
                'status_code': db_status
            }
            
    except Exception as e:
        logger.error(f"Error in shared complaint processing: {e}")
        return {
            'response': {'status': 'error', 'message': f'Processing error: {str(e)}'},
            'status_code': 500
        }



def insert_complaint_to_db(complaint_id, description, category, location_text, 
                          longitude, latitude, photo_path, status, 
                          citizen_name, citizen_phone, citizen_email,
                          processed_image_path=None, detection_info=None):
    """Insert complaint into database"""
    try:
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Find nearest ward office for automatic notifications
        nearest_ward = None
        try:
            if latitude and longitude and 'ward_system' in globals() and ward_system:
                nearest_ward = ward_system.find_nearest_ward(latitude, longitude, max_distance_km=20)
                if nearest_ward:
                    logger.info(f"Found nearest ward: {nearest_ward['name']} ({nearest_ward['distance_km']} km away)")
                else:
                    logger.warning(f"No ward office found within 20km of coordinates: {latitude}, {longitude}")
        except Exception as e:
            logger.warning(f"Ward office lookup failed: {e}")
            nearest_ward = None
        
        # Prepare ward office information  
        ward_office_data = None
        ward_id = None
        if nearest_ward:
            # Store complete ward office information as JSON
            ward_office_data = {
                'name': nearest_ward['name'],
                'email': nearest_ward.get('email'),
                'phone': nearest_ward.get('phone'),
                'distance_km': nearest_ward.get('distance_km')
            }
            ward_id = nearest_ward.get('code', nearest_ward['name'].split()[0])  # Use ward code or first word as ID

        # Insert complaint into database
        # Handle location data - only create ST_Point if we have valid coordinates
        if longitude is not None and latitude is not None:
            cursor.execute('''
                INSERT INTO complaints (id, description, category, location_text, 
                                      photo_path, status, created_at, citizen_name, citizen_phone, citizen_email,
                                      processed_image_path, detection_info, assigned_ward_office, ward_id, location)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s, ST_Point(%s, %s))
                ''', (complaint_id, description, category, location_text, photo_path, status,
                      citizen_name, citizen_phone, citizen_email, processed_image_path, 
                      json.dumps(detection_info) if detection_info else None, 
                      json.dumps(ward_office_data) if ward_office_data else None, ward_id,
                      longitude, latitude))
        else:
            # Insert without location if coordinates are not available
            cursor.execute('''
                INSERT INTO complaints (id, description, category, location_text, 
                                      photo_path, status, created_at, citizen_name, citizen_phone, citizen_email,
                                      processed_image_path, detection_info, assigned_ward_office, ward_id)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)
                ''', (complaint_id, description, category, location_text, photo_path, status,
                      citizen_name, citizen_phone, citizen_email, processed_image_path, 
                      json.dumps(detection_info) if detection_info else None, 
                      json.dumps(ward_office_data) if ward_office_data else None, ward_id))
        
        # Get the inserted complaint data
        cursor.execute('''
            SELECT id, description, category, location_text, 
                   photo_path, status, created_at, citizen_name, citizen_phone, citizen_email,
                   processed_image_path, detection_info
            FROM complaints WHERE id = %s
            ''', (complaint_id,))
        
        complaint = cursor.fetchone()
        conn.commit()
        
        if complaint:
            # Convert to dictionary
            complaint_data = {
                'complaint_id': complaint[0],
                'description': complaint[1],
                'category': complaint[2],
                'location_text': complaint[3],
                'longitude': longitude,  # Use the passed values
                'latitude': latitude,
                'photo_path': complaint[4],
                'status': complaint[5],
                'created_at': complaint[6].isoformat() if complaint[6] else None,
                'citizen_name': complaint[7],
                'citizen_phone': complaint[8],
                'citizen_email': complaint[9],
                'processed_image_path': complaint[10],
                'detection_info': json.loads(complaint[11]) if complaint[11] and isinstance(complaint[11], str) else complaint[11]
            }
            
            # Send professional email notification to ward office
            try:
                # Determine ward office details
                if ward_office_data:
                    ward_office_name = ward_office_data['name']
                    # For prototype: send to admin email but show actual ward office details
                    ward_email = "prachitiparulekar14@gmail.com"  # Prototype mode - your email
                    actual_ward_email = ward_office_data.get('email', 'No email available')
                    ward_phone = ward_office_data.get('phone', '+91-22-2417-3000')
                else:
                    ward_office_name = 'Auto-assigned Ward Office (Location-based routing failed)'
                    ward_email = "prachitiparulekar14@gmail.com"  # Fallback to your email
                    actual_ward_email = 'No ward office found'
                    ward_phone = '+91-22-2417-3000'
                
                subject = f"New Complaint #{complaint_id} - pothole"
                
                # Create detection description for email
                detection_desc = description
                if detection_info and detection_info.get('detected'):
                    confidence = detection_info.get('confidence', 0) * 100
                    severity = detection_info.get('severity', 'Unknown')
                    area = detection_info.get('area_m2', 0)
                    detection_desc = f"Pothole detected - Confidence: {confidence:.1f}%, Severity: {severity}, Area: {area:.4f} m²"
                
                # Professional email body matching the format shown
                body = f"""New CivicSightAI Complaint #{complaint_id}

Complaint Details:
Type: pothole
Description: {detection_desc}
Location: {location_text}
Coordinates: {latitude}, {longitude}
Status: pending
Reported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Google Maps Link: https://www.google.com/maps?q={latitude},{longitude}

Citizen Contact Information:
Name: {citizen_name or 'Not provided'}
Phone: {citizen_phone or 'Not provided'}
Email: {citizen_email or 'Not provided'}

Ward Office Information:
Name: {ward_office_name}
Manager: Ward Manager
Phone: {ward_phone}
Official Email: {actual_ward_email if ward_office_data else 'Not available'}

This complaint has been automatically assigned to your ward office based on location proximity.

[PROTOTYPE MODE: This email is being sent to {ward_email} for testing. In production, it would be sent to {actual_ward_email if ward_office_data else 'the appropriate ward office email'}]

CivicSightAI - Automated Urban Infrastructure Management"""

                # Send email with attachment
                send_email_notification([ward_email], subject, body, photo_path)
                logger.info(f"📧 Ward office notification sent to: {ward_email}")
                
            except Exception as e:
                logger.warning(f"Failed to send email notification: {e}")
            
            # Send WhatsApp notification to citizen if phone number is provided
            if citizen_phone and config['default'].ENABLE_GREENAPI_WHATSAPP:
                try:
                    whatsapp_message = f"""🚨 *Complaint Submitted Successfully!*

📋 *Complaint ID:* {complaint_id}
📍 *Location:* {location_text or 'Location provided'}
📝 *Description:* {description[:100]}{'...' if len(description) > 100 else ''}

✅ *Status:* Your complaint has been received and authorities have been notified.

🔔 You will receive updates on this WhatsApp number as your complaint is processed.

Thank you for helping make our city better! 🏙️

- CivicSightAI Team"""
                    
                    message_id = send_whatsapp_notification(citizen_phone, whatsapp_message)
                    if message_id:
                        log_notification(complaint_id, 'whatsapp', citizen_phone, message_id, 'sent')
                        logger.info(f"✅ WhatsApp confirmation sent to citizen: {citizen_phone}")
                    else:
                        log_notification(complaint_id, 'whatsapp', citizen_phone, None, 'failed', 'Send failed')
                        logger.warning(f"❌ Failed to send WhatsApp to citizen: {citizen_phone}")
                        
                except Exception as e:
                    log_notification(complaint_id, 'whatsapp', citizen_phone, None, 'error', str(e))
                    logger.error(f"❌ WhatsApp notification error: {e}")
            
            response_data = {
                'message': 'Complaint submitted successfully',
                'complaint_id': complaint_id,
                **complaint_data
            }
            
            return jsonify(response_data), 201
        else:
            conn.rollback()
            return jsonify({'error': 'Failed to retrieve saved complaint'}), 500
            
    except Exception as e:
        logger.error(f"Database error in insert_complaint_to_db: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def get_complaints():
    """Get all complaints from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
            SELECT id, description, category, location, longitude, latitude, 
                   photo_path, status, created_at, citizen_name, citizen_phone, citizen_email
            FROM complaints 
            ORDER BY created_at DESC
        ''')
        
        complaints = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        complaints_list = []
        for complaint in complaints:
            complaint_dict = dict(complaint)
            if complaint_dict['created_at']:
                complaint_dict['created_at'] = complaint_dict['created_at'].isoformat()
            complaints_list.append(complaint_dict)
        
        return jsonify({'complaints': complaints_list})
        
    except Exception as e:
        logger.error(f"Error getting complaints: {e}")
        return jsonify({'error': 'Failed to retrieve complaints'}), 500

def enhanced_geocode_location(location_text):
    """Enhanced geocoding with multiple fallback strategies including area-based extraction"""
    geolocator = Nominatim(user_agent="civicsight_pothole_detector")
    
    # Extract area names from complex addresses
    def extract_mumbai_areas(text):
        """Extract known Mumbai area names from the address"""
        mumbai_areas = [
            'Borivali West', 'Borivali East', 'Malad West', 'Malad East', 
            'Kandivali West', 'Kandivali East', 'Goregaon West', 'Goregaon East',
            'Andheri West', 'Andheri East', 'Bandra West', 'Bandra East',
            'Dadar West', 'Dadar East', 'Matunga', 'Kurla', 'Ghatkopar',
            'Powai', 'Colaba', 'Marine Drive', 'Fort', 'Churchgate'
        ]
        
        found_areas = []
        text_lower = text.lower()
        for area in mumbai_areas:
            if area.lower() in text_lower:
                found_areas.append(area)
        return found_areas
    
    # Get area-based fallback addresses
    extracted_areas = extract_mumbai_areas(location_text)
    
    # Build comprehensive search strategies
    search_strategies = [
        f"{location_text}, Mumbai, Maharashtra, India",
        f"{location_text}, Mumbai, India", 
        f"{location_text}, Maharashtra, India",
        f"{location_text}, India",
        location_text
    ]
    
    # Add area-based fallbacks if found
    for area in extracted_areas:
        search_strategies.extend([
            f"{area}, Mumbai, Maharashtra, India",
            f"{area}, Mumbai, India"
        ])
    
    for i, strategy in enumerate(search_strategies):
        try:
            logger.debug(f"Trying geocoding strategy {i+1}: '{strategy}'")
            location = geolocator.geocode(strategy, timeout=10)
            if location:
                logger.info(f"✅ Geocoding successful with strategy: '{strategy}'")
                # Determine if this is a fallback based on whether it's one of the original strategies
                is_area_fallback = i >= 5  # After the original 5 strategies
                return location.latitude, location.longitude, is_area_fallback
                
        except Exception as e:
            logger.warning(f"Geocoding strategy '{strategy}' failed: {e}")
            continue
    
    # If all strategies fail, return None
    logger.warning(f"All geocoding strategies failed for: '{location_text}'")
    return None, None, True

def process_pothole_image(image_path):
    """Process image with YOLO model to detect potholes"""
    try:
        global model
        if not model:
            model_path = "yolov11_best.pt"
            if os.path.exists(model_path):
                model = YOLO(model_path)
            else:
                logger.warning("YOLO model not found")
                return None, None
        
        # Run inference
        results = model(image_path)
        
        # Process results
        detection_info = {
            'detected': False,
            'confidence': 0.0,
            'severity': 'unknown',
            'area_m2': 0.0
        }
        
        if results and len(results) > 0:
            result = results[0]
            if result.boxes and len(result.boxes) > 0:
                # Get highest confidence detection
                max_conf_idx = result.boxes.conf.argmax()
                confidence = float(result.boxes.conf[max_conf_idx])
                
                if confidence > 0.5:  # Threshold for detection
                    detection_info['detected'] = True
                    detection_info['confidence'] = confidence
                    
                    # Estimate severity based on confidence
                    if confidence > 0.8:
                        detection_info['severity'] = 'high'
                    elif confidence > 0.65:
                        detection_info['severity'] = 'medium'
                    else:
                        detection_info['severity'] = 'low'
                    
                    # Estimate area (placeholder calculation)
                    box = result.boxes.xywh[max_conf_idx]
                    detection_info['area_m2'] = float(box[2] * box[3] * 0.001)  # Rough estimate
        
        # Save processed image with annotations
        processed_path = image_path.replace('.', '_processed.')
        if results:
            annotated = results[0].plot()
            cv2.imwrite(processed_path, annotated)
            
            # Convert to relative path for web serving
            if processed_path.startswith(app.config['UPLOAD_FOLDER']):
                relative_path = processed_path.replace(app.config['UPLOAD_FOLDER'], 'uploads').replace('\\', '/')
            else:
                # Fallback: just get the filename and prepend uploads/
                relative_path = f"uploads/{os.path.basename(processed_path)}"
            
            return relative_path, detection_info
        
        return None, detection_info
        
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        return None, None

def send_email_notification(recipients, subject, body, attachment_path=None):
    """Send email notification"""
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        if attachment_path and os.path.exists(attachment_path):
            with app.open_resource(attachment_path) as fp:
                msg.attach(
                    filename=os.path.basename(attachment_path),
                    content_type="image/jpeg",
                    data=fp.read()
                )
        
        mail.send(msg)
        logger.info(f"Email sent successfully to {recipients}")
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Initialize Green API
    initialize_greenapi()
    
    # Initialize Mumbai ward office system
    try:
        ward_system = MumbaiWardOffices()
        logger.info("Mumbai ward office system initialized")
    except Exception as e:
        ward_system = None
        logger.warning(f"Ward office system initialization failed: {e}")
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=False)
