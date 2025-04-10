// LifeLens Complete Implementation
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const video = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const output = document.getElementById('output');
    const synth = window.speechSynthesis;

    // Camera State
    let isCameraOn = false;

    // Initialize Camera
    async function startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment', width: 1280, height: 720 },
                audio: false
            });
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                isCameraOn = true;
                showStatus("Camera ready");
            };
        } catch (err) {
            showStatus(`Camera error: ${err.message}`, 'error');
        }
    }

    // Object Detection
    async function detectObjects() {
        if (!isCameraOn) {
            showStatus("Please start camera first", 'error');
            return;
        }

        showStatus("Detecting objects...");
        
        try {
            const formData = new FormData();
            canvas.toBlob(async (blob) => {
                formData.append('image', blob, 'frame.jpg');
                
                const response = await fetch('/detect_objects', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                if (data.error) throw new Error(data.error);
                
                drawDetections(data.objects);
                showStatus(`Found ${data.objects.length} objects`);
            }, 'image/jpeg');
            
        } catch (err) {
            showStatus(`Detection failed: ${err.message}`, 'error');
        }
    }

    // Text Recognition
    async function recognizeText() {
        if (!isCameraOn) {
            showStatus("Please start camera first", 'error');
            return;
        }

        showStatus("Reading text...");
        
        try {
            const formData = new FormData();
            canvas.toBlob(async (blob) => {
                formData.append('image', blob, 'frame.jpg');
                
                const response = await fetch('/read_text', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                if (data.error) throw new Error(data.error);
                
                showStatus(data.text || "No text found");
            }, 'image/jpeg');
            
        } catch (err) {
            showStatus(`Text recognition failed: ${err.message}`, 'error');
        }
    }

    // Helper Functions
    function drawDetections(objects) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        objects.forEach(obj => {
            const [x, y, w, h] = obj.position;
            
            // Draw bounding box
            ctx.strokeStyle = '#00FF00';
            ctx.lineWidth = 3;
            ctx.strokeRect(x, y, w, h);
            
            // Draw label
            ctx.fillStyle = '#00FF00';
            ctx.font = '16px Arial';
            ctx.fillText(`${obj.label} (${Math.round(obj.confidence*100)}%)`, x, y-5);
        });
    }

    function showStatus(message, type = 'info') {
        output.textContent = message;
        output.className = type;
        speak(message);
    }

    function speak(text) {
        if (synth.speaking) synth.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        synth.speak(utterance);
    }

    // Event Listeners
    document.getElementById('startBtn').addEventListener('click', startCamera);
    document.getElementById('detectBtn').addEventListener('click', detectObjects);
    document.getElementById('readBtn').addEventListener('click', recognizeText);
    document.getElementById('stopBtn').addEventListener('click', () => {
        if (video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
            isCameraOn = false;
            showStatus("Camera stopped");
        }
    });
});
