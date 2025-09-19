from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message
import os
import json
import uuid
import random
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import psycopg2
import psycopg2.extras
from geopy.geocoders import Nominatim
from config import config
from ultralytics import YOLO
import cv2
import numpy as np
from src.ward_office_parser import WardOfficeParser
import logging
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from whatsapp_api_client_python import API  # Using whatsapp-api-client-python package
except ImportError:
    logger.warning("Green API client not installed. WhatsApp functionality disabled.")
    API = None

app = Flask(__name__)
app.config.from_object(config['default'])

# Initialize Flask-Mail
mail = Mail(app)

# Import routes after app creation
from src import notification_routes

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
        if API and hasattr(config['default'], 'GREEN_API_ID'):
            greenapi = API.GreenAPI(
                config['default'].GREEN_API_ID, 
                config['default'].GREEN_API_TOKEN
            )
            logger.info("Green API WhatsApp client initialized successfully")
            return True
    except Exception as e:
        logger.warning(f"Failed to initialize Green API: {e}")
    return False

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

@app.route('/heatmap')
def heatmap():
    """Display heatmap with all complaints"""
    return render_template('heatmap.html')

@app.route('/notifications')
def notifications():
    """Display notifications page"""
    return render_template('notifications.html')

@app.route('/api/complaints', methods=['GET', 'POST'])
def api_complaints():
    """Handle complaints API - JSON only"""
    if request.method == 'POST':
        return add_complaint_api()
    else:
        return get_complaints()

@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    """Handle form submission from web interface"""
    return add_complaint_form()

