#!/usr/bin/env python3
"""
Test the CivicSightAI complaint API with notification features
This script demonstrates how to create complaints with citizen contact information
that will trigger email, SMS, and WhatsApp notifications.
"""

import requests
import json

def test_api_complaint_with_notifications():
    """Test creating a complaint via API with citizen contact info"""
    
    # API endpoint (adjust URL as needed)
    url = "http://localhost:5000/api/complaints"
    
    # Sample complaint data with citizen contact information
    complaint_data = {
        "description": "Large pothole causing traffic hazard on Main Street",
        "category": "pothole",
        "latitude": 40.7589,
        "longitude": -73.9851,
        "location_text": "Main Street & Broadway, New York",
        "citizen_name": "Jane Smith",
        "citizen_phone": "+1234567890",
        "citizen_email": "jane.smith@example.com"
    }
    
    try:
        print("Creating complaint with notification features...")
        print(f"Data: {json.dumps(complaint_data, indent=2)}")
        
        response = requests.post(url, json=complaint_data, timeout=30)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Complaint created successfully!")
            print(f"Complaint ID: {result['id']}")
            print(f"Message: {result['message']}")
            
            if 'assigned_ward_office' in result:
                ward_office = result['assigned_ward_office']
                print(f"Assigned to: {ward_office['name']}")
                print("📧 Email notification sent to ward office")
                print("📱 SMS notification sent to citizen")
                if "whatsapp" in result.get('notifications_sent', []):
                    print("💬 WhatsApp notification sent to citizen")
            
            return True
        else:
            print(f"❌ Failed to create complaint: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the Flask app is running.")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The API might be slow to respond.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_complaint_minimal():
    """Test creating a complaint with minimal data"""
    
    url = "http://localhost:5000/api/complaints"
    
    # Minimal complaint data (only required fields)
    complaint_data = {
        "description": "Small pothole on residential street",
        "latitude": 40.7504,
        "longitude": -73.9948
    }
    
    try:
        print("\nCreating minimal complaint...")
        response = requests.post(url, json=complaint_data, timeout=30)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Minimal complaint created successfully!")
            print(f"Complaint ID: {result['id']}")
            print("ℹ️  No notifications sent (no citizen contact info provided)")
            return True
        else:
            print(f"❌ Failed to create minimal complaint: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_complaints():
    """Fetch all complaints via API"""
    
    url = "http://localhost:5000/api/complaints"
    
    try:
        print("\nFetching all complaints...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            complaints = response.json()
            print(f"✅ Found {len(complaints)} complaints")
            
            for complaint in complaints[:3]:  # Show first 3
                print(f"- ID: {complaint['id']}, Status: {complaint['status']}")
                if complaint.get('citizen_name'):
                    print(f"  Citizen: {complaint['citizen_name']}")
            
            return True
        else:
            print(f"❌ Failed to fetch complaints: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("CivicSightAI API Test with Notifications")
    print("=" * 50)
    print("Make sure the Flask app is running: python app.py")
    print()
    
    # Test creating complaint with full notification data
    success1 = test_api_complaint_with_notifications()
    
    # Test creating minimal complaint
    success2 = test_api_complaint_minimal()
    
    # Test fetching complaints
    success3 = get_complaints()
    
    # Summary
    tests_passed = sum([success1, success2, success3])
    print(f"\n=== Test Summary ===")
    print(f"Tests Passed: {tests_passed}/3")
    
    if tests_passed == 3:
        print("🎉 All API tests passed!")
    else:
        print("⚠️  Some tests failed. Check the Flask app and database connection.")
