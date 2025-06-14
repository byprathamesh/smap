import cv2
from deepface import DeepFace

class AIAnalyzer:
    def __init__(self, config):
        print("[INFO] AI Analyzer initialized using DeepFace library.")
        self.config = config
        self.face_detector = "opencv"  # Use 'mtcnn' or 'retinaface' for higher accuracy but slower speed

    def analyze_frame(self, frame):
        # DeepFace's analyze function handles everything: detection, gender, and age
        # It returns a list of dictionaries, one for each face found.
        try:
            face_results = DeepFace.analyze(
                img_path=frame,
                actions=['age', 'gender'],
                enforce_detection=False,  # Don't crash if no face is found
                detector_backend=self.face_detector
            )
        except Exception as e:
            # This can happen if an image is corrupted or has an issue.
            # print(f"[DEBUG] DeepFace analysis failed with an error: {e}")
            return [], []  # Return empty lists to avoid crashing the main loop

        detected_faces = []
        person_predictions = []

        for face_obj in face_results:
            # 'region' contains the bounding box: {'x':, 'y':, 'w':, 'h':}
            region = face_obj['region']
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            
            # The main output contains 'dominant_gender' and 'age'
            gender = face_obj['dominant_gender']
            age = face_obj['age']
            
            # Format for our existing system
            detected_faces.append((x, y, x + w, y + h))
            person_predictions.append({
                "gender": gender,
                "age": age
            })

        # The YOLO person detection part is no longer needed from this file,
        # as DeepFace handles face detection.
        # We can integrate a separate person detector in the main loop if needed.
        return detected_faces, person_predictions 