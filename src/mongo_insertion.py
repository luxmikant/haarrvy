import pymongo
from pymongo import MongoClient
import datetime
import json
from bson import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Atlas connection string (replace with your actual connection string)
# Format: mongodb+srv://<username>:<password>@<cluster-url>/<default-database>
MONGODB_URI = "mongodb+srv://luxmikant:vQ6FO028ZedltCdY@ehr.za6ipze.mongodb.net/?retryWrites=true&w=majority&appName=EHR"

# Initialize MongoDB client
try:
    client = MongoClient(MONGODB_URI)
    db = client["ehr_database"]  # Your database name
    collection = db["patient_records"]  # Collection to store EHR data
    
    # Ping the database to verify connection
    client.admin.command('ping')
    logger.info("Connected successfully to MongoDB Atlas")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

def store_ehr_data(ehr_data):
    """
    Stores the extracted EHR data into MongoDB
    
    Args:
        ehr_data (dict): The JSON data containing EHR components
        
    Returns:
        str: The ID of the inserted document
    """
    try:
        # Add metadata if not present
        if "timestamp" not in ehr_data:
            ehr_data["timestamp"] = datetime.datetime.utcnow()
            
        # Insert the document
        result = collection.insert_one(ehr_data)
        logger.info(f"Inserted document with ID: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error storing EHR data: {e}")
        raise

def retrieve_patient_records(query=None, limit=10):
    """
    Retrieves patient records based on a query
    
    Args:
        query (dict): MongoDB query filter
        limit (int): Maximum number of records to return
        
    Returns:
        list: List of patient records
    """
    if query is None:
        query = {}
        
    try:
        cursor = collection.find(query).limit(limit)
        # Convert ObjectId to string for JSON serialization
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
        return results
    except Exception as e:
        logger.error(f"Error retrieving patient records: {e}")
        raise

def retrieve_patient_by_id(patient_id):
    """
    Retrieves a specific patient record by ID
    
    Args:
        patient_id (str): Patient ID to search for
        
    Returns:
        dict: Patient record or None if not found
    """
    try:
        # Try to find by MongoDB _id first
        if ObjectId.is_valid(patient_id):
            record = collection.find_one({"_id": ObjectId(patient_id)})
            if record:
                record['_id'] = str(record['_id'])
                return record
                
        # If not found or invalid ObjectId, try patient ID from demographics
        record = collection.find_one({"patientDemographics.patientId": patient_id})
        if record:
            record['_id'] = str(record['_id'])
            return record
            
        # If still not found, try by name (less precise)
        record = collection.find_one({"patientDemographics.firstName": patient_id})
        if record:
            record['_id'] = str(record['_id'])
            return record
            
        return None
    except Exception as e:
        logger.error(f"Error retrieving patient by ID: {e}")
        raise
        
def update_patient_record(patient_id, update_data):
    """
    Updates an existing patient record
    
    Args:
        patient_id (str): MongoDB ID or patient ID
        update_data (dict): Data to update
        
    Returns:
        bool: True if update was successful
    """
    try:
        if ObjectId.is_valid(patient_id):
            query = {"_id": ObjectId(patient_id)}
        else:
            query = {"patientDemographics.patientId": patient_id}
            
        result = collection.update_one(query, {"$set": update_data})
        success = result.modified_count > 0
        logger.info(f"Updated patient record: {success}")
        return success
    except Exception as e:
        logger.error(f"Error updating patient record: {e}")
        raise

# Create indexes for efficient queries
def create_indexes():
    try:
        collection.create_index([("patientDemographics.firstName", pymongo.ASCENDING)])
        collection.create_index([("patientDemographics.lastName", pymongo.ASCENDING)])
        collection.create_index([("patientDemographics.patientId", pymongo.ASCENDING)], unique=True)
        collection.create_index([("timestamp", pymongo.DESCENDING)])
        logger.info("Created indexes successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

if __name__ == "__main__":
    # Create indexes when module is run directly
    create_indexes()
    
    # Example usage - for testing only
    test_data = {
        "patientDemographics": {
            "firstName": "John",
            "lastName": "Doe",
            "patientId": "P12345",
            "gender": "Male",
            "age": 45
        },
        "clinicalNotes": "Patient reported headache and dizziness."
    }
    
    doc_id = store_ehr_data(test_data)
    print(f"Test document inserted with ID: {doc_id}")
    
    # Retrieve and display
    result = retrieve_patient_by_id("P12345")
    print(json.dumps(result, indent=2))
