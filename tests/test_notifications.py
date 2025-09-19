#!/usr/bin/env python3
"""
Test script for CivicSightAI notification system
This script demonstrates the email and Green API WhatsApp notification capabilities.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app import app, send_email, send_whatsapp_greenapi, send_complaint_notifications

def test_email_notification():
    """Test email notification functionality"""
    print("Testing Email Notification...")
    
    with app.app_context():
        # Test basic email
        success = send_email(
            to_email="test@example.com",
            subject="CivicSightAI Test Email",
            body="This is a test email from CivicSightAI notification system."
        )
        
        if success:
            print("✅ Email notification configured successfully!")
        else:
            print("❌ Email notification failed - check your configuration")
    
    return success

def test_greenapi_whatsapp_notification():
    """Test Green API WhatsApp notification functionality"""
    print("\nTesting Green API WhatsApp Notification...")
    
    if not app.config.get('ENABLE_GREENAPI_WHATSAPP'):
        print("⚠️  Green API WhatsApp notifications are disabled in configuration")
        return False
    
    if not app.config.get('GREENAPI_ID_INSTANCE'):
        print("❌ Green API not configured - missing credentials")
        return False
    
    # Use your WhatsApp number for testing
    test_phone = "+919028075890"  # Replace with your WhatsApp number
    
    success = send_whatsapp_greenapi(
        to_phone=test_phone,
        message="🤖 Test WhatsApp message from CivicSightAI via Green API!\n\nYour pothole complaint has been received and is being processed."
    )
    
    if success:
        print("✅ Green API WhatsApp notification configured successfully!")
    else:
        print("❌ Green API WhatsApp notification failed - check your configuration")
    
    return success

def test_full_complaint_workflow():
    """Test the complete complaint notification workflow"""
    print("\nTesting Complete Complaint Notification Workflow...")
    
    # Sample complaint data
    complaint_data = {
        'id': 'TEST001',
        'description': 'Large pothole detected on Main Street',
        'category': 'pothole',
        'location_text': 'Main Street & 1st Avenue',
        'latitude': 40.7128,
        'longitude': -74.0060,
        'status': 'pending',
        'created_at': '2025-01-01 12:00:00',
        'citizen_name': 'John Doe',
        'citizen_phone': '+15005550006',
        'citizen_email': 'john.doe@example.com'
    }
    
    # Sample ward office data
    ward_office = {
        'name': 'Manhattan Ward Office',
        'contact_details': {
            'email': 'ward.manhattan@example.com',
            'phone': '+1234567890'
        }
    }
    
    with app.app_context():
        success = send_complaint_notifications(complaint_data, ward_office)
        
        if success:
            print("✅ Complete complaint notification workflow test passed!")
        else:
            print("❌ Complete complaint notification workflow test failed!")
    
    return success

def print_configuration_status():
    """Print current configuration status"""
    print("=== CivicSightAI Notification Configuration Status ===")
    
    # Email configuration
    email_configured = bool(app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'))
    email_enabled = app.config.get('ENABLE_EMAIL_NOTIFICATIONS', False)
    print(f"Email Notifications: {'✅ Configured' if email_configured else '❌ Not Configured'} | {'✅ Enabled' if email_enabled else '❌ Disabled'}")
    
    # Green API WhatsApp configuration
    greenapi_configured = bool(app.config.get('GREENAPI_ID_INSTANCE') and app.config.get('GREENAPI_API_TOKEN'))
    greenapi_enabled = app.config.get('ENABLE_GREENAPI_WHATSAPP', False)
    print(f"Green API WhatsApp: {'✅ Configured' if greenapi_configured else '❌ Not Configured'} | {'✅ Enabled' if greenapi_enabled else '❌ Disabled'}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("CivicSightAI Notification System Test")
    print("="*50)
    
    # Load environment variables
    load_dotenv()
    
    # Print configuration status
    print_configuration_status()
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_email_notification():
        tests_passed += 1
    
    if test_greenapi_whatsapp_notification():
        tests_passed += 1
    
    if test_full_complaint_workflow():
        tests_passed += 1
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All notification tests passed! Your system is ready.")
    else:
        print("⚠️  Some tests failed. Please check your configuration in .env file.")
        print("\nTo configure notifications:")
        print("1. Update .env with your Green API credentials")
        print("2. Set ENABLE_GREENAPI_WHATSAPP=true")
        print("3. Run this test script again")
