import cv2
import numpy as np
from ultralytics import YOLO
import os
from datetime import datetime

class PotholeDetector:
    def __init__(self, model_path='yolov11_best.pt'):
        """Initialize the pothole detector with YOLOv11 model"""
        self.model_path = model_path
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load the YOLOv11 model"""
        try:
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                print(f"Model loaded successfully from {self.model_path}")
            else:
                print(f"Model file not found: {self.model_path}")
                # Load default model
                self.model = YOLO('yolov8n.pt')
                print("Using default YOLOv8n model")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
    
    def detect_potholes(self, image_path):
        """
        Detect potholes in the given image
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Detection results containing count, confidence, and coordinates
        """
        if not self.model:
            return {
                'error': 'Model not loaded',
                'potholes_detected': 0,
                'detections': []
            }
        
        try:
            # Read the image
            image = cv2.imread(image_path)
            if image is None:
                return {
                    'error': 'Could not read image',
                    'potholes_detected': 0,
                    'detections': []
                }
            
            # Run inference
            results = self.model(image)
            
            detections = []
            pothole_count = 0
            
            # Process results
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = box.cls[0].cpu().numpy()
                        
                        # Filter for pothole class (adjust class_id as needed)
                        if confidence > 0.5:  # Confidence threshold
                            pothole_count += 1
                            detections.append({
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'confidence': float(confidence),
                                'class_id': int(class_id)
                            })
            
            # Create annotated image
            annotated_image_path = self.create_annotated_image(image_path, detections)
            
            return {
                'potholes_detected': pothole_count,
                'detections': detections,
                'annotated_image': annotated_image_path,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f'Detection failed: {str(e)}',
                'potholes_detected': 0,
                'detections': []
            }
    
    def create_annotated_image(self, image_path, detections):
        """
        Create an annotated image with bounding boxes
        
        Args:
            image_path (str): Path to original image
            detections (list): List of detection results
            
        Returns:
            str: Path to annotated image
        """
        try:
            image = cv2.imread(image_path)
            
            # Draw bounding boxes
            for detection in detections:
                bbox = detection['bbox']
                confidence = detection['confidence']
                
                # Draw rectangle
                cv2.rectangle(image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                
                # Add confidence text
                label = f'Pothole: {confidence:.2f}'
                cv2.putText(image, label, (bbox[0], bbox[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            # Save annotated image
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            annotated_path = os.path.join(
                os.path.dirname(image_path), 
                f"{base_name}_annotated.jpg"
            )
            cv2.imwrite(annotated_path, image)
            
            return annotated_path
            
        except Exception as e:
            print(f"Error creating annotated image: {e}")
            return image_path
    
    def process_batch(self, image_folder):
        """
        Process multiple images in a folder
        
        Args:
            image_folder (str): Path to folder containing images
            
        Returns:
            list: Results for all processed images
        """
        results = []
        
        if not os.path.exists(image_folder):
            return results
        
        for filename in os.listdir(image_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image_path = os.path.join(image_folder, filename)
                result = self.detect_potholes(image_path)
                result['filename'] = filename
                results.append(result)
        
        return results