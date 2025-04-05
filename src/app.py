from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import tempfile
import json
import datetime
from werkzeug.utils import secure_filename
from speech_to_text import transcribe_audio, extract_ehr_components, process_audio_for_ehr
from mongo_insertion import retrieve_patient_records, retrieve_patient_by_id, store_ehr_data

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

@app.route('/')
def index():
    """Main page with recording functionality"""
    return render_template('index.html')

@app.route('/patients')
def patients_list():
    """Page showing all patients"""
    return render_template('patients.html')

@app.route('/patient/<patient_id>')
def patient_detail(patient_id):
    """Page showing details for a specific patient"""
    return render_template('patient_detail.html', patient_id=patient_id)

@app.route('/api/patients', methods=['GET'])
def get_patients():
    """API endpoint to get all patients"""
    limit = request.args.get('limit', 10, type=int)
    patients = retrieve_patient_records(limit=limit)
    return jsonify(patients)

@app.route('/api/patient/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    """API endpoint to get a specific patient"""
    patient = retrieve_patient_by_id(patient_id)
    if patient:
        return jsonify(patient)
    return jsonify({"error": "Patient not found"}), 404

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """
    API endpoint to process audio from the frontend.
    Expects a WAV/MP3 file in the request, processes it, and returns the structured EHR data.
    """
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No audio file selected"}), 400
    
    # Save the file temporarily
    filename = secure_filename(audio_file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(file_path)
    
    try:
        # Process the audio file
        ehr_data = process_audio_for_ehr(file_path)
        
        # Delete the temporary file
        os.remove(file_path)
        
        return jsonify(ehr_data)
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": str(e)}), 500

@app.route('/api/record', methods=['POST'])
def record_audio():
    """
    Alternative endpoint that accepts raw audio data (not a file)
    and processes it directly.
    """
    if request.data:
        # Save the raw audio data to a temporary file
        temp_file = os.path.join(app.config['UPLOAD_FOLDER'], f"recording_{datetime.datetime.now().timestamp()}.webm")
        with open(temp_file, 'wb') as f:
            f.write(request.data)
        
        try:
            # Process the audio file
            ehr_data = process_audio_for_ehr(temp_file)
            
            # Delete the temporary file
            os.remove(temp_file)
            
            return jsonify(ehr_data)
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "No audio data received"}), 400

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, port=5000)# Flask application for EHR Audio Processing 
