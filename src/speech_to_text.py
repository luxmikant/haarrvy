import google.generativeai as genai
import pathlib
import json
import os
from mongo_insertion import store_ehr_data, retrieve_patient_by_id

# Configure the API key
genai.configure(api_key="AIzaSyAD6nnFW9hHef5Jad9DaiT1tl3c4EBVvT0")

def transcribe_audio(file_path: str) -> str:
    """
    Uploads an audio file to Google Gemini API and returns a transcription.
    Uses a prompt to transcribe the audio content.
    """
    # Create a model instance
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Generate content by passing the file directly
    with open(file_path, 'rb') as f:
        audio_data = f.read()
        
    response = model.generate_content([
        "Transcribe this audio clip in detail:",
        {"mime_type": "audio/mp3", "data": audio_data}
    ])
    
    return response.text

def extract_ehr_components(transcript: str) -> dict:
    """
    Takes a transcript and extracts structured EHR components using Gemini.
    Returns a structured JSON with medical information.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Prompt engineering to extract EHR components
    prompt = f"""
    Extract the following EHR components from this medical conversation transcript and return them in JSON format.
    Include any available information for each component:
    
    1. patientDemographics (name, age, gender, contact info)
    2. medicalHistory (past diagnoses, surgeries, family history)
    3. medicationsAndAllergies (current medications, allergies)
    4. laboratoryAndTestResults (recent tests, results)
    5. clinicalNotes (chief complaint, symptoms, observations)
    6. vitalSigns (blood pressure, heart rate, temperature, etc)
    7. immunizationRecords (vaccines)
    8. ordersAndPrescriptions (tests ordered, medications prescribed)
    9. billingAndAdministrativeData (insurance info, billing codes)
    
    Format the response as valid JSON only, with no additional text.
    
    Transcript:
    {transcript}
    """
    
    response = model.generate_content(prompt)
    
    try:
        # Parse the JSON response
        ehr_data = json.loads(response.text)
        return ehr_data
    except json.JSONDecodeError:
        # If parsing fails, try to extract JSON portion
        try:
            # Look for JSON-like content (between { and })
            json_text = response.text
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0].strip()
            elif '```' in json_text:
                json_text = json_text.split('```')[1].split('```')[0].strip()
            
            # Ensure we start with { and end with }
            start_idx = json_text.find('{')
            end_idx = json_text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_text = json_text[start_idx:end_idx]
                return json.loads(json_text)
            
        except Exception as e:
            print(f"Error extracting JSON: {e}")
        
        # Return a simple error structure as fallback
        return {"error": "Failed to parse structured data", "rawText": response.text}

def process_audio_for_ehr(file_path: str) -> dict:
    """
    Combined function that transcribes audio and extracts EHR components in one step.
    Also saves the extracted data to MongoDB.
    """
    # Get transcript
    transcript = transcribe_audio(file_path)
    print(f"Transcript obtained: {transcript[:100]}...")  # Print first 100 chars for debugging
    
    # Extract structured EHR data
    ehr_data = extract_ehr_components(transcript)
    
    # Store in MongoDB and get document ID
    document_id = store_ehr_data(ehr_data)
    
    # Add the MongoDB ID to the response
    ehr_data["_id"] = document_id
    
    return ehr_data

if __name__ == "__main__":
    # Example usage: replace with your actual audio file path
    # Make sure this path actually exists
    file_path = os.path.join(os.path.dirname(__file__), "media", "sample.mp3")
    
    if not os.path.exists(file_path):
        print(f"Error: Audio file not found at {file_path}")
        # Try alternative paths
        alt_path = "automated-testing/src/media/sample.mp3"
        if os.path.exists(alt_path):
            file_path = alt_path
            print(f"Using alternative path: {file_path}")
        else:
            print("Please specify a valid audio file path")
            exit(1)
    
    # Process the audio and store in MongoDB in one operation
    try:
        ehr_data = process_audio_for_ehr(file_path)
        
        print("\nStructured EHR Data (saved to MongoDB):")
        print(json.dumps(ehr_data, indent=2))
        
        # Demonstrate retrieval
        patient_id = ehr_data.get("patientDemographics", {}).get("patientId", ehr_data["_id"])
        retrieved_data = retrieve_patient_by_id(patient_id)
        
        print("\nRetrieved from MongoDB:")
        print(json.dumps(retrieved_data, indent=2))
    except Exception as e:
        print(f"Error processing audio: {e}")