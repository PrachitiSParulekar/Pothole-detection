# Notification routes for CivicSightAI
from flask import render_template, flash, request, jsonify
import psycopg2.extras
import uuid
from datetime import datetime

def register_notification_routes(app, get_db_connection, send_whatsapp_greenapi=None, send_email=None):
    """Register notification routes with the Flask app"""
    
    @app.route('/notifications')
    def view_notifications():
        """Display notification history and statistics"""
        try:
            conn = get_db_connection()
            if conn is None:
                flash("Database connection failed", "danger")
                return render_template('notifications.html', notifications=[], total_notifications=0, stats={})
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get recent notifications
            cursor.execute('''
                SELECT *
                FROM notification_logs
                ORDER BY sent_at DESC
                LIMIT 100
            ''')
            
            notifications = cursor.fetchall()
            
            # Get notification statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent_count,
                    SUM(CASE WHEN DATE(sent_at) = CURRENT_DATE THEN 1 ELSE 0 END) as today_count
                FROM notification_logs
            ''')
            
            stats_row = cursor.fetchone()
            
            # Calculate success rate
            total = stats_row['total'] if stats_row and stats_row['total'] else 0
            sent_count = stats_row['sent_count'] if stats_row and stats_row['sent_count'] else 0
            success_rate = round((sent_count / total) * 100) if total > 0 else 0
            
            stats = {
                'success_rate': success_rate,
                'notifications_today': stats_row['today_count'] if stats_row else 0
            }
            
            # Convert to list of dictionaries and format dates
            notifications_list = []
            for notification in notifications:
                notification_dict = dict(notification)
                if notification_dict['sent_at']:
                    notification_dict['sent_at'] = notification_dict['sent_at'].strftime('%Y-%m-%d %H:%M:%S')
                notifications_list.append(notification_dict)
            
            return render_template(
                'notifications.html', 
                notifications=notifications_list, 
                total_notifications=total, 
                stats=stats
            )
            
        except Exception as e:
            print(f"Notification history error: {e}")
            flash(f"Error retrieving notification history: {e}", "danger")
            return render_template('notifications.html', notifications=[], total_notifications=0, stats={})

    @app.route('/api/test-notifications', methods=['POST'])
    def test_notifications():
        """Test endpoint to send test notifications"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            recipient = data.get('recipient')
            type_to_test = data.get('type', 'all')
            
            if not recipient:
                return jsonify({'error': 'No recipient provided'}), 400
                
            results = {}
            test_id = str(uuid.uuid4())
            
            # Test WhatsApp
            if type_to_test in ['all', 'whatsapp'] and send_whatsapp_greenapi:
                try:
                    whatsapp_result = send_whatsapp_greenapi(
                        recipient, 
                        f"This is a test WhatsApp message from CivicSightAI. Test ID: {test_id}"
                    )
                    results['whatsapp'] = {
                        'success': bool(whatsapp_result),
                        'details': whatsapp_result
                    }
                except Exception as e:
                    results['whatsapp'] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Test Email
            if type_to_test in ['all', 'email'] and '@' in recipient and send_email:
                try:
                    email_result = send_email(
                        recipient, 
                        "CivicSightAI Test Email", 
                        f"This is a test email from CivicSightAI notification system. Test ID: {test_id}"
                    )
                    results['email'] = {
                        'success': bool(email_result),
                        'details': True
                    }
                except Exception as e:
                    results['email'] = {
                        'success': False,
                        'error': str(e)
                    }
                    
            return jsonify({
                'success': True,
                'test_id': test_id,
                'results': results
            })
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app
