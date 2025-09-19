#!/usr/bin/env python3
"""
Setup script for Mumbai Ward Office integration
This script helps you set up the ward office functionality
"""

import os
import sys
from ward_office_parser import WardOfficeParser

def check_requirements():
    """Check if all requirements are met"""
    print("Checking requirements...")
    
    # Check if fastkml is available
    try:
        import fastkml
        print("✅ fastkml library is installed")
    except ImportError:
        print("❌ fastkml library not found. Install with: pip install fastkml")
        return False
    
    # Check database connection
    try:
        from app import get_db_connection
        conn = get_db_connection()
        if conn:
            conn.close()
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    
    return True

def create_sample_kml():
    """Create a sample KML file with Mumbai ward offices for testing"""
    sample_kml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Mumbai Ward Offices - Sample Data</name>
    <description>Sample Mumbai ward office locations for testing CivicSightAI</description>
    <Folder>
      <name>Ward Offices</name>
      <Placemark>
        <name>A Ward Office - Fort</name>
        <description>Municipal Corporation Ward A Office</description>
        <ExtendedData>
          <Data name="contact_phone">
            <value>+91-22-2266-8822</value>
          </Data>
          <Data name="contact_email">
            <value>awardfoft@mcgm.gov.in</value>
          </Data>
          <Data name="office_hours">
            <value>9:00 AM - 6:00 PM</value>
          </Data>
          <Data name="ward_code">
            <value>A</value>
          </Data>
        </ExtendedData>
        <Point>
          <coordinates>72.8347,18.9322,0</coordinates>
        </Point>
      </Placemark>
      <Placemark>
        <name>B Ward Office - Mazgaon</name>
        <description>Municipal Corporation Ward B Office</description>
        <ExtendedData>
          <Data name="contact_phone">
            <value>+91-22-2373-4455</value>
          </Data>
          <Data name="contact_email">
            <value>bwardmazgaon@mcgm.gov.in</value>
          </Data>
          <Data name="office_hours">
            <value>9:00 AM - 6:00 PM</value>
          </Data>
          <Data name="ward_code">
            <value>B</value>
          </Data>
        </ExtendedData>
        <Point>
          <coordinates>72.8493,18.9667,0</coordinates>
        </Point>
      </Placemark>
      <Placemark>
        <name>C Ward Office - Marine Lines</name>
        <description>Municipal Corporation Ward C Office</description>
        <ExtendedData>
          <Data name="contact_phone">
            <value>+91-22-2201-5566</value>
          </Data>
          <Data name="contact_email">
            <value>cwardmarine@mcgm.gov.in</value>
          </Data>
          <Data name="office_hours">
            <value>9:00 AM - 6:00 PM</value>
          </Data>
          <Data name="ward_code">
            <value>C</value>
          </Data>
        </ExtendedData>
        <Point>
          <coordinates>72.8258,18.9467,0</coordinates>
        </Point>
      </Placemark>
      <Placemark>
        <name>D Ward Office - Grant Road</name>
        <description>Municipal Corporation Ward D Office</description>
        <ExtendedData>
          <Data name="contact_phone">
            <value>+91-22-2382-7788</value>
          </Data>
          <Data name="contact_email">
            <value>dwardgrant@mcgm.gov.in</value>
          </Data>
          <Data name="office_hours">
            <value>9:00 AM - 6:00 PM</value>
          </Data>
          <Data name="ward_code">
            <value>D</value>
          </Data>
        </ExtendedData>
        <Point>
          <coordinates>72.8156,18.9625,0</coordinates>
        </Point>
      </Placemark>
      <Placemark>
        <name>K/East Ward Office - Andheri East</name>
        <description>Municipal Corporation Ward K/East Office</description>
        <ExtendedData>
          <Data name="contact_phone">
            <value>+91-22-2821-9900</value>
          </Data>
          <Data name="contact_email">
            <value>keastandheri@mcgm.gov.in</value>
          </Data>
          <Data name="office_hours">
            <value>9:00 AM - 6:00 PM</value>
          </Data>
          <Data name="ward_code">
            <value>K/E</value>
          </Data>
        </ExtendedData>
        <Point>
          <coordinates>72.8697,19.1197,0</coordinates>
        </Point>
      </Placemark>
    </Folder>
  </Document>
</kml>'''
    
    sample_file = "mumbai_ward_offices_sample.kml"
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(sample_kml_content)
    
    print(f"✅ Created sample KML file: {sample_file}")
    return sample_file

def load_ward_offices(kml_file):
    """Load ward offices from KML file into database"""
    try:
        parser = WardOfficeParser()
        
        print(f"Parsing KML file: {kml_file}")
        ward_offices = parser.parse_ward_offices_kml(kml_file)
        print(f"Found {len(ward_offices)} ward offices")
        
        print("Saving to database...")
        parser.save_to_database()
        
        print("Saving to JSON file...")
        parser.save_to_json("ward_offices_data.json")
        
        print("✅ Ward offices loaded successfully!")
        
        # Test nearest office functionality
        test_coordinates = [(19.0760, 72.8777), (18.9322, 72.8347), (19.1197, 72.8697)]
        
        print("\nTesting nearest ward office functionality:")
        for i, (lat, lng) in enumerate(test_coordinates, 1):
            nearest = parser.find_nearest_ward_office_db(lat, lng)
            if nearest:
                print(f"Test {i}: Nearest to ({lat}, {lng}) is {nearest['name']} ({nearest['distance_km']} km)")
            else:
                print(f"Test {i}: No ward office found near ({lat}, {lng})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading ward offices: {e}")
        return False

def main():
    """Main setup function"""
    print("Mumbai Ward Office Setup for CivicSightAI")
    print("=" * 45)
    
    if not check_requirements():
        print("\n❌ Setup failed. Please resolve the issues above.")
        return False
    
    # Check if KML file exists
    kml_file = "mumbai_ward_offices.kml"
    
    if os.path.exists(kml_file):
        print(f"✅ Found KML file: {kml_file}")
    else:
        print(f"❌ KML file not found: {kml_file}")
        response = input("Would you like to create a sample KML file for testing? (y/n): ")
        if response.lower().startswith('y'):
            kml_file = create_sample_kml()
        else:
            print("Please download the Mumbai Ward Offices KML file and name it 'mumbai_ward_offices.kml'")
            return False
    
    # Load ward offices
    success = load_ward_offices(kml_file)
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start your Flask app: python app.py")
        print("2. Test the new endpoints:")
        print("   - GET /api/ward-offices")
        print("   - GET /api/ward-offices/nearest?lat=19.0760&lng=72.8777")
        print("   - POST /api/complaints (now auto-assigns ward offices)")
        print("3. Use the test script: python test_ward_office_api.py")
    else:
        print("\n❌ Setup failed. Check the errors above.")
    
    return success

if __name__ == "__main__":
    main()
