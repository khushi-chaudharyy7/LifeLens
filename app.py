from flask import Flask, request, jsonify
import cv2
import numpy as np
import pytesseract
from werkzeug.utils import secure_filename
import os
import time

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load pre-trained object detection model (COCO)
net = cv2.dnn.readNetFromDarknet('yolov3.cfg', 'yolov3.weights')
classes = []
with open('coco.names', 'r') as f:
    classes = [line.strip() for line in f.readlines()]
layer_names = net.getLayerNames()
output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def process_image(file):
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return cv2.imread(filepath)

def detect_objects(img):
    height, width = img.shape[:2]
    
    # Preprocess image for object detection
    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)
    
    # Process detection results
    class_ids = []
    confidences = []
    boxes = []
    
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)
    
    # Apply non-max suppression
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    
    results = []
    for i in range(len(boxes)):
        if i in indexes:
            results.append({
                "label": classes[class_ids[i]],
                "confidence": confidences[i],
                "position": boxes[i],
                "distance": estimate_distance(boxes[i], width, height)
            })
    
    return results

def estimate_distance(box, img_width, img_height):
    x, y, w, h = box
    # Simple distance estimation based on object size and position
    # This is a placeholder - real implementation would use camera calibration
    distance = (img_width * img_height) / (w * h)  # Inverse relationship
    return round(distance, 2)

@app.route('/detect_objects', methods=['POST'])
def handle_detection():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        img = process_image(file)
        results = detect_objects(img)
        return jsonify({"objects": results})

@app.route('/read_text', methods=['POST'])
def read_text():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        img = process_image(file)
        # Preprocess image for better OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        text = pytesseract.image_to_string(thresh)
        return jsonify({"text": text.strip()})

@app.route('/')
def index():
    return "LifeLens Backend Server"

@app.route('/test')
def test():
    return jsonify({"status": "success", "message": "Backend is working"})

if __name__ == '__main__':
    app.run(debug=True)
