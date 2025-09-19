#!/usr/bin/env python3
"""
Mumbai Ward Offices KML Parser for CivicSightAI
This module parses KML files containing Mumbai ward office locations and contact details.
"""

import json
import os
from fastkml import kml
from typing import List, Dict, Any, Optional
import psycopg2
import psycopg2.extras
from config import config
from math import radians, cos, sin, asin, sqrt

class WardOfficeParser:
    def __init__(self):
        self.ward_offices = []
    
    def parse_ward_offices_kml(self, kml_path: str) -> List[Dict[str, Any]]:
        """
        Parse Mumbai Ward Offices KML file and extract locations with contact details
        
        Args:
            kml_path (str): Path to the KML file
            
        Returns:
            List[Dict[str, Any]]: List of ward office data
        """
        if not os.path.exists(kml_path):
            raise FileNotFoundError(f"KML file not found: {kml_path}")
        
        with open(kml_path, 'rt', encoding='utf-8') as f:
            doc = f.read()

        k = kml.KML()
        k.from_string(doc)

        ward_offices = []

        # Alternative parsing approach using lxml directly if fastkml fails
        try:
            from lxml import etree
            root = etree.fromstring(doc.encode())
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            placemarks = root.xpath('//kml:Placemark', namespaces=ns)
            
            for placemark_elem in placemarks:
                office_data = self._extract_placemark_from_xml(placemark_elem, ns)
                if office_data:
                    ward_offices.append(office_data)
                    
        except ImportError:
            # Fallback to fastkml approach
            # Navigate through KML structure: Document > Folder > Placemarks 
            for feature in k.features:
                if hasattr(feature, 'features'):
                    for f2 in feature.features:
                        if hasattr(f2, 'features'):
                            for placemark in f2.features:
                                office_data = self._extract_placemark_data(placemark)
                                if office_data:
                                    ward_offices.append(office_data)
                else:
                    # Handle case where placemarks are directly under the document
                    office_data = self._extract_placemark_data(feature)
                    if office_data:
                        ward_offices.append(office_data)

        self.ward_offices = ward_offices
        return ward_offices
    
    def _extract_placemark_data(self, placemark) -> Optional[Dict[str, Any]]:
        """Extract data from a KML placemark"""
        try:
            name = placemark.name
            geom = placemark.geometry
            
            if not name or not geom:
                return None
            
            # Extract coordinates
            coords = geom.coords[0] if hasattr(geom, 'coords') and geom.coords else None
            if not coords:
                return None
            
            longitude, latitude = coords[0], coords[1]
            
            # Extract extended data like contact details
            contact_details = {}
            if hasattr(placemark, 'extended_data') and placemark.extended_data:
                if hasattr(placemark.extended_data, 'elements') and placemark.extended_data.elements:
                    for data in placemark.extended_data.elements:
                        if hasattr(data, 'name') and hasattr(data, 'value'):
                            contact_details[data.name] = data.value
            
            # Also check description for additional data
            description = placemark.description if hasattr(placemark, 'description') else ""
            
            return {
                'name': name,
                'latitude': latitude,
                'longitude': longitude,
                'geometry': geom.wkt if hasattr(geom, 'wkt') else f"POINT({longitude} {latitude})",
                'contact_details': contact_details,
                'description': description
            }
            
        except Exception as e:
            print(f"Error extracting placemark data: {e}")
            return None
    
    def _extract_placemark_from_xml(self, placemark_elem, namespaces) -> Optional[Dict[str, Any]]:
        """Extract data from a KML placemark XML element using lxml"""
        try:
            # Get name
            name_elem = placemark_elem.find('.//kml:name', namespaces)
            name = name_elem.text if name_elem is not None else None
            
            if not name:
                return None
            
            # Get coordinates from Point
            coords_elem = placemark_elem.find('.//kml:coordinates', namespaces)
            if coords_elem is None:
                return None
                
            coords_text = coords_elem.text.strip()
            coords_parts = coords_text.split(',')
            
            if len(coords_parts) < 2:
                return None
                
            longitude = float(coords_parts[0])
            latitude = float(coords_parts[1])
            
            # Extract extended data
            contact_details = {}
            extended_data = placemark_elem.find('.//kml:ExtendedData', namespaces)
            if extended_data is not None:
                for data_elem in extended_data.findall('.//kml:Data', namespaces):
                    data_name = data_elem.get('name')
                    value_elem = data_elem.find('.//kml:value', namespaces)
                    if data_name and value_elem is not None:
                        contact_details[data_name] = value_elem.text
            
            # Get description
            desc_elem = placemark_elem.find('.//kml:description', namespaces)
            description = desc_elem.text if desc_elem is not None else ""
            
            return {
                'name': name,
                'latitude': latitude,
                'longitude': longitude,
                'coordinates': [longitude, latitude],  # For consistency
                'geometry': f"POINT({longitude} {latitude})",
                'contact_details': contact_details,
                'description': description
            }
            
        except Exception as e:
            print(f"Error extracting placemark from XML: {e}")
            return None
    
    def save_to_json(self, output_path: str):
        """Save ward offices data to JSON file"""
        with open(output_path, "w", encoding='utf-8') as json_file:
            json.dump(self.ward_offices, json_file, indent=4, ensure_ascii=False)
        print(f"Ward offices data saved to {output_path}")
    
    def save_to_database(self):
        """Save ward offices data to PostgreSQL database"""
        conn = psycopg2.connect(**config['default'].DATABASE_CONFIG)
        
        try:
            cursor = conn.cursor()
            
            # Create ward offices table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ward_offices (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    location GEOMETRY(POINT, 4326),
                    contact_details JSONB,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create spatial index
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ward_offices_location 
                ON ward_offices USING GIST(location)
            ''')
            
            # Clear existing data
            cursor.execute('DELETE FROM ward_offices')
            
            # Insert ward offices data
            for office in self.ward_offices:
                cursor.execute('''
                    INSERT INTO ward_offices (name, location, contact_details, description)
                    VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)
                ''', (
                    office['name'],
                    office['longitude'],
                    office['latitude'],
                    json.dumps(office['contact_details']),
                    office['description']
                ))
            
            conn.commit()
            print(f"Successfully saved {len(self.ward_offices)} ward offices to database")
            
        except Exception as e:
            conn.rollback()
            print(f"Error saving to database: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def find_nearest_ward_office(self, latitude: float, longitude: float, max_distance_km: float = 10) -> Optional[Dict[str, Any]]:
        """
        Find the nearest ward office to given coordinates
        
        Args:
            latitude (float): Complaint latitude
            longitude (float): Complaint longitude  
            max_distance_km (float): Maximum search distance in kilometers
            
        Returns:
            Optional[Dict[str, Any]]: Nearest ward office data with distance
        """
        if not self.ward_offices:
            return None
        
        nearest_office = None
        min_distance = float('inf')
        
        for office in self.ward_offices:
            distance = self._haversine_distance(
                latitude, longitude,
                office['latitude'], office['longitude']
            )
            
            if distance < min_distance and distance <= max_distance_km:
                min_distance = distance
                nearest_office = office.copy()
                nearest_office['distance_km'] = round(distance, 2)
        
        return nearest_office
    
    def find_nearest_ward_office_db(self, latitude: float, longitude: float, max_distance_km: float = 10) -> Optional[Dict[str, Any]]:
        """
        Find the nearest ward office using PostGIS spatial queries (more efficient)
        
        Args:
            latitude (float): Complaint latitude
            longitude (float): Complaint longitude
            max_distance_km (float): Maximum search distance in kilometers
            
        Returns:
            Optional[Dict[str, Any]]: Nearest ward office data with distance
        """
        conn = psycopg2.connect(**config['default'].DATABASE_CONFIG)
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Use PostGIS ST_Distance with geography for accurate distance calculation
            cursor.execute('''
                SELECT id, name, contact_details, description,
                       ST_X(location) as longitude, ST_Y(location) as latitude,
                       ST_Distance(
                           location::geography, 
                           ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                       ) / 1000 as distance_km
                FROM ward_offices
                WHERE ST_Distance(
                    location::geography, 
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) <= %s * 1000
                ORDER BY distance_km
                LIMIT 1
            ''', (longitude, latitude, longitude, latitude, max_distance_km))
            
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            else:
                return None
                
        except Exception as e:
            print(f"Database error finding nearest ward office: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth (in kilometers)
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of Earth in kilometers
        r = 6371
        return c * r

def main():
    """Example usage of the WardOfficeParser"""
    parser = WardOfficeParser()
    
    # Path to your KML file
    kml_file_path = "mumbai_ward_offices.kml"
    
    if not os.path.exists(kml_file_path):
        print(f"KML file not found: {kml_file_path}")
        print("Please download the Mumbai Ward Offices KML file and place it in the project directory.")
        return
    
    try:
        # Parse KML file
        print("Parsing Mumbai Ward Offices KML file...")
        ward_offices = parser.parse_ward_offices_kml(kml_file_path)
        print(f"Found {len(ward_offices)} ward offices")
        
        # Save to JSON
        parser.save_to_json("ward_offices_data.json")
        
        # Save to database
        print("Saving to PostgreSQL database...")
        parser.save_to_database()
        
        # Example: Find nearest ward office
        test_lat, test_lng = 19.0760, 72.8777  # Mumbai coordinates
        nearest = parser.find_nearest_ward_office_db(test_lat, test_lng)
        
        if nearest:
            print(f"\nNearest ward office to test coordinates:")
            print(f"Name: {nearest['name']}")
            print(f"Distance: {nearest['distance_km']} km")
            print(f"Contact: {nearest.get('contact_details', {})}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
