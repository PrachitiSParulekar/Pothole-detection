import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from whatsapp_api_client_python.API import GreenAPI
import requests
import json

load_dotenv()

class NotificationService:
    def __init__(self):
        """Initialize notification service with configuration from environment variables"""
        self.email_enabled = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
        self.whatsapp_enabled = os.getenv('ENABLE_WHATSAPP_NOTIFICATIONS', 'false').lower() == 'true'
        self.greenapi_enabled = os.getenv('ENABLE_GREENAPI_WHATSAPP', 'false').lower() == 'true'
        
        # Email configuration
        self.mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        self.mail_port = int(os.getenv('MAIL_PORT', 587))
        self.mail_username = os.getenv('MAIL_USERNAME')
        self.mail_password = os.getenv('MAIL_PASSWORD')
        self.mail_use_tls = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
        
        # WhatsApp (Green API) configuration
        self.greenapi_id = os.getenv('GREENAPI_ID_INSTANCE')
        self.greenapi_token = os.getenv('GREENAPI_API_TOKEN_INSTANCE')
        
        if self.greenapi_enabled and self.greenapi_id and self.greenapi_token:
            self.greenapi = GreenAPI(self.greenapi_id, self.greenapi_token)
    
    def send_notifications(self, detection_results, complaint_id):
        """
        Send notifications about pothole detection
        
        Args:
            detection_results (dict): Results from pothole detection
            complaint_id (int): Unique complaint identifier
        """
        message = self.create_notification_message(detection_results, complaint_id)
        
        notifications_sent = []
        
        # Send email notification
        if self.email_enabled:
            email_result = self.send_email_notification(message, complaint_id)
            notifications_sent.append({
                'type': 'email',
                'success': email_result['success'],
                'message': email_result['message']
            })
        
        # Send WhatsApp notification via Green API
        if self.greenapi_enabled:
            whatsapp_result = self.send_whatsapp_notification(message)
            notifications_sent.append({
                'type': 'whatsapp',
                'success': whatsapp_result['success'],
                'message': whatsapp_result['message']
            })
        
        return notifications_sent
    
    def create_notification_message(self, detection_results, complaint_id):
        """
        Create a formatted notification message
        
        Args:
            detection_results (dict): Results from pothole detection
            complaint_id (int): Unique complaint identifier
            
        Returns:
            dict: Formatted message components
        """
        pothole_count = detection_results.get('potholes_detected', 0)
        timestamp = detection_results.get('timestamp', 'Unknown')
        
        subject = f"🚨 Pothole Alert - Complaint #{complaint_id}"
        
        body = f"""
CivicSight AI - Pothole Detection Alert

Complaint ID: #{complaint_id}
Detection Time: {timestamp}
Potholes Detected: {pothole_count}

A new pothole has been detected and reported through the CivicSight AI system.
This requires immediate attention from the municipal authorities.

Location: [Location data would be added here if GPS is available]
Confidence Level: High

Please take appropriate action to address this road safety concern.

Thank you,
CivicSight AI System
        """
        
        return {
            'subject': subject,
            'body': body,
            'complaint_id': complaint_id,
            'pothole_count': pothole_count
        }
    
    def send_email_notification(self, message, complaint_id):
        """
        Send email notification
        
        Args:
            message (dict): Message components
            complaint_id (int): Complaint ID
            
        Returns:
            dict: Result of email sending
        """
        if not all([self.mail_username, self.mail_password]):
            return {
                'success': False,
                'message': 'Email credentials not configured'
            }
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.mail_username
            msg['To'] = self.mail_username  # Sending to same email for demo
            msg['Subject'] = message['subject']
            
            msg.attach(MIMEText(message['body'], 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.mail_server, self.mail_port)
            if self.mail_use_tls:
                server.starttls()
            server.login(self.mail_username, self.mail_password)
            
            text = msg.as_string()
            server.sendmail(self.mail_username, self.mail_username, text)
            server.quit()
            
            return {
                'success': True,
                'message': f'Email notification sent successfully for complaint #{complaint_id}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}'
            }
    
    def send_whatsapp_notification(self, message):
        """
        Send WhatsApp notification using Green API
        
        Args:
            message (dict): Message components
            
        Returns:
            dict: Result of WhatsApp sending
        """
        if not self.greenapi_enabled or not hasattr(self, 'greenapi'):
            return {
                'success': False,
                'message': 'WhatsApp API not configured'
            }
        
        try:
            # Format message for WhatsApp
            whatsapp_message = f"🚨 *{message['subject']}*\n\n{message['body']}"
            
            # Send to yourself for demo (replace with actual recipient)
            result = self.greenapi.sending.sendMessage(
                'your_phone_number@c.us',  # Replace with actual recipient
                whatsapp_message
            )
            
            return {
                'success': True,
                'message': f'WhatsApp notification sent successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to send WhatsApp message: {str(e)}'
            }
    
    def send_sms_notification(self, message, phone_number):
        """
        Send SMS notification (placeholder - would need SMS service integration)
        
        Args:
            message (dict): Message components
            phone_number (str): Recipient phone number
            
        Returns:
            dict: Result of SMS sending
        """
        # This would integrate with an SMS service like Twilio
        return {
            'success': False,
            'message': 'SMS service not implemented'
        }
    
    def test_notifications(self):
        """
        Test all notification services
        
        Returns:
            dict: Test results for all services
        """
        test_results = {}
        
        # Test email
        if self.email_enabled:
            test_message = {
                'subject': 'CivicSight AI - Test Notification',
                'body': 'This is a test notification from CivicSight AI system.',
                'complaint_id': 'TEST',
                'pothole_count': 1
            }
            
            test_results['email'] = self.send_email_notification(test_message, 'TEST')
        
        # Test WhatsApp
        if self.greenapi_enabled:
            test_message = {
                'subject': 'CivicSight AI - Test Notification',
                'body': 'This is a test notification from CivicSight AI system.',
                'complaint_id': 'TEST',
                'pothole_count': 1
            }
            
            test_results['whatsapp'] = self.send_whatsapp_notification(test_message)
        
        return test_results