# eduhub_bonus_features.py

# This file demonstrates bonus challenges for the EduHub MongoDB project:
# - Text Search functionality
# - A simple Recommendation System
# - Data Archiving Strategy
# - Geospatial Queries

from pymongo import MongoClient, ASCENDING
from datetime import datetime, timedelta, UTC
import random
import uuid # For generating new IDs for test data
import json # For handling GeoJSON

# --- MongoDB Connection ---
client = MongoClient('mongodb://localhost:27017/')
db = client['eduhub_db']
print("Connected to MongoDB: eduhub_db for Bonus Features.")

# --- Helper Function for Printing Documents ---
# Reusing the helper from eduhub_queries.py for consistent output
def print_documents(title, documents, limit=5):
    """
    Prints MongoDB documents in a clean, readable format.
    Truncates long strings and formats datetimes.
    """
    print(f"\n--- {title} ---")
    if not documents:
        print("No documents found.")
        return
    count = 0
    for doc in documents:
        if doc is None:
            print("  [Document not found or deleted]")
            continue
        
        doc_copy = doc.copy()
        for key, value in doc_copy.items():
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    doc_copy[key] = value.replace(tzinfo=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
                else:
                    doc_copy[key] = value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
            if isinstance(value, str) and len(value) > 20 and '_id' not in key.lower():
                doc_copy[key] = value[:17] + "..."
            elif isinstance(value, str) and len(value) > 10 and 'id' in key.lower() and key != '_id':
                doc_copy[key] = value[:7] + "..."
            elif isinstance(value, dict) and 'type' in value and 'coordinates' in value: # Handle GeoJSON for printing
                doc_copy[key] = f"GeoJSON({value['type']}: {value['coordinates']})"

        print(doc_copy)
        count += 1
        if count >= limit:
            print(f"... (showing first {limit} documents, if more exist)")
            break
    print("-" * (len(title) + 8))


# --- Bonus Challenge 1: Implement Text Search Functionality ---

def setup_text_search_index():
    """
    Creates a text index on 'title' and 'description' fields in the 'courses' collection.
    This enables full-text search capabilities.
    """
    print("\n--- Setting up Text Search Index on Courses ---")
    try:
        # Create a text index on multiple fields. Weights can be assigned if needed.
        # Default weight for all fields is 1 if not specified.
        db.courses.create_index([
            ('title', 'text'),
            ('description', 'text')
        ], name='course_text_index', default_language='english')
        print("Text index 'course_text_index' created successfully on 'courses' collection.")
    except Exception as e:
        print(f"Error creating text index on 'courses': {e}")

def search_course_content(search_term):
    """
    Performs a full-text search on course titles and descriptions.
    """
    print(f"\n--- Performing Text Search for: '{search_term}' ---")
    # $text operator is used for full-text search.
    # $meta: "textScore" is used to get a relevance score for sorting.
    pipeline = [
        {"$match": {"$text": {"$search": search_term}}},
        {"$project": {
            "title": 1,
            "description": 1,
            "category": 1,
            "score": {"$meta": "textScore"} # Include the text search relevance score
        }},
        {"$sort": {"score": -1}} # Sort by relevance score (highest first)
    ]
    return list(db.courses.aggregate(pipeline))

# --- Bonus Challenge 2: Create a Recommendation System (Aggregation) ---

def get_course_recommendations_collaborative(target_course_title, limit=3):
    """
    Recommends courses based on a simple collaborative filtering approach:
    "Students who enrolled in X course also enrolled in Y courses."
    """
    print(f"\n--- Recommending Courses for '{target_course_title}' (Collaborative Filtering) ---")

    # 1. Find the target course's ID
    target_course = db.courses.find_one({"title": {"$regex": target_course_title, "$options": "i"}})
    if not target_course:
        print(f"Error: Target course '{target_course_title}' not found.")
        return []

    target_course_id = target_course["_id"]

    pipeline = [
        # Stage 1: Find all enrollments for the target course
        {"$match": {"course_id": target_course_id}},
        # Stage 2: Get the student_ids from these enrollments
        {"$group": {"_id": None, "student_ids": {"$addToSet": "$student_id"}}},
        # Stage 3: Unwind the student_ids array to process each student
        {"$unwind": "$student_ids"},
        # Stage 4: Find all other enrollments made by these students
        {"$lookup": {
            "from": "enrollments",
            "localField": "student_ids",
            "foreignField": "student_id",
            "as": "other_enrollments"
        }},
        {"$unwind": "$other_enrollments"},
        # Stage 5: Filter out the target course itself
        {"$match": {"other_enrollments.course_id": {"$ne": target_course_id}}},
        # Stage 6: Group by the recommended course_id and count how many times it appeared
        {"$group": {
            "_id": "$other_enrollments.course_id",
            "recommendation_count": {"$sum": 1}
        }},
        # Stage 7: Join with the courses collection to get course details
        {"$lookup": {
            "from": "courses",
            "localField": "_id",
            "foreignField": "_id",
            "as": "course_details"
        }},
        {"$unwind": "$course_details"},
        # Stage 8: Project desired fields and sort by recommendation count
        {"$project": {
            "_id": 0,
            "recommended_course_id": "$_id",
            "recommended_course_title": "$course_details.title",
            "recommended_course_category": "$course_details.category",
            "recommendation_strength": "$recommendation_count"
        }},
        {"$sort": {"recommendation_strength": -1}},
        {"$limit": limit}
    ]
    return list(db.enrollments.aggregate(pipeline))

# --- Bonus Challenge 3: Design a Data Archiving Strategy ---

def archive_old_enrollments(cutoff_date):
    """
    Archives enrollments older than a specified cutoff date.
    Moves them from 'enrollments' to 'archived_enrollments' and then deletes from 'enrollments'.
    """
    print(f"\n--- Archiving Enrollments older than {cutoff_date.strftime('%Y-%m-%d')} ---")
    
    # 1. Find old enrollments
    old_enrollments_cursor = db.enrollments.find({
        "enrollment_date": {"$lt": cutoff_date}
    })
    
    old_enrollments_list = list(old_enrollments_cursor)
    
    if not old_enrollments_list:
        print("No old enrollments found to archive.")
        return 0, 0

    print(f"Found {len(old_enrollments_list)} enrollments to archive.")

    # 2. Insert into archived_enrollments collection
    try:
        archive_result = db.archived_enrollments.insert_many(old_enrollments_list)
        inserted_count = len(archive_result.inserted_ids)
        print(f"Successfully archived {inserted_count} enrollments.")
    except Exception as e:
        print(f"Error archiving enrollments: {e}")
        return 0, 0 # Return 0, 0 if archiving fails

    # 3. Delete from original enrollments collection
    try:
        deleted_count = 0
        for doc in old_enrollments_list:
            delete_result = db.enrollments.delete_one({"_id": doc["_id"]})
            deleted_count += delete_result.deleted_count
        print(f"Successfully deleted {deleted_count} archived enrollments from 'enrollments' collection.")
        return inserted_count, deleted_count
    except Exception as e:
        print(f"Error deleting archived enrollments from original collection: {e}")
        return inserted_count, 0 # Return inserted count, but 0 for deleted if deletion fails

# --- Bonus Challenge 4: Implement Geospatial Queries ---

# Helper to add location data to existing courses for demonstration
def add_sample_locations_to_courses():
    """
    Adds a 'location' field (GeoJSON Point) to existing course documents.
    This is for demonstration of geospatial queries.
    """
    print("\n--- Adding Sample Geospatial Locations to Courses ---")
    courses = list(db.courses.find({}))
    locations = [
        {"type": "Point", "coordinates": [-74.0060, 40.7128]}, # New York City
        {"type": "Point", "coordinates": [2.3522, 48.8566]},   # Paris
        {"type": "Point", "coordinates": [139.6917, 35.6895]}, # Tokyo
        {"type": "Point", "coordinates": [-0.1278, 51.5074]},  # London
        {"type": "Point", "coordinates": [-118.2437, 34.0522]} # Los Angeles
    ]
    
    updates_count = 0
    for i, course in enumerate(courses):
        # Assign a random location to each course
        location_data = random.choice(locations)
        result = db.courses.update_one(
            {"_id": course["_id"]},
            {"$set": {"location": location_data}}
        )
        if result.modified_count > 0:
            updates_count += 1
    print(f"Added geospatial locations to {updates_count} courses.")

    # Create 2dsphere index on the new 'location' field
    try:
        db.courses.create_index([("location", "2dsphere")])
        print("2dsphere index created successfully on 'courses.location'.")
    except Exception as e:
        print(f"Error creating 2dsphere index on 'courses.location': {e}")


def find_courses_near_location(longitude, latitude, max_distance_km=100):
    """
    Finds courses located within a specified maximum distance (in kilometers)
    from a given point.
    """
    print(f"\n--- Finding Courses near ({latitude}, {longitude}) within {max_distance_km} km ---")
    
    # MongoDB expects distance in meters for $maxDistance with 2dsphere index
    max_distance_meters = max_distance_km * 1000 

    # GeoJSON Point for the center of the search
    search_point = {
        "type": "Point",
        "coordinates": [longitude, latitude]
    }

    pipeline = [
        {
            "$geoNear": {
                "near": search_point,
                "distanceField": "distance_km", # Output field for distance
                "maxDistance": max_distance_meters, # Max distance in meters
                "spherical": True, # Required for distance calculations on a sphere
                "key": "location", # The field with the 2dsphere index
                "query": {"is_published": True} # Optional: additional query criteria
            }
        },
        # Convert distance to km for readability
        {"$addFields": {"distance_km": {"$divide": ["$distance_km", 1000]}}},
        {"$sort": {"distance_km": ASCENDING}}, # Sort by distance
        {"$project": { # Project relevant fields
            "title": 1,
            "category": 1,
            "level": 1,
            "price": 1,
            "distance_km": {"$round": ["$distance_km", 2]},
            "location": 1 # Include location for verification
        }}
    ]
    
    return list(db.courses.aggregate(pipeline))


# --- Main Execution Block for Bonus Features ---
if __name__ == "__main__":
    print("\n--- Starting EduHub Bonus Features Script ---")

    # IMPORTANT: Ensure eduhub_queries.py has been run at least once
    # to set up collections and populate with sample data.

    # --- Bonus Challenge 1: Text Search ---
    setup_text_search_index()
    text_search_results = search_course_content("introduction python")
    print_documents("Text Search Results for 'introduction python'", text_search_results)
    
    text_search_results_ai = search_course_content("AI concepts")
    print_documents("Text Search Results for 'AI concepts'", text_search_results_ai)


    # --- Bonus Challenge 2: Recommendation System ---
    # To make recommendations work, ensure there's enough overlapping enrollments
    # in your sample data.
    recommendations = get_course_recommendations_collaborative("Introduction to Python Programming")
    print_documents("Recommended Courses (Collaborative Filter)", recommendations)
    
    recommendations_web = get_course_recommendations_collaborative("Full-Stack Web Development Bootcamp")
    print_documents("Recommended Courses for Web Dev (Collaborative Filter)", recommendations_web)

    # --- Bonus Challenge 3: Data Archiving Strategy ---
    # To test archiving, let's create some old enrollments
    # Ensure there's a student and course to make an old enrollment
    first_student = db.users.find_one({"role": "student"})
    first_course = db.courses.find_one({})

    if first_student and first_course:
        old_enrollment_id = str(uuid.uuid4())
        old_enrollment_doc = {
            "_id": old_enrollment_id,
            "student_id": first_student["_id"],
            "course_id": first_course["_id"],
            "enrollment_date": datetime.now(UTC) - timedelta(days=400), # Over a year ago
            "status": "completed"
        }
        try:
            db.enrollments.insert_one(old_enrollment_doc)
            print(f"\nInserted an old enrollment for archiving test: {old_enrollment_id[:8]}")
        except Exception as e:
            print(f"\nCould not insert old enrollment for test: {e}")

        # Now, try archiving
        one_year_ago = datetime.now(UTC) - timedelta(days=365)
        inserted_archived, deleted_original = archive_old_enrollments(one_year_ago)
        print(f"Archiving Summary: Inserted {inserted_archived} into archive, Deleted {deleted_original} from original.")
        
        # Verify
        print_documents("Archived Enrollments (first 5)", list(db.archived_enrollments.find({})))
        print_documents("Original Enrollments (check for deletion)", list(db.enrollments.find({"_id": old_enrollment_id})))
    else:
        print("\nSkipping Archiving Test: Not enough sample data (student/course) for old enrollment.")


    # --- Bonus Challenge 4: Geospatial Queries ---
    add_sample_locations_to_courses()
    
    # Example search location: Somewhere in New York City (approx. latitude/longitude)
    nyc_longitude, nyc_latitude = -74.0060, 40.7128 
    courses_near_nyc = find_courses_near_location(nyc_longitude, nyc_latitude, max_distance_km=200)
    print_documents(f"Courses within 200km of NYC ({nyc_latitude},{nyc_longitude})", courses_near_nyc)

    # Example search location: London
    london_longitude, london_latitude = -0.1278, 51.5074
    courses_near_london = find_courses_near_location(london_longitude, london_latitude, max_distance_km=50)
    print_documents(f"Courses within 50km of London ({london_latitude},{london_longitude})", courses_near_london)


    # --- Final Step: Close Connection ---
    client.close()
    print("\n--- EduHub Bonus Features Script Finished. Connection Closed. ---")