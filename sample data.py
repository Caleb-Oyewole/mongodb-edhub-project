import json
from pymongo import MongoClient
from datetime import datetime, date
from uuid import UUID

# --- Custom JSON Encoder for PyMongo Objects ---
# This class helps serialize MongoDB specific data types (like datetime and UUID)
# into a format that can be easily converted to JSON.
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # Convert datetime objects to ISO 8601 strings (e.g., "2023-10-27T10:00:00Z")
            return obj.isoformat() + "Z" # 'Z' indicates UTC time
        elif isinstance(obj, date):
            # Convert date objects to ISO 8601 strings
            return obj.isoformat()
        elif isinstance(obj, UUID):
            # Convert UUID objects to their string representation
            return str(obj)
        # For other types (like ObjectId from pymongo), you might need specific handling,
        # but for string UUIDs as _id, this is sufficient.
        return json.JSONEncoder.default(self, obj)

# --- MongoDB Connection ---
client = MongoClient('mongodb://localhost:27017/')
db = client['eduhub_db']
print("Connected to MongoDB: eduhub_db")

# --- Collections to Export ---
collections_to_export = [
    "users",
    "courses",
    "enrollments",
    "lessons",
    "assignments",
    "submissions"
]

# --- Dictionary to hold all exported data ---
exported_data = {}

print("Exporting data from collections...")

# --- Fetch data from each collection ---
for collection_name in collections_to_export:
    print(f"Fetching documents from '{collection_name}'...")
    documents = list(db[collection_name].find({})) # Fetch all documents
    exported_data[collection_name] = documents
    print(f"  - Found {len(documents)} documents in '{collection_name}'.")

# --- Write data to JSON file ---
output_filename = "sample_data.json"
try:
    with open(output_filename, 'w', encoding='utf-8') as f:
        # Use the custom encoder to handle datetime and UUID objects
        json.dump(exported_data, f, indent=4, cls=CustomEncoder, ensure_ascii=False)
    print(f"\nSuccessfully exported all sample data to '{output_filename}'")
except Exception as e:
    print(f"Error exporting data to JSON: {e}")

# --- Close MongoDB Connection ---
client.close()
print("MongoDB connection closed.")
