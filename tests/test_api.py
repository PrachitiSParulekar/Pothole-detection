#!/usr/bin/env python3
"""
Test script for the CivicSightAI REST API endpoints
This script demonstrates how to use the new POST and GET endpoints
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def test_post_complaint():
    """Test POST /api/complaints endpoint"""
    print("Testing POST /api/complaints...")
    
    # Sample complaint data
    complaint_data = {
        "description": "Large pothole on Main Street causing vehicle damage",
        "category": "pothole",
        "status": "pending",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "location_text": "Main Street, New York, NY",
        "photo_path": "uploads/sample_pothole.jpg"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/complaints",
            json=complaint_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            return response.json().get('id')
        else:
            print("Error creating complaint")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_get_complaints_geojson():
    """Test GET /api/complaints (GeoJSON format)"""
    print("\nTesting GET /api/complaints (GeoJSON format)...")
    
    try:
        response = requests.get(f"{API_BASE}/complaints")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Type: {data.get('type')}")
            print(f"Features count: {len(data.get('features', []))}")
            
            # Show first feature if available
            if data.get('features'):
                first_feature = data['features'][0]
                print(f"First complaint ID: {first_feature['properties']['id']}")
                print(f"Description: {first_feature['properties']['description'][:50]}...")
        else:
            print(f"Error: {response.json()}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_get_complaints_simple():
    """Test GET /api/complaints/simple (Simple JSON format)"""
    print("\nTesting GET /api/complaints/simple (Simple JSON format)...")
    
    try:
        response = requests.get(f"{API_BASE}/complaints/simple")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Complaints count: {len(data)}")
            
            # Show first complaint if available
            if data:
                first_complaint = data[0]
                print(f"First complaint ID: {first_complaint['id']}")
                print(f"Description: {first_complaint['description'][:50]}...")
                print(f"Location: {first_complaint['location']}")
        else:
            print(f"Error: {response.json()}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_post_minimal_complaint():
    """Test POST with minimal required fields"""
    print("\nTesting POST /api/complaints (minimal data)...")
    
    # Minimal complaint data
    complaint_data = {
        "description": "Small pothole detected",
        "latitude": 40.7589,
        "longitude": -73.9851
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/complaints",
            json=complaint_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_post_invalid_data():
    """Test POST with invalid data to test error handling"""
    print("\nTesting POST /api/complaints (invalid data)...")
    
    # Invalid complaint data (missing required fields)
    complaint_data = {
        "description": "Missing coordinates"
        # Missing latitude and longitude
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/complaints",
            json=complaint_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_get_complaint_by_id(complaint_id):
    """Test GET /api/complaints/{id}"""
    if not complaint_id:
        print("\nSkipping GET complaint by ID test (no complaint ID available)")
        return
        
    print(f"\nTesting GET /api/complaints/{complaint_id}...")
    
    try:
        response = requests.get(f"{API_BASE}/complaints/{complaint_id}")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Complaint ID: {data['id']}")
            print(f"Description: {data['description'][:50]}...")
            print(f"Status: {data['status']}")
        else:
            print(f"Error: {response.json()}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_get_nonexistent_complaint():
    """Test GET /api/complaints/{id} with non-existent ID"""
    print(f"\nTesting GET /api/complaints/nonexistent...")
    
    try:
        response = requests.get(f"{API_BASE}/complaints/nonexist")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    print("CivicSightAI REST API Test Script")
    print("=" * 40)
    print("Make sure the Flask app is running on http://localhost:5000")
    print()
    
    # Test all endpoints
    complaint_id = test_post_complaint()
    test_get_complaints_geojson()
    test_get_complaints_simple()
    test_get_complaint_by_id(complaint_id)
    test_get_nonexistent_complaint()
    test_post_minimal_complaint()
    test_post_invalid_data()
    
    print("\n" + "=" * 40)
    print("API testing completed!")