def add_complaint_api():
    """Submit a new complaint via REST API (JSON only)"""
    try:
        # Handle JSON data only
        if not request.content_type or 'application/json' not in request.content_type:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        # Extract required fields
        description = data.get('description')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Validate required fields
        if not (description and latitude and longitude):
            return jsonify({'error': 'Missing required fields: description, latitude, longitude'}), 400
        
        # Extract optional fields with defaults
        category = data.get('category', 'pothole')
        status = data.get('status', 'pending')
        photo_path = data.get('photo_path')
        location_text = data.get('location_text', f"Lat: {latitude}, Lng: {longitude}")
        
        # Extract citizen contact information
        citizen_name = data.get('citizen_name')
        citizen_phone = data.get('citizen_phone')
        citizen_email = data.get('citizen_email')
        
        # Generate complaint ID
        complaint_id = str(uuid.uuid4())
        
        # Connect to database and insert complaint
        return insert_complaint_to_db(complaint_id, description, category, location_text, 
                                    longitude, latitude, photo_path, status, 
                                    citizen_name, citizen_phone, citizen_email)
        
    except Exception as e:
        logger.error(f"Error in add_complaint_api: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def add_complaint_form():
    """Handle form submission from web interface"""
    try:
        # Handle form data (multipart/form-data)
        description = request.form.get('description') or "Pothole detected via image upload"
        location_text = request.form.get('location')
        category = request.form.get('category') or "pothole"
        
        # Get citizen contact information from form
        citizen_name = request.form.get('citizen_name')
        citizen_phone = request.form.get('citizen_phone')
        citizen_email = request.form.get('citizen_email')
        
        # Handle file upload and processing
        photo_path = None
        processed_image_path = None
        detection_info = None
        full_photo_path = None
        
        # Generate unique complaint ID (full UUID for database compatibility)
        complaint_id = str(uuid.uuid4())
        
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                filename = secure_filename(f"{complaint_id}_{file.filename}")
                full_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(full_photo_path)
                photo_path = f"uploads/{filename}"  # Store relative path
                
                # Process image with YOLO if model is available
                try:
                    processed_image_path, detection_info = process_pothole_image(full_photo_path)
                    
                    # Update description with detection info if available
                    if detection_info and detection_info['detected']:
                        confidence_pct = detection_info['confidence'] * 100
                        area_val = detection_info['area_m2']
                        description = f"Pothole detected - Confidence: {confidence_pct:.1f}%, Severity: {detection_info['severity']}, Area: {area_val:.4f} m²"
                except Exception as e:
                    logger.warning(f"Image processing failed: {e}")
        
        # Enhanced geocoding with fallback strategies
        latitude, longitude, is_fallback = None, None, False
        if location_text:
            try:
                latitude, longitude, is_fallback = enhanced_geocode_location(location_text)
                
                if latitude is not None and longitude is not None:
                    if is_fallback:
                        logger.info(f"📍 Geocoded '{location_text}' to fallback coordinates: {latitude}, {longitude}")
                    else:
                        logger.info(f"✅ Geocoded '{location_text}' to exact coordinates: {latitude}, {longitude}")
                else:
                    logger.info(f"❌ Enhanced geocoding completely failed for '{location_text}'")
                    
            except Exception as e:
                logger.info(f"Geocoding error for '{location_text}': {e}")
                # Use Mumbai center as last resort
                latitude, longitude, is_fallback = 19.0760, 72.8777, True
                logger.info(f"🔄 Using Mumbai center coordinates as emergency fallback")
            
        else:
            logger.warning("No location provided for geocoding")
            return jsonify({'error': 'Location is required'}), 400
        
        if not (latitude and longitude):
            return jsonify({'error': 'Could not determine location coordinates'}), 400
        
        status = 'pending'
        
        # Insert complaint and get response
        response = insert_complaint_to_db(complaint_id, description, category, location_text, 
                                        longitude, latitude, photo_path, status, 
                                        citizen_name, citizen_phone, citizen_email)
        
        # Parse the response to get the complaint data
        if isinstance(response, tuple):
            response_data, status_code = response
            if hasattr(response_data, 'get_json'):
                data = response_data.get_json()
            else:
                data = response_data
        else:
            data = response.get_json() if hasattr(response, 'get_json') else response
            status_code = 201
        
        # If successful, redirect to success page with complaint data
        if status_code == 201:
            return render_template('success.html', 
                                 complaint_data=data,
                                 complaint_id=data['complaint_id'],
                                 latitude=latitude,
                                 longitude=longitude)
        else:
            # Return error response
            return response
            
    except Exception as e:
        logger.error(f"Error in add_complaint_form: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

def insert_complaint_to_db(complaint_id, description, category, location_text, 
                          longitude, latitude, photo_path, status, 
                          citizen_name, citizen_phone, citizen_email):
    """Insert complaint into database"""
    try:
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Check if ward office parser is available for notifications
        try:
            # Find nearest ward office for automatic notifications
            if latitude and longitude and parser:
                nearest_ward = parser.find_nearest_ward_office_db(latitude, longitude, max_distance_km=20)
        except Exception as e:
            logger.warning(f"Ward office lookup failed: {e}")
            nearest_ward = None
        
        # Insert complaint into database
        cursor.execute('''
            INSERT INTO complaints (id, description, category, location, longitude, latitude, 
                                  photo_path, status, created_at, citizen_name, citizen_phone, citizen_email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s)
            ''', (complaint_id, description, category, location_text, longitude, latitude, photo_path, status,
                  citizen_name, citizen_phone, citizen_email))
        
        # Get the inserted complaint data
        cursor.execute('''
            SELECT id, description, category, location, longitude, latitude, 
                   photo_path, status, created_at, citizen_name, citizen_phone, citizen_email
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
                'location': complaint[3],
                'longitude': float(complaint[4]) if complaint[4] else None,
                'latitude': float(complaint[5]) if complaint[5] else None,
                'photo_path': complaint[6],
                'status': complaint[7],
                'created_at': complaint[8].isoformat() if complaint[8] else None,
                'citizen_name': complaint[9],
                'citizen_phone': complaint[10],
                'citizen_email': complaint[11]
            }
            
            # Try to send email notification if nearest ward is found and email is configured
            if nearest_ward and nearest_ward.get('email'):
                try:
                    subject = f"New Pothole Complaint - ID: {complaint_id}"
                    body = f"""
                    A new pothole complaint has been submitted:
                    
                    Complaint ID: {complaint_id}
                    Description: {description}
                    Location: {location_text}
                    Coordinates: {latitude}, {longitude}
                    Status: {status}
                    
                    Citizen Details:
                    Name: {citizen_name or 'Not provided'}
                    Phone: {citizen_phone or 'Not provided'}
                    Email: {citizen_email or 'Not provided'}
                    
                    Ward Office: {nearest_ward.get('name', 'Unknown')}
                    """
                    
                    send_email_notification([nearest_ward['email']], subject, body, photo_path)
                    logger.info(f"Email notification sent to ward office: {nearest_ward['email']}")
                    
                except Exception as e:
                    logger.warning(f"Failed to send email notification: {e}")
            
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
    """Enhanced geocoding with multiple fallback strategies"""
    geolocator = Nominatim(user_agent="civicsight_pothole_detector")
    
    try:
        # Try exact search first
        location = geolocator.geocode(location_text + ", Mumbai, Maharashtra, India")
        if location:
            return location.latitude, location.longitude, False
        
        # Try without Mumbai
        location = geolocator.geocode(location_text)
        if location:
            return location.latitude, location.longitude, True
            
    except Exception as e:
        logger.warning(f"Geocoding failed: {e}")
    
    # Return None if all attempts fail
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
            return processed_path, detection_info
        
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

# Initialize services on startup
if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Initialize Green API
    initialize_greenapi()
    
    # Initialize ward office parser
    try:
        parser = WardOfficeParser()
        logger.info("Ward office parser initialized")
    except Exception as e:
        logger.warning(f"Ward office parser initialization failed: {e}")
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Run the app
    app.run(debug=True)
