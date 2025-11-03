#!/usr/bin/env python3
"""
Simple Mumbai Ward Office Database for CivicSightAI
Contains major BMC ward offices with their coordinates and contact information
"""

import math
import json
from typing import Dict, List, Optional, Tuple

class MumbaiWardOffices:
    """Simple Mumbai Ward Office locator"""
    
    def __init__(self):
        # Major Mumbai BMC Ward Offices with coordinates and emails
        self.ward_offices = [
            {
                "name": "A Ward Office (Fort/Churchgate)",
                "area": "Fort, Churchgate, Colaba",
                "latitude": 18.9220,
                "longitude": 72.8347,
                "email": "ward.a@mcgm.gov.in",
                "phone": "+91-22-2266-0502"
            },
            {
                "name": "B Ward Office (Dongri/Mohammad Ali Road)",
                "area": "Dongri, Mohammad Ali Road, Bhendi Bazaar",
                "latitude": 18.9569,
                "longitude": 72.8302,
                "email": "ward.b@mcgm.gov.in",
                "phone": "+91-22-2373-4911"
            },
            {
                "name": "C Ward Office (Marine Lines/Charni Road)",
                "area": "Marine Lines, Charni Road, Girgaon",
                "latitude": 18.9446,
                "longitude": 72.8226,
                "email": "ward.c@mcgm.gov.in",
                "phone": "+91-22-2201-5064"
            },
            {
                "name": "D Ward Office (Grant Road/Mumbai Central)",
                "area": "Grant Road, Mumbai Central, Tardeo",
                "latitude": 18.9689,
                "longitude": 72.8103,
                "email": "ward.d@mcgm.gov.in",
                "phone": "+91-22-2386-2251"
            },
            {
                "name": "E Ward Office (Byculla/Mazgaon)",
                "area": "Byculla, Mazgaon, Sewri",
                "latitude": 18.9756,
                "longitude": 72.8344,
                "email": "ward.e@mcgm.gov.in",
                "phone": "+91-22-2373-2081"
            },
            {
                "name": "F North Ward Office (Matunga/King Circle)",
                "area": "Matunga, King Circle, Mahim",
                "latitude": 19.0412,
                "longitude": 72.8570,
                "email": "ward.fn.matunga@mcgm.gov.in",
                "phone": "+91-22-2414-5821"
            },
            {
                "name": "F South Ward Office (Parel/Lalbaug)",
                "area": "Parel, Lalbaug, Chinchpokli",
                "latitude": 19.0096,
                "longitude": 72.8314,
                "email": "ward.fs.parel@mcgm.gov.in",
                "phone": "+91-22-2416-2394"
            },
            {
                "name": "G North Ward Office (Dadar West/Shivaji Park)",
                "area": "Dadar West, Shivaji Park, Worli",
                "latitude": 19.0178,
                "longitude": 72.8446,
                "email": "ward.gn.dadar@mcgm.gov.in",
                "phone": "+91-22-2430-2585"
            },
            {
                "name": "G South Ward Office (Worli/Lower Parel)",
                "area": "Worli, Lower Parel, Elphinstone Road",
                "latitude": 19.0135,
                "longitude": 72.8184,
                "email": "ward.gs.worli@mcgm.gov.in",
                "phone": "+91-22-2493-8627"
            },
            {
                "name": "H East Ward Office (Bandra East/Khar East)",
                "area": "Bandra East, Khar East, Santa Cruz East",
                "latitude": 19.0596,
                "longitude": 72.8656,
                "email": "ward.he.bandra@mcgm.gov.in",
                "phone": "+91-22-2642-3891"
            },
            {
                "name": "H West Ward Office (Bandra West/Khar West)",
                "area": "Bandra West, Khar West, Santa Cruz West",
                "latitude": 19.0544,
                "longitude": 72.8269,
                "email": "ward.hw.bandra@mcgm.gov.in",
                "phone": "+91-22-2640-7292"
            },
            {
                "name": "K East Ward Office (Andheri East)",
                "area": "Andheri East, Chakala, Marol",
                "latitude": 19.1136,
                "longitude": 72.8697,
                "email": "ward.ke.andheri@mcgm.gov.in",
                "phone": "+91-22-2836-4521"
            },
            {
                "name": "K West Ward Office (Andheri West/Juhu)",
                "area": "Andheri West, Juhu, Versova",
                "latitude": 19.1368,
                "longitude": 72.8267,
                "email": "ward.kw.andheri@mcgm.gov.in",
                "phone": "+91-22-2673-9281"
            },
            {
                "name": "L Ward Office (Kurla/Ghatkopar)",
                "area": "Kurla, Ghatkopar, Chembur",
                "latitude": 19.0728,
                "longitude": 72.8826,
                "email": "ward.l.kurla@mcgm.gov.in",
                "phone": "+91-22-2522-8934"
            },
            {
                "name": "M East Ward Office (Mankhurd/Govandi)",
                "area": "Mankhurd, Govandi, Shivaji Nagar",
                "latitude": 19.0434,
                "longitude": 72.9342,
                "email": "ward.me.mankhurd@mcgm.gov.in",
                "phone": "+91-22-2551-7485"
            },
            {
                "name": "M West Ward Office (Chembur/Tilak Nagar)",
                "area": "Chembur, Tilak Nagar, VN Purav Marg",
                "latitude": 19.0622,
                "longitude": 72.8972,
                "email": "ward.mw.chembur@mcgm.gov.in",
                "phone": "+91-22-2522-4176"
            },
            {
                "name": "N Ward Office (Ghatkopar East/Vikhroli)",
                "area": "Ghatkopar East, Vikhroli, Bhandup",
                "latitude": 19.0863,
                "longitude": 72.9065,
                "email": "ward.n.ghatkopar@mcgm.gov.in",
                "phone": "+91-22-2501-3794"
            },
            {
                "name": "P North Ward Office (Malad East/Kurar)",
                "area": "Malad East, Kurar, Akurli",
                "latitude": 19.1872,
                "longitude": 72.8492,
                "email": "ward.pn.malad@mcgm.gov.in",
                "phone": "+91-22-2888-6521"
            },
            {
                "name": "P South Ward Office (Goregaon East/Aarey)",
                "area": "Goregaon East, Aarey Colony, Film City",
                "latitude": 19.1553,
                "longitude": 72.8631,
                "email": "ward.ps.goregaon@mcgm.gov.in",
                "phone": "+91-22-2841-2956"
            },
            {
                "name": "R Central Ward Office (Borivali West)",
                "area": "Borivali West, Kandivali West, Dahisar West",
                "latitude": 19.2307,
                "longitude": 72.8567,
                "email": "ward.rc.borivali@mcgm.gov.in",
                "phone": "+91-22-2892-3741"
            },
            {
                "name": "R North Ward Office (Dahisar/Mira Road)",
                "area": "Dahisar, Mira Road, Bhayander",
                "latitude": 19.2544,
                "longitude": 72.8656,
                "email": "ward.rn.dahisar@mcgm.gov.in",
                "phone": "+91-22-2895-6283"
            },
            {
                "name": "R South Ward Office (Kandivali East)",
                "area": "Kandivali East, Borivali East, Poisar",
                "latitude": 19.2047,
                "longitude": 72.8681,
                "email": "ward.rs.kandivali@mcgm.gov.in",
                "phone": "+91-22-2867-4192"
            },
            {
                "name": "S Ward Office (Bhandup/Mulund)",
                "area": "Bhandup, Mulund, Kanjurmarg",
                "latitude": 19.1367,
                "longitude": 72.9356,
                "email": "ward.s.bhandup@mcgm.gov.in",
                "phone": "+91-22-2594-7381"
            },
            {
                "name": "T Ward Office (Mulund East/Nahur)",
                "area": "Mulund East, Nahur, Bhandup East",
                "latitude": 19.1728,
                "longitude": 72.9548,
                "email": "ward.t.mulund@mcgm.gov.in",
                "phone": "+91-22-2164-8529"
            }
        ]
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        Returns distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r
    
    def find_nearest_ward(self, latitude: float, longitude: float, max_distance_km: float = 20) -> Optional[Dict]:
        """
        Find the nearest BMC ward office for given coordinates
        
        Args:
            latitude: Complaint latitude
            longitude: Complaint longitude  
            max_distance_km: Maximum search radius in kilometers
            
        Returns:
            Dictionary containing nearest ward office info or None
        """
        if not self.ward_offices:
            return None
            
        nearest_ward = None
        min_distance = float('inf')
        
        for ward in self.ward_offices:
            distance = self.haversine_distance(
                latitude, longitude,
                ward['latitude'], ward['longitude']
            )
            
            if distance < min_distance and distance <= max_distance_km:
                min_distance = distance
                nearest_ward = ward.copy()
                nearest_ward['distance_km'] = round(distance, 2)
        
        return nearest_ward
    
    def get_all_wards(self) -> List[Dict]:
        """Get all ward offices"""
        return self.ward_offices
    
    def get_ward_by_name(self, name: str) -> Optional[Dict]:
        """Get ward office by name"""
        for ward in self.ward_offices:
            if name.lower() in ward['name'].lower():
                return ward
        return None