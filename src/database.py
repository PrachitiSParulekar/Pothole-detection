import sqlite3
import os
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self, db_path='data/complaints.db'):
        """Initialize database manager"""
        self.db_path = db_path
        self.ensure_database_exists()
        self.create_tables()
    
    def ensure_database_exists(self):
        """Ensure the database directory and file exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def create_tables(self):
        """Create necessary tables if they don't exist (adapted for existing schema)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if the complaints table exists and adapt to existing schema
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='complaints'")
            if not cursor.fetchone():
                # Create new complaints table with our preferred schema
                cursor.execute('''
                    CREATE TABLE complaints (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        image_path TEXT NOT NULL,
                        annotated_image_path TEXT,
                        potholes_detected INTEGER DEFAULT 0,
                        detection_results TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        latitude REAL,
                        longitude REAL,
                        status TEXT DEFAULT 'pending',
                        priority TEXT DEFAULT 'medium'
                    )
                ''')
            else:
                # Work with existing schema, ensure required columns exist
                cursor.execute("PRAGMA table_info(complaints)")
                columns = [row[1] for row in cursor.fetchall()]
                
                required_columns = {
                    'potholes_detected': 'INTEGER DEFAULT 0',
                    'detection_results': 'TEXT',
                    'annotated_image_path': 'TEXT'
                }
                
                for column, definition in required_columns.items():
                    if column not in columns:
                        try:
                            cursor.execute(f'ALTER TABLE complaints ADD COLUMN {column} {definition}')
                        except:
                            pass  # Column might already exist
            
            # Notifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complaint_id INTEGER,
                    notification_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (complaint_id) REFERENCES complaints (id)
                )
            ''')
            
            # Detections table (for individual pothole detections)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complaint_id INTEGER,
                    bbox_x1 INTEGER,
                    bbox_y1 INTEGER,
                    bbox_x2 INTEGER,
                    bbox_y2 INTEGER,
                    confidence REAL,
                    class_id INTEGER,
                    FOREIGN KEY (complaint_id) REFERENCES complaints (id)
                )
            ''')
            
            conn.commit()
    
    def save_complaint(self, image_path, detection_results):
        """
        Save a complaint to the database
        
        Args:
            image_path (str): Path to the uploaded image
            detection_results (dict): Results from pothole detection
            
        Returns:
            int: Complaint ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert complaint
            cursor.execute('''
                INSERT INTO complaints 
                (image_path, annotated_image_path, potholes_detected, detection_results)
                VALUES (?, ?, ?, ?)
            ''', (
                image_path,
                detection_results.get('annotated_image', ''),
                detection_results.get('potholes_detected', 0),
                json.dumps(detection_results)
            ))
            
            complaint_id = cursor.lastrowid
            
            # Save individual detections
            detections = detection_results.get('detections', [])
            for detection in detections:
                bbox = detection.get('bbox', [])
                if len(bbox) == 4:
                    cursor.execute('''
                        INSERT INTO detections 
                        (complaint_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, confidence, class_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        complaint_id,
                        bbox[0], bbox[1], bbox[2], bbox[3],
                        detection.get('confidence', 0),
                        detection.get('class_id', 0)
                    ))
            
            conn.commit()
            return complaint_id
    
    def get_complaint(self, complaint_id):
        """
        Get a specific complaint by ID
        
        Args:
            complaint_id (int): Complaint ID
            
        Returns:
            dict: Complaint data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM complaints WHERE id = ?
            ''', (complaint_id,))
            
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                complaint = dict(zip(columns, row))
                
                # Parse detection results JSON
                if complaint['detection_results']:
                    complaint['detection_results'] = json.loads(complaint['detection_results'])
                
                return complaint
            return None
    
    def get_all_complaints(self):
        """
        Get all complaints from the database
        
        Returns:
            list: List of complaint dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM complaints ORDER BY timestamp DESC
            ''')
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            complaints = []
            for row in rows:
                complaint = dict(zip(columns, row))
                
                # Parse detection results JSON
                if complaint['detection_results']:
                    try:
                        complaint['detection_results'] = json.loads(complaint['detection_results'])
                    except:
                        complaint['detection_results'] = {}
                
                complaints.append(complaint)
            
            return complaints
    
    def save_notification(self, complaint_id, notification_type, status, message):
        """
        Save notification status to database
        
        Args:
            complaint_id (int): Related complaint ID
            notification_type (str): Type of notification (email, whatsapp, sms)
            status (str): Status (success, failed)
            message (str): Status message
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notifications 
                (complaint_id, notification_type, status, message)
                VALUES (?, ?, ?, ?)
            ''', (complaint_id, notification_type, status, message))
            conn.commit()
    
    def get_notifications(self, complaint_id=None):
        """
        Get notifications from database
        
        Args:
            complaint_id (int, optional): Filter by complaint ID
            
        Returns:
            list: List of notification dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if complaint_id:
                cursor.execute('''
                    SELECT * FROM notifications 
                    WHERE complaint_id = ? 
                    ORDER BY timestamp DESC
                ''', (complaint_id,))
            else:
                cursor.execute('''
                    SELECT * FROM notifications 
                    ORDER BY timestamp DESC
                ''')
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            notifications = []
            for row in rows:
                notification = dict(zip(columns, row))
                notifications.append(notification)
            
            return notifications
    
    def update_complaint_status(self, complaint_id, status):
        """
        Update complaint status
        
        Args:
            complaint_id (int): Complaint ID
            status (str): New status (pending, in_progress, resolved, rejected)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE complaints SET status = ? WHERE id = ?
            ''', (status, complaint_id))
            conn.commit()
    
    def get_statistics(self):
        """
        Get database statistics
        
        Returns:
            dict: Statistics about complaints and detections
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total complaints
            cursor.execute('SELECT COUNT(*) FROM complaints')
            total_complaints = cursor.fetchone()[0]
            
            # Total potholes detected
            cursor.execute('SELECT SUM(potholes_detected) FROM complaints')
            total_potholes = cursor.fetchone()[0] or 0
            
            # Complaints by status
            cursor.execute('''
                SELECT status, COUNT(*) FROM complaints 
                GROUP BY status
            ''')
            status_counts = dict(cursor.fetchall())
            
            # Recent complaints (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM complaints 
                WHERE timestamp >= datetime('now', '-7 days')
            ''')
            recent_complaints = cursor.fetchone()[0]
            
            return {
                'total_complaints': total_complaints,
                'total_potholes': total_potholes,
                'status_counts': status_counts,
                'recent_complaints': recent_complaints
            }
    
    def export_to_csv(self, output_path):
        """
        Export complaints data to CSV
        
        Args:
            output_path (str): Path for output CSV file
        """
        import csv
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM complaints')
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                columns = [description[0] for description in cursor.description]
                writer.writerow(columns)
                
                # Write data
                for row in cursor:
                    writer.writerow(row)