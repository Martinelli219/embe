import cv2
import time
import serial
from flask import Flask, Response, request, render_template_string

app = Flask(__name__)
ser = serial.Serial('/dev/serial0', 9600) 

class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 640)  # Ancho del video
        self.cap.set(4, 480)  # Alto del video

    def __del__(self):
        self.cap.release()

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        _, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data_to_send = request.form.get('serial_data')
        if data_to_send:
            ser.write(data_to_send.encode())
            return "Data sent to Raspberry Pi via UART: " + data_to_send
        else:
            return "No data provided."
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Camera Stream</title>
            <style>
                /* ... (your CSS styles) ... */
                    body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    text-align: center;
                }

                h1 {
                    margin: 20px 0;
                }

                #video {
                    width: 640px;
                    height: 480px;
                    border: 1px solid #ccc;
                    margin: 20px auto;
                    display: block;
                }

                form {
                    margin-top: 20px;
                }
                
                input[type="submit"] {
                    padding: 10px 20px;
                    font-size: 16px;
                    background-color: #007bff;
                    color: #fff;
                    border: none;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }

                input[type="submit"]:hover {
                    background-color: #0056b3;
                }

                /* Popup styles */
                .popup {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.7);
                    align-items: center;
                    justify-content: center;
                }

                .popup-content {
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 5px;
                }

                .popup-close {
                    margin-top: 10px;
                    background-color: #007bff;
                    color: #fff;
                    border: none;
                    padding: 5px 10px;
                    cursor: pointer;
                }

                .popup-close:hover {
                    background-color: #0056b3;
                }
            </style>
            <script>
                // Function to update the video stream
                function updateVideoStream() {
                    var video = document.getElementById('video');
                    video.src = "{{ url_for('video_feed') }}" + "?t=" + new Date().getTime();
                    setTimeout(updateVideoStream, 1000); // Update every 1 second
                }

                // Function to show popup
                function showPopup(message) {
                    var popup = document.getElementById('popup');
                    var popupContent = document.getElementById('popup-content');
                    popupContent.innerText = message;
                    popup.style.display = 'flex';
                }

                // Function to hide popup
                function hidePopup() {
                    var popup = document.getElementById('popup');
                    popup.style.display = 'none';
                }

                // Start updating the video stream and show popup when the page loads
                window.onload = function() {
                    updateVideoStream();
                    var form = document.getElementById('data-form');
                    form.addEventListener('submit', function(event) {
                        event.preventDefault();
                        var dataInput = document.getElementById('serial-data');
                        var data = dataInput.value.trim();
                        if (data !== '') {
                            var xhr = new XMLHttpRequest();
                            xhr.open('POST', '/', true);
                            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                            xhr.onload = function() {
                                if (xhr.status === 200) {
                                    showPopup('Data sent to Raspberry Pi via UART: ' + data);
                                } else {
                                    showPopup('Error sending data.');
                                }
                            };
                            xhr.send('serial_data=' + encodeURIComponent(data));
                        } else {
                            showPopup('Please enter data to send.');
                        }
                    });
                };
            </script>
        </head>
        <body>
            <h1>Camera Stream</h1>
            <img id="video" />
            <form id="data-form">
                <input type="text" id="serial-data" placeholder="Enter data to send" />
                <input type="submit" value="Send Data to Raspberry Pi" />
            </form>
            
            <!-- Popup -->
            <div id="popup" class="popup">
                <div class="popup-content" id="popup-content"></div>
                <button class="popup-close" onclick="hidePopup()">Close</button>
            </div>
        </body>
        </html>
    ''')

def generate_video():
    while True:
        frame = camera.get_frame()
        if frame is None:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    camera = Camera()  # Create the Camera instance here
    app.run(host='0.0.0.0', port=8000)
