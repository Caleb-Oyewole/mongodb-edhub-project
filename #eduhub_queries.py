# eduhub_queries.py

# This file contains all MongoDB operations for the EduHub database,
# organized by task.

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, WriteError
from datetime import datetime, timedelta, UTC
import uuid
import random
import time
import re

# --- MongoDB Connection ---
client = MongoClient('mongodb://localhost:27017/')
db = client['eduhub_db']
print("Connected to MongoDB: eduhub_db")

# --- Helper Function for Printing Documents ---
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
                # Ensure datetime objects are converted to UTC for consistency before formatting
                if value.tzinfo is None:
                    doc_copy[key] = value.replace(tzinfo=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
                else:
                    doc_copy[key] = value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
            if isinstance(value, str) and len(value) > 20 and '_id' not in key.lower():
                doc_copy[key] = value[:17] + "..."
            elif isinstance(value, str) and len(value) > 10 and 'id' in key.lower() and key != '_id':
                doc_copy[key] = value[:7] + "..."
        print(doc_copy)
        count += 1
        if count >= limit:
            print(f"... (showing first {limit} documents, if more exist)")
            break
    print("-" * (len(title) + 8))

# --- Part 1: Database Setup and Schema Validation ---
# (As implemented in mongo_db_setup)
def setup_collections_with_validation():
    """
    Creates MongoDB collections with predefined JSON schema validation rules.
    This ensures data integrity for required fields, data types, and enum values.
    """
    print("\n--- Setting up Collections with Validation ---")
    collections_to_create = {
        'users': {
            'bsonType': 'object',
            'required': ['_id', 'username', 'email', 'password_hash', 'role', 'created_at', 'updated_at'],
            'properties': {
                '_id': {'bsonType': 'string', 'description': 'must be a string and is required (e.g., UUID)'},
                'username': {'bsonType': 'string', 'description': 'must be a string and is required', 'minLength': 3},
                'email': {'bsonType': 'string', 'description': 'must be a string and a valid email format, and is required', 'pattern': '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'},
                'password_hash': {'bsonType': 'string', 'description': 'must be a string and is required'},
                'role': {'bsonType': 'string', 'description': 'must be "student" or "instructor" and is required', 'enum': ['student', 'instructor']},
                'created_at': {'bsonType': 'date', 'description': 'must be a date and is required'},
                'updated_at': {'bsonType': 'date', 'description': 'must be a date and is required'},
                'first_name': {'bsonType': 'string'},
                'last_name': {'bsonType': 'string'},
                'profile': { # Nested document
                    'bsonType': 'object',
                    'properties': {
                        'bio': {'bsonType': 'string'},
                        'avatar': {'bsonType': 'string'},
                        'skills': {'bsonType': 'array', 'items': {'bsonType': 'string'}}
                    }
                },
                'is_active': {'bsonType': 'bool'}
            }
        },
        'courses': {
            'bsonType': 'object',
            'required': ['_id', 'title', 'description', 'instructor_id', 'created_at', 'updated_at'],
            'properties': {
                '_id': {'bsonType': 'string', 'description': 'must be a string and is required (e.g., UUID)'},
                'title': {'bsonType': 'string', 'description': 'must be a string and is required', 'minLength': 5},
                'description': {'bsonType': 'string', 'description': 'must be a string and is required', 'minLength': 10},
                'instructor_id': {'bsonType': 'string', 'description': 'must be a string referencing users._id and is required'},
                'category': {'bsonType': 'string'},
                'level': {'bsonType': 'string', 'enum': ['beginner', 'intermediate', 'advanced']},
                'duration': {'bsonType': 'double'},
                'price': {'bsonType': 'double'},
                'tags': {'bsonType': 'array', 'items': {'bsonType': 'string'}},
                'created_at': {'bsonType': 'date', 'description': 'must be a date and is required'},
                'updated_at': {'bsonType': 'date', 'description': 'must be a date and is required'},
                'is_published': {'bsonType': 'bool'}
            }
        },
        'enrollments': {
            'bsonType': 'object',
            'required': ['_id', 'student_id', 'course_id', 'enrollment_date', 'status'],
            'properties': {
                '_id': {'bsonType': 'string', 'description': 'must be a string and is required (e.g., UUID)'},
                'student_id': {'bsonType': 'string', 'description': 'must be a string referencing users._id and is required'},
                'course_id': {'bsonType': 'string', 'description': 'must be a string referencing courses._id and is required'},
                'enrollment_date': {'bsonType': 'date', 'description': 'must be a date and is required'},
                'status': {'bsonType': 'string', 'description': 'must be "active", "completed", or "dropped" and is required', 'enum': ['active', 'completed', 'dropped']}
            }
        },
        'lessons': {
            'bsonType': 'object',
            'required': ['_id', 'course_id', 'title', 'content', 'order'],
            'properties': {
                '_id': {'bsonType': 'string', 'description': 'must be a string and is required (e.g., UUID)'},
                'course_id': {'bsonType': 'string', 'description': 'must be a string referencing courses._id and is required'},
                'title': {'bsonType': 'string', 'description': 'must be a string and is required', 'minLength': 5},
                'content': {'bsonType': 'string', 'description': 'must be a string containing lesson material and is required', 'minLength': 20},
                'order': {'bsonType': 'int', 'description': 'must be an integer representing lesson order and is required', 'minimum': 1},
                'created_at': {'bsonType': 'date'},
                'updated_at': {'bsonType': 'date'}
            }
        },
        'assignments': {
            'bsonType': 'object',
            'required': ['_id', 'lesson_id', 'title', 'description', 'due_date'],
            'properties': {
                '_id': {'bsonType': 'string', 'description': 'must be a string and is required (e.g., UUID)'},
                'lesson_id': {'bsonType': 'string', 'description': 'must be a string referencing lessons._id and is required'},
                'title': {'bsonType': 'string', 'description': 'must be a string and is required', 'minLength': 5},
                'description': {'bsonType': 'string', 'description': 'must be a string and is required', 'minLength': 10},
                'due_date': {'bsonType': 'date', 'description': 'must be a date and is required'},
                'max_score': {'bsonType': 'double'},
                'created_at': {'bsonType': 'date'},
                'updated_at': {'bsonType': 'date'}
            }
        },
        'submissions': {
            'bsonType': 'object',
            'required': ['_id', 'assignment_id', 'student_id', 'submission_date', 'content'],
            'properties': {
                '_id': {'bsonType': 'string', 'description': 'must be a string and is required (e.g., UUID)'},
                'assignment_id': {'bsonType': 'string', 'description': 'must be a string referencing assignments._id and is required'},
                'student_id': {'bsonType': 'string', 'description': 'must be a string referencing users._id and is required'},
                'submission_date': {'bsonType': 'date', 'description': 'must be a date and is required'},
                'content': {'bsonType': 'string', 'description': 'must be a string representing submission content (e.g., text, file path) and is required', 'minLength': 1},
                'grade': {'bsonType': ['double', 'null'], 'description': 'must be a number between 0 and 100 if present', 'minimum': 0, 'maximum': 100},
                'feedback': {'bsonType': ['string', 'null'], 'description': 'must be a string containing feedback if present'},
                'created_at': {'bsonType': 'date'},
                'updated_at': {'bsonType': 'date'}
            }
        }
    }

    for col_name, validator_rules in collections_to_create.items():
        try:
            # Drop collection if it exists to apply new validation rules
            db.drop_collection(col_name)
            db.create_collection(col_name, validator={'$jsonSchema': validator_rules})
            print(f"Collection '{col_name}' created/recreated with validation.")
        except Exception as e:
            print(f"Error creating/updating '{col_name}' collection: {e}")

# --- Part 2: Insert Sample Data ---
# (As implemented in mongo_db_sample_data)
def insert_sample_data():
    """
    Inserts a comprehensive set of sample documents into all collections.
    Ensures referential relationships between documents.
    """
    print("\n--- Inserting Sample Data ---")

    # Clear existing data to ensure a fresh start
    try:
        db.users.delete_many({})
        db.courses.delete_many({})
        db.enrollments.delete_many({})
        db.lessons.delete_many({})
        db.assignments.delete_many({})
        db.submissions.delete_many({})
        print("Cleared existing data from collections before inserting samples.")
    except Exception as e:
        print(f"Error clearing collections: {e}")

    sample_users = []
    instructor_ids = []
    student_ids = []

    for i in range(20): # 20 users
        user_id = str(uuid.uuid4())
        role = "student" if i % 2 == 0 else "instructor"
        
        if role == "instructor":
            instructor_ids.append(user_id)
            first_name = random.choice(["Alice", "Bob", "Charlie", "Diana", "Eve"])
            last_name = random.choice(["Smith", "Jones", "Williams", "Brown", "Davis"])
            bio = f"Experienced instructor in {random.choice(['AI', 'Web Dev', 'Data Science', 'Networking'])}."
            skills = random.sample(["Python", "Java", "C++", "JavaScript", "MongoDB", "SQL", "Machine Learning", "Cloud Computing"], k=random.randint(2,4))
        else:
            student_ids.append(user_id)
            first_name = random.choice(["Frank", "Grace", "Heidi", "Ivan", "Judy", "Karl", "Linda", "Mike", "Nancy", "Oscar"])
            last_name = random.choice(["Wilson", "Miller", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson"])
            bio = f"Eager to learn about {random.choice(['programming', 'design', 'history', 'science'])}."
            skills = random.sample(["Beginner", "Intermediate", "Fast Learner", "Problem Solver"], k=random.randint(1,2))

        sample_users.append({
            "_id": user_id,
            "username": f"{first_name.lower()}_{last_name.lower()}{i}",
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
            "password_hash": f"hashed_password_{uuid.uuid4().hex[:8]}",
            "role": role,
            "created_at": datetime.now(UTC) - timedelta(days=random.randint(30, 365)),
            "updated_at": datetime.now(UTC) - timedelta(days=random.randint(1, 30)),
            "first_name": first_name,
            "last_name": last_name,
            "profile": {
                "bio": bio,
                "avatar": f"https://placehold.co/100x100/{random.choice(['ADD8E6', 'FFDDC1', 'D4A6C5'])}/000000?text={first_name[0]}{last_name[0]}",
                "skills": skills
            },
            "is_active": random.choice([True, False])
        })

    try:
        db.users.insert_many(sample_users)
        print(f"Inserted {len(sample_users)} sample user documents.")
    except Exception as e:
        print(f"Error inserting sample user documents: {e}")

    sample_courses = []
    course_ids = []
    categories = ["Programming", "Web Development", "Data Science", "Design", "Business", "Marketing", "Science", "Arts"]
    levels = ["beginner", "intermediate", "advanced"]

    for i in range(8): # 8 courses
        course_id = str(uuid.uuid4())
        course_ids.append(course_id)
        
        sample_courses.append({
            "_id": course_id,
            "title": f"{random.choice(['Mastering', 'Introduction to', 'Advanced', 'Fundamentals of'])} {random.choice(categories)} Course {i+1}",
            "description": f"A comprehensive course covering {random.choice(categories).lower()} concepts and practices. This course is for {levels[i % 3]} learners.",
            "instructor_id": random.choice(instructor_ids),
            "category": random.choice(categories),
            "level": levels[i % 3],
            "duration": random.randint(20, 100),
            "price": round(random.uniform(29.99, 299.99), 2),
            "tags": random.sample(["Online", "Certification", "Project-based", "Interactive", "Self-paced", "Beginner Friendly"], k=random.randint(2,4)),
            "created_at": datetime.now(UTC) - timedelta(days=random.randint(60, 180)),
            "updated_at": datetime.now(UTC) - timedelta(days=random.randint(7, 60)),
            "is_published": random.choice([True, True, True, False])
        })

    try:
        db.courses.insert_many(sample_courses)
        print(f"Inserted {len(sample_courses)} sample course documents.")
    except Exception as e:
        print(f"Error inserting sample course documents: {e}")

    sample_enrollments = []
    enrollment_statuses = ["active", "completed", "dropped"]

    for i in range(15): # 15 enrollments
        student_id = random.choice(student_ids)
        course_id = random.choice(course_ids)
        
        sample_enrollments.append({
            "_id": str(uuid.uuid4()),
            "student_id": student_id,
            "course_id": course_id,
            "enrollment_date": datetime.now(UTC) - timedelta(days=random.randint(10, 90)),
            "status": random.choice(enrollment_statuses)
        })

    try:
        db.enrollments.insert_many(sample_enrollments)
        print(f"Inserted {len(sample_enrollments)} sample enrollment documents.")
    except Exception as e:
        print(f"Error inserting sample enrollment documents: {e}")


    sample_lessons = []
    lesson_ids = []
    lesson_counter = 0

    for course_id in course_ids:
        num_lessons_for_course = random.randint(3, 5) # Each course gets 3-5 lessons
        for i in range(num_lessons_for_course):
            if lesson_counter >= 25: # Ensure total lessons don't exceed 25
                break
            lesson_id = str(uuid.uuid4())
            lesson_ids.append(lesson_id)
            lesson_counter += 1
            
            sample_lessons.append({
                "_id": lesson_id,
                "course_id": course_id,
                "title": f"Lesson {i+1}: {random.choice(['Introduction', 'Core Concepts', 'Advanced Topics', 'Practice Session'])}",
                "content": f"Detailed content for lesson {i+1} covering specific topics within the course. This lesson aims to deepen understanding of {random.choice(['algorithms', 'frontend', 'data analysis', 'user experience'])}.",
                "order": i + 1,
                "created_at": datetime.now(UTC) - timedelta(days=random.randint(5, 45)),
                "updated_at": datetime.now(UTC) - timedelta(days=random.randint(1, 5))
            })
        if lesson_counter >= 25:
            break

    try:
        db.lessons.insert_many(sample_lessons)
        print(f"Inserted {len(sample_lessons)} sample lesson documents.")
    except Exception as e:
        print(f"Error inserting sample lesson documents: {e}")

    sample_assignments = []
    assignment_ids = []

    for i in range(10): # 10 assignments
        assignment_id = str(uuid.uuid4())
        assignment_ids.append(assignment_id)
        
        sample_assignments.append({
            "_id": assignment_id,
            "lesson_id": random.choice(lesson_ids),
            "title": f"Assignment {i+1}: {random.choice(['Quiz', 'Project', 'Essay', 'Coding Challenge'])}",
            "description": f"Complete this task to demonstrate your understanding of the lesson. It's about {random.choice(['data structures', 'web design', 'marketing strategies', 'scientific principles'])}.",
            "due_date": datetime.now(UTC) + timedelta(days=random.randint(7, 21)),
            "max_score": 100,
            "created_at": datetime.now(UTC) - timedelta(days=random.randint(3, 10)),
            "updated_at": datetime.now(UTC) - timedelta(days=random.randint(0, 3))
        })

    try:
        db.assignments.insert_many(sample_assignments)
        print(f"Inserted {len(sample_assignments)} sample assignment documents.")
    except Exception as e:
        print(f"Error inserting sample assignment documents: {e}")

    sample_submissions = []

    for i in range(12): # 12 submissions
        submission_id = str(uuid.uuid4())
        
        assignment_id = random.choice(assignment_ids)
        student_id = random.choice(student_ids)

        has_grade = random.choice([True, False])
        grade = round(random.uniform(50, 100), 2) if has_grade else None
        feedback = random.choice([
            "Excellent work!", "Good attempt, review chapter 3.",
            "Well done, minor improvements needed.", "Needs more detail.", None
        ]) if has_grade else None

        sample_submissions.append({
            "_id": submission_id,
            "assignment_id": assignment_id,
            "student_id": student_id,
            "submission_date": datetime.now(UTC) - timedelta(days=random.randint(0, 7)),
            "content": f"Submission content for assignment {assignment_id[:8]} by student {student_id[:8]}.",
            "grade": grade,
            "feedback": feedback,
            "created_at": datetime.now(UTC) - timedelta(days=random.randint(0, 7)),
            "updated_at": datetime.now(UTC) - timedelta(days=random.randint(0, 1))
        })

    try:
        db.submissions.insert_many(sample_submissions)
        print(f"Inserted {len(sample_submissions)} sample submission documents.")
    except Exception as e:
        print(f"Error inserting sample submission documents: {e}")

# --- Part 3: Basic CRUD Operations ---
# (As implemented in mongo_db_create_operations, mongo_db_read_operations,
# mongo_db_update_operations, mongo_db_delete_operations)

# Helper for CRUD
def document_exists(collection_name, doc_id):
    """Checks if a document with the given ID exists in the specified collection."""
    return db[collection_name].find_one({"_id": doc_id}) is not None

# Create Operations
def add_new_student(username, email, password, first_name, last_name, bio, skills):
    new_student_id = str(uuid.uuid4())
    student_document = {
        "_id": new_student_id, "username": username, "email": email, "password_hash": password,
        "role": "student", "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
        "first_name": first_name, "last_name": last_name,
        "profile": {"bio": bio, "avatar": f"https://placehold.co/100x100/{random.choice(['E6E6FA', 'C1E1C1', 'F0F8FF'])}/000000?text={first_name[0]}{last_name[0]}", "skills": skills},
        "is_active": True
    }
    try:
        db.users.insert_one(student_document)
        print(f"Successfully added new student: {username} (ID: {new_student_id})")
        return new_student_id
    except Exception as e:
        print(f"Error adding new student: {e}")
        return None

def create_new_course(title, description, instructor_id, category, level, duration, price, tags):
    if not document_exists("users", instructor_id):
        print(f"Error: Instructor with ID {instructor_id[:8]} not found. Cannot create course.")
        return None
    new_course_id = str(uuid.uuid4())
    course_document = {
        "_id": new_course_id, "title": title, "description": description, "instructor_id": instructor_id,
        "category": category, "level": level, "duration": duration, "price": price, "tags": tags,
        "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC), "is_published": True
    }
    try:
        db.courses.insert_one(course_document)
        print(f"Successfully created new course: '{title}' (ID: {new_course_id})")
        return new_course_id
    except Exception as e:
        print(f"Error creating new course: {e}")
        return None

def enroll_student_in_course(student_id, course_id):
    if not document_exists("users", student_id) or not document_exists("courses", course_id):
        print(f"Error: Student {student_id[:8]} or Course {course_id[:8]} not found. Cannot enroll.")
        return None
    if db.enrollments.find_one({"student_id": student_id, "course_id": course_id}):
        print(f"Student {student_id[:8]} is already enrolled in course {course_id[:8]}.")
        return None
    new_enrollment_id = str(uuid.uuid4())
    enrollment_document = {
        "_id": new_enrollment_id, "student_id": student_id, "course_id": course_id,
        "enrollment_date": datetime.now(UTC), "status": "active"
    }
    try:
        db.enrollments.insert_one(enrollment_document)
        print(f"Successfully enrolled student {student_id[:8]} in course {course_id[:8]} (ID: {new_enrollment_id})")
        return new_enrollment_id
    except Exception as e:
        print(f"Error enrolling student: {e}")
        return None

def add_new_lesson(course_id, title, content):
    if not document_exists("courses", course_id):
        print(f"Error: Course with ID {course_id[:8]} not found. Cannot add lesson.")
        return None
    last_lesson = db.lessons.find({"course_id": course_id}).sort("order", -1).limit(1)
    next_order = (next(last_lesson, None)['order'] + 1) if next(last_lesson, None) else 1
    new_lesson_id = str(uuid.uuid4())
    lesson_document = {
        "_id": new_lesson_id, "course_id": course_id, "title": title, "content": content,
        "order": next_order, "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC)
    }
    try:
        db.lessons.insert_one(lesson_document)
        print(f"Successfully added new lesson: '{title}' to course {course_id[:8]} (ID: {new_lesson_id})")
        return new_lesson_id
    except Exception as e:
        print(f"Error adding new lesson: {e}")
        return None

# Read Operations
def find_active_students():
    return list(db.users.find({"role": "student", "is_active": True}))

def get_course_details_with_instructor(course_title_substring=None):
    match_stage = {}
    if course_title_substring:
        escaped_substring = re.escape(course_title_substring)
        match_stage = {"title": {"$regex": escaped_substring, "$options": "i"}}
    pipeline = [
        {"$match": match_stage},
        {"$lookup": {"from": "users", "localField": "instructor_id", "foreignField": "_id", "as": "instructor_info"}},
        {"$unwind": "$instructor_info"},
        {"$project": {"_id": 1, "title": 1, "description": 1, "category": 1, "level": 1, "price": 1,
                      "instructor_name": {"$concat": ["$instructor_info.first_name", " ", "$instructor_info.last_name"]},
                      "instructor_email": "$instructor_info.email"}}
    ]
    return list(db.courses.aggregate(pipeline))

def get_courses_by_category(category_name):
    return list(db.courses.find({"category": category_name}))

def find_students_in_course(course_title):
    escaped_course_title = re.escape(course_title)
    course_doc = db.courses.find_one({"title": {"$regex": f"^{escaped_course_title}$", "$options": "i"}})
    if not course_doc:
        print(f"Error: Course '{course_title}' not found.")
        return []
    course_id = course_doc["_id"]
    pipeline = [
        {"$match": {"course_id": course_id}},
        {"$lookup": {"from": "users", "localField": "student_id", "foreignField": "_id", "as": "student_info"}},
        {"$unwind": "$student_info"},
        {"$project": {"_id": "$student_info._id", "username": "$student_info.username", "email": "$student_info.email",
                      "first_name": "$student_info.first_name", "last_name": "$student_info.last_name",
                      "enrollment_date": "$enrollment_date", "enrollment_status": "$status"}}
    ]
    return list(db.enrollments.aggregate(pipeline))

def search_courses_by_title_partial(search_term):
    escaped_search_term = re.escape(search_term)
    return list(db.courses.find({"title": {"$regex": escaped_search_term, "$options": "i"}}))

# Update Operations
def update_user_profile(user_id, new_bio=None, new_avatar=None, skills_to_add=None, is_active=None):
    update_fields = {}
    if new_bio is not None: update_fields["profile.bio"] = new_bio
    if new_avatar is not None: update_fields["profile.avatar"] = new_avatar
    if is_active is not None: update_fields["is_active"] = is_active
    update_fields["updated_at"] = datetime.now(UTC)

    try:
        if skills_to_add:
            result = db.users.update_one(
                {"_id": user_id},
                {"$set": {k: v for k, v in update_fields.items() if k != "profile.skills"},
                 "$addToSet": {"profile.skills": {"$each": skills_to_add}} if skills_to_add else {}}
            )
        else:
            result = db.users.update_one({"_id": user_id}, {"$set": update_fields})
        if result.matched_count > 0:
            print(f"Successfully updated user {user_id[:8]} profile. Matched: {result.matched_count}, Modified: {result.modified_count}")
        else:
            print(f"User {user_id[:8]} not found or no changes made.")
    except Exception as e:
        print(f"Error updating user profile: {e}")

def mark_course_as_published(course_id, is_published=True):
    try:
        result = db.courses.update_one(
            {"_id": course_id},
            {"$set": {"is_published": is_published, "updated_at": datetime.now(UTC)}}
        )
        if result.matched_count > 0:
            status = "published" if is_published else "unpublished"
            print(f"Successfully marked course {course_id[:8]} as {status}.")
        else:
            print(f"Course {course_id[:8]} not found or no changes made.")
    except Exception as e:
        print(f"Error marking course as published: {e}")

def update_assignment_grade(submission_id, new_grade, feedback=None):
    if not (0 <= new_grade <= 100):
        print(f"Error: Grade {new_grade} is out of valid range (0-100).")
        return
    update_fields = {"grade": float(new_grade), "updated_at": datetime.now(UTC)}
    if feedback is not None: update_fields["feedback"] = feedback
    try:
        result = db.submissions.update_one({"_id": submission_id}, {"$set": update_fields})
        if result.matched_count > 0:
            print(f"Successfully updated grade for submission {submission_id[:8]} to {new_grade}.")
        else:
            print(f"Submission {submission_id[:8]} not found or no changes made.")
    except Exception as e:
        print(f"Error updating assignment grade: {e}")

def add_tags_to_course(course_id, new_tags):
    try:
        result = db.courses.update_one(
            {"_id": course_id},
            {"$addToSet": {"tags": {"$each": new_tags}}, "$set": {"updated_at": datetime.now(UTC)}}
        )
        if result.matched_count > 0:
            print(f"Successfully added tags to course {course_id[:8]}.")
        else:
            print(f"Course {course_id[:8]} not found or no changes made.")
    except Exception as e:
        print(f"Error adding tags to course: {e}")

# Delete Operations
def soft_delete_user(user_id):
    try:
        result = db.users.update_one(
            {"_id": user_id},
            {"$set": {"is_active": False, "updated_at": datetime.now(UTC)}}
        )
        if result.matched_count > 0:
            print(f"Successfully soft-deleted user {user_id[:8]} (is_active set to False).")
        else:
            print(f"User {user_id[:8]} not found or already inactive.")
    except Exception as e:
        print(f"Error soft-deleting user: {e}")

def delete_enrollment(enrollment_id):
    try:
        result = db.enrollments.delete_one({"_id": enrollment_id})
        if result.deleted_count > 0:
            print(f"Successfully deleted enrollment {enrollment_id[:8]}.")
        else:
            print(f"Enrollment {enrollment_id[:8]} not found.")
    except Exception as e:
        print(f"Error deleting enrollment: {e}")

def remove_lesson_from_course(lesson_id):
    try:
        lesson_to_delete = db.lessons.find_one({"_id": lesson_id})
        if not lesson_to_delete:
            print(f"Lesson {lesson_id[:8]} not found. Cannot remove.")
            return

        course_id = lesson_to_delete["course_id"]
        deleted_order = lesson_to_delete["order"]
        delete_result = db.lessons.delete_one({"_id": lesson_id})

        if delete_result.deleted_count > 0:
            print(f"Successfully deleted lesson {lesson_id[:8]} from course {course_id[:8]}.")
            lessons_to_reorder = db.lessons.find(
                {"course_id": course_id, "order": {"$gt": deleted_order}}
            ).sort("order", 1)

            updates_performed = 0
            for lesson in lessons_to_reorder:
                new_order = lesson["order"] - 1
                update_result = db.lessons.update_one(
                    {"_id": lesson["_id"]},
                    {"$set": {"order": new_order, "updated_at": datetime.now(UTC)}}
                )
                if update_result.modified_count > 0: updates_performed += 1
            
            if updates_performed > 0:
                print(f"Re-ordered {updates_performed} subsequent lessons in course {course_id[:8]}.")
            else:
                print(f"No lessons needed re-ordering after deleting lesson {lesson_id[:8]}.")
        else:
            print(f"Lesson {lesson_id[:8]} not found. No deletion performed.")
    except Exception as e:
        print(f"Error removing lesson: {e}")

# --- Part 4: Advanced Queries and Aggregation ---

# Complex Queries
def find_courses_by_price_range(min_price, max_price):
    return list(db.courses.find({"price": {"$gte": min_price, "$lte": max_price}}))

def get_users_joined_last_n_months(num_months):
    six_months_ago = datetime.now(UTC) - timedelta(days=num_months * 30)
    return list(db.users.find({"created_at": {"$gte": six_months_ago}}))

def find_courses_with_specific_tags(tags_list):
    return list(db.courses.find({"tags": {"$in": tags_list}}))

def get_assignments_due_next_week():
    now_utc = datetime.now(UTC)
    one_week_from_now_utc = now_utc + timedelta(days=7)
    return list(db.assignments.find({"due_date": {"$gte": now_utc, "$lte": one_week_from_now_utc}}))

# Aggregation Pipelines

# Course Enrollment Statistics
def get_enrollments_per_course():
    pipeline = [
        {"$group": {"_id": "$course_id", "total_enrollments": {"$sum": 1}}},
        {"$lookup": {"from": "courses", "localField": "_id", "foreignField": "_id", "as": "course_info"}},
        {"$unwind": "$course_info"},
        {"$project": {"_id": 0, "course_id": "$_id", "course_title": "$course_info.title", "total_enrollments": 1}},
        {"$sort": {"total_enrollments": -1}}
    ]
    return list(db.enrollments.aggregate(pipeline))

def get_average_grade_per_course():
    pipeline = [
        {"$lookup": {"from": "assignments", "localField": "assignment_id", "foreignField": "_id", "as": "assignment_info"}},
        {"$unwind": "$assignment_info"},
        {"$lookup": {"from": "lessons", "localField": "assignment_info.lesson_id", "foreignField": "_id", "as": "lesson_info"}},
        {"$unwind": "$lesson_info"},
        {"$match": {"grade": {"$ne": None}}},
        {"$group": {"_id": "$lesson_info.course_id", "average_grade": {"$avg": "$grade"}}},
        {"$lookup": {"from": "courses", "localField": "_id", "foreignField": "_id", "as": "course_details"}},
        {"$unwind": "$course_details"},
        {"$project": {"_id": 0, "course_id": "$_id", "course_title": "$course_details.title", "average_grade": {"$round": ["$average_grade", 2]}}},
        {"$sort": {"average_grade": -1}}
    ]
    return list(db.submissions.aggregate(pipeline))

def get_course_count_by_category():
    pipeline = [
        {"$group": {"_id": "$category", "total_courses": {"$sum": 1}}},
        {"$project": {"_id": 0, "category": "$_id", "total_courses": 1}},
        {"$sort": {"total_courses": -1}}
    ]
    return list(db.courses.aggregate(pipeline))

# Student Performance Analysis
def get_average_grade_per_student():
    pipeline = [
        {"$match": {"grade": {"$ne": None}}},
        {"$group": {"_id": "$student_id", "average_grade": {"$avg": "$grade"}}},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "_id", "as": "student_info"}},
        {"$unwind": "$student_info"},
        {"$project": {"_id": 0, "student_id": "$_id", "student_name": {"$concat": ["$student_info.first_name", " ", "$student_info.last_name"]}, "average_grade": {"$round": ["$average_grade", 2]}}},
        {"$sort": {"average_grade": -1}}
    ]
    return list(db.submissions.aggregate(pipeline))

def get_course_completion_rate():
    pipeline = [
        {"$group": {
            "_id": "$course_id", "total_enrollments": {"$sum": 1},
            "completed_enrollments": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}}
        }},
        {"$addFields": {"completion_rate": {"$cond": [{"$eq": ["$total_enrollments", 0]}, 0, {"$multiply": [{"$divide": ["$completed_enrollments", "$total_enrollments"]}, 100]}]}}},
        {"$lookup": {"from": "courses", "localField": "_id", "foreignField": "_id", "as": "course_info"}},
        {"$unwind": "$course_info"},
        {"$project": {"_id": 0, "course_id": "$_id", "course_title": "$course_info.title", "total_enrollments": 1, "completed_enrollments": 1, "completion_rate": {"$round": ["$completion_rate", 2]}}},
        {"$sort": {"completion_rate": -1}}
    ]
    return list(db.enrollments.aggregate(pipeline))

def get_top_performing_students(limit=5):
    pipeline = [
        {"$match": {"grade": {"$ne": None}}},
        {"$group": {"_id": "$student_id", "average_grade": {"$avg": "$grade"}}},
        {"$sort": {"average_grade": -1}},
        {"$limit": limit},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "_id", "as": "student_info"}},
        {"$unwind": "$student_info"},
        {"$project": {"_id": 0, "student_id": "$_id", "student_name": {"$concat": ["$student_info.first_name", " ", "$student_info.last_name"]}, "average_grade": {"$round": ["$average_grade", 2]}}}
    ]
    return list(db.submissions.aggregate(pipeline))

# Instructor Analytics
def get_total_students_taught_by_instructor():
    pipeline = [
        {"$lookup": {"from": "enrollments", "localField": "_id", "foreignField": "course_id", "as": "enrollments"}},
        {"$unwind": "$enrollments"},
        {"$group": {"_id": "$instructor_id", "distinct_students": {"$addToSet": "$enrollments.student_id"}}},
        {"$addFields": {"total_students_taught": {"$size": "$distinct_students"}}},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "_id", "as": "instructor_info"}},
        {"$unwind": "$instructor_info"},
        {"$project": {"_id": 0, "instructor_id": "$_id", "instructor_name": {"$concat": ["$instructor_info.first_name", " ", "$instructor_info.last_name"]}, "total_students_taught": 1}},
        {"$sort": {"total_students_taught": -1}}
    ]
    return list(db.courses.aggregate(pipeline))

def get_average_course_rating_per_instructor():
    pipeline = [
        {"$lookup": {"from": "assignments", "localField": "assignment_id", "foreignField": "_id", "as": "assignment_details"}},
        {"$unwind": "$assignment_details"},
        {"$lookup": {"from": "lessons", "localField": "assignment_details.lesson_id", "foreignField": "_id", "as": "lesson_details"}},
        {"$unwind": "$lesson_details"},
        {"$lookup": {"from": "courses", "localField": "lesson_details.course_id", "foreignField": "_id", "as": "course_details"}},
        {"$unwind": "$course_details"},
        {"$match": {"grade": {"$ne": None}}},
        {"$group": {"_id": "$course_details.instructor_id", "average_grade": {"$avg": "$grade"}}},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "_id", "as": "instructor_info"}},
        {"$unwind": "$instructor_info"},
        {"$project": {"_id": 0, "instructor_id": "$_id", "instructor_name": {"$concat": ["$instructor_info.first_name", " ", "$instructor_info.last_name"]}, "average_course_grade": {"$round": ["$average_grade", 2]}}},
        {"$sort": {"average_course_grade": -1}}
    ]
    return list(db.submissions.aggregate(pipeline))

def get_revenue_generated_per_instructor():
    pipeline = [
        {"$group": {"_id": "$instructor_id", "total_course_value": {"$sum": "$price"}}},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "_id", "as": "instructor_info"}},
        {"$unwind": "$instructor_info"},
        {"$project": {"_id": 0, "instructor_id": "$_id", "instructor_name": {"$concat": ["$instructor_info.first_name", " ", "$instructor_info.last_name"]}, "total_revenue_from_courses": {"$round": ["$total_course_value", 2]}}},
        {"$sort": {"total_revenue_from_courses": -1}}
    ]
    return list(db.courses.aggregate(pipeline))

# Advanced Analytics
def get_monthly_enrollment_trends():
    pipeline = [
        {"$group": {"_id": {"year": {"$year": "$enrollment_date"}, "month": {"$month": "$enrollment_date"}}, "total_enrollments": {"$sum": 1}}},
        {"$project": {"_id": 0, "year": "$_id.year", "month": "$_id.month", "enrollment_count": "$total_enrollments"}},
        {"$sort": {"year": 1, "month": 1}}
    ]
    return list(db.enrollments.aggregate(pipeline))

def get_most_popular_course_categories():
    pipeline = [
        {"$group": {"_id": "$category", "course_count": {"$sum": 1}}},
        {"$project": {"_id": 0, "category": "$_id", "course_count": 1}},
        {"$sort": {"course_count": -1}},
        {"$limit": 5}
    ]
    return list(db.courses.aggregate(pipeline))

def get_student_engagement_by_submissions():
    pipeline = [
        {"$group": {"_id": "$student_id", "total_submissions": {"$sum": 1}}},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "_id", "as": "student_info"}},
        {"$unwind": "$student_info"},
        {"$project": {"_id": 0, "student_id": "$_id", "student_name": {"$concat": ["$student_info.first_name", " ", "$student_info.last_name"]}, "total_submissions": 1}},
        {"$sort": {"total_submissions": -1}}
    ]
    return list(db.submissions.aggregate(pipeline))

# --- Part 5: Indexing and Performance ---

def create_all_indexes():
    """
    Creates various indexes to optimize common queries.
    """
    print("\n--- Creating Indexes ---")
    indexes_to_create = {
        'users': [
            ([("email", ASCENDING)], {"unique": True, "name": "email_1"}),
            ([("created_at", ASCENDING)], {"name": "created_at_1"})
        ],
        'courses': [
            ([("title", ASCENDING), ("category", ASCENDING)], {"name": "title_1_category_1"}),
            ([("price", ASCENDING)], {"name": "price_1"}) # Added for price range queries
        ],
        'assignments': [
            ([("due_date", ASCENDING)], {"name": "due_date_1"})
        ],
        'enrollments': [
            ([("student_id", ASCENDING), ("course_id", ASCENDING)], {"name": "student_id_1_course_id_1"}),
            ([("student_id", ASCENDING)], {"name": "student_id_1"}), # For lookups
            ([("course_id", ASCENDING)], {"name": "course_id_1"})   # For lookups
        ]
    }

    for col_name, index_defs in indexes_to_create.items():
        for keys, options in index_defs:
            try:
                db[col_name].create_index(keys, **options)
                print(f"Index '{options.get('name', 'default')}' created successfully on '{col_name}'.")
            except Exception as e:
                print(f"Error creating index on '{col_name}{keys}' ({options.get('name', 'default')}): {e}")

def analyze_query_performance(query_name, query_func, *args, **kwargs):
    """
    Runs a query function, measures its execution time,
    and prints its explain() plan's performance metrics.
    """
    print(f"\n--- Analyzing Query Performance: {query_name} ---")

    start_time = time.perf_counter()
    
    # We need to get the cursor/pipeline to call explain() on it
    explain_result = None
    if query_name == "find_courses_by_price_range":
        explain_result = db.courses.find({"price": {"$gte": kwargs['min_price'], "$lte": kwargs['max_price']}}).explain()
        results = list(db.courses.find({"price": {"$gte": kwargs['min_price'], "$lte": kwargs['max_price']}}))
    elif query_name == "get_users_joined_last_n_months":
        six_months_ago = datetime.now(UTC) - timedelta(days=kwargs['num_months'] * 30)
        explain_result = db.users.find({"created_at": {"$gte": six_months_ago}}).explain()
        results = list(db.users.find({"created_at": {"$gte": six_months_ago}}))
    elif query_name == "find_students_in_course":
        course_title = args[0] # The course title
        escaped_course_title = re.escape(course_title)
        course_doc = db.courses.find_one({"title": {"$regex": f"^{escaped_course_title}$", "$options": "i"}})
        if course_doc:
            course_id = course_doc["_id"]
            pipeline = [
                {"$match": {"course_id": course_id}},
                {"$lookup": {"from": "users", "localField": "student_id", "foreignField": "_id", "as": "student_info"}},
                {"$unwind": "$student_info"},
                {"$project": {"_id": "$student_info._id", "username": "$student_info.username", "email": "$student_info.email",
                              "first_name": "$student_info.first_name", "last_name": "$student_info.last_name",
                              "enrollment_date": "$enrollment_date", "enrollment_status": "$status"}}
            ]
            explain_result = db.enrollments.aggregate(pipeline).explain()
            results = list(db.enrollments.aggregate(pipeline))
        else:
            print(f"Course '{course_title}' not found for performance analysis.")
            return

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    print(f"Python-side Query Execution Time: {duration_ms:.2f} ms")

    if explain_result and 'executionStats' in explain_result:
        stats = explain_result['executionStats']
        print("\n--- MongoDB Explain() Execution Stats ---")
        print(f"MongoDB Execution Time: {stats.get('executionTimeMillis', 'N/A')} ms")
        print(f"Documents Examined: {stats.get('totalDocsExamined', 'N/A')}")
        print(f"Keys Examined: {stats.get('totalKeysExamined', 'N/A')}")
        winning_plan = stats.get('winningPlan', {})
        input_stage = winning_plan.get('inputStage', {})
        if input_stage.get('stage') == 'IXSCAN':
            print(f"Used Index: {input_stage.get('indexName', 'N/A')}")
        elif input_stage.get('stage') == 'COLLSCAN':
            print("Used Index: No (Collection Scan)")
        else:
            print(f"Used Index: Complex Plan (Stage: {input_stage.get('stage')})")
        print("------------------------------------------")
    elif explain_result:
        print("\n--- Full Explain() Output (no executionStats) ---")
        print(explain_result)
        print("--------------------------------------------------")
    else:
        print("Explain results not available.")

# --- Part 6: Data Validation and Error Handling ---
# (As implemented in mongo_db_error_handling)

def attempt_insert_duplicate_user(user_data):
    print(f"\n--- Attempting to insert user (possible duplicate): {user_data.get('email')} ---")
    try:
        result = db.users.insert_one(user_data)
        print(f"Successfully inserted user with ID: {result.inserted_id}")
    except DuplicateKeyError as e:
        print(f"Error: Duplicate Key Error encountered! Details: {e}")
        print("This typically means a user with the same _id or email already exists.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def attempt_insert_invalid_data_user(user_data):
    print(f"\n--- Attempting to insert user with invalid data type/enum: {user_data.get('email')} ---")
    try:
        result = db.users.insert_one(user_data)
        print(f"Successfully inserted user with ID: {result.inserted_id} (Unexpectedly - schema validation might be off or data passed validation)")
    except WriteError as e:
        print(f"Error: Write Error (Invalid Data Type/Enum) encountered! Details: {e}")
        print("This typically means a field value did not match the defined bsonType or enum in the schema validator.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def attempt_insert_missing_fields_user(user_data):
    print(f"\n--- Attempting to insert user with missing required fields: {user_data.get('email', 'N/A')} ---")
    try:
        result = db.users.insert_one(user_data)
        print(f"Successfully inserted user with ID: {result.inserted_id} (Unexpectedly - schema validation might be off or data passed validation)")
    except WriteError as e:
        print(f"Error: Write Error (Missing Required Field) encountered! Details: {e}")
        print("This typically means a required field was not provided in the document.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# --- Main Execution Block ---
if __name__ == "__main__":
    print("--- Starting EduHub MongoDB Operations Script ---")

    # --- Task 6.1 (and Part 1): Schema Validation ---
    # Running setup_collections_with_validation will drop existing collections
    # and recreate them with the latest validation rules.
    setup_collections_with_validation()

    # --- Task 2.1 & 2.2 (and Part 2): Insert Sample Data & Data Relationships ---
    insert_sample_data()

    # --- Task 5.1 (and Part 5): Index Creation ---
    create_all_indexes()

    # --- Task 3.1: Create Operations ---
    print("\n\n--- Running Basic Create Operations ---")
    new_student_id = add_new_student(
        "new_learner_max", "max.test@example.com", "pass123", "Max", "Learner",
        "Eager to explore new subjects.", ["Curious", "Fast Learner"]
    )
    existing_instructor = db.users.find_one({"role": "instructor"})
    if existing_instructor:
        instructor_id_for_new_course = existing_instructor["_id"]
        new_course_ai_id = create_new_course(
            "AI Fundamentals for Kids", "An exciting intro to AI for young minds.",
            instructor_id_for_new_course, "AI", "beginner", 15, 29.99, ["AI", "Kids", "Learning"]
        )
        if new_student_id and new_course_ai_id:
            enroll_student_in_course(new_student_id, new_course_ai_id)
            add_new_lesson(new_course_ai_id, "Lesson 1: What is AI?", "Learn about the basics of Artificial Intelligence.")
            add_new_lesson(new_course_ai_id, "Lesson 2: Friendly Robots", "Discover how AI helps robots in everyday life.")
    else:
        print("Skipping new course/enrollment: No instructor found.")


    # --- Task 3.2: Read Operations ---
    print("\n\n--- Running Basic Read Operations ---")
    print_documents("Active Students", find_active_students())
    print_documents("Courses in 'Programming' Category", get_courses_by_category("Programming"))
    print_documents("Courses matching 'Python' (partial, case-insensitive)", search_courses_by_title_partial("python"))
    print_documents("Students in 'Introduction to Python Programming'", find_students_in_course("Introduction to Python Programming"))
    print_documents("Course Details with Instructor Info", get_course_details_with_instructor("AI Fundamentals")) # Use the newly created course


    # --- Task 3.3: Update Operations ---
    print("\n\n--- Running Basic Update Operations ---")
    if new_student_id:
        update_user_profile(new_student_id, new_bio="Now an intermediate learner!", skills_to_add=["Advanced Topics"])
    if new_course_ai_id:
        mark_course_as_published(new_course_ai_id, True)
        add_tags_to_course(new_course_ai_id, ["Fun", "Interactive"])
    
    # Try to update a submission grade (find an ungraded one if possible, or a random one)
    submission_to_update = db.submissions.find_one({"grade": None}) or db.submissions.find_one({})
    if submission_to_update:
        update_assignment_grade(submission_to_update["_id"], 85.0, "Well done!")


    # --- Task 3.4: Delete Operations ---
    print("\n\n--- Running Basic Delete Operations ---")
    if new_student_id:
        soft_delete_user(new_student_id) # Soft delete the newly created student
        print_documents("Newly Created Student after Soft Delete", [db.users.find_one({"_id": new_student_id})])
    
    enrollment_to_delete = db.enrollments.find_one({"student_id": new_student_id, "course_id": new_course_ai_id})
    if enrollment_to_delete:
        delete_enrollment(enrollment_to_delete["_id"]) # Delete the enrollment if it exists
        print_documents("Enrollment after Hard Delete Check", [db.enrollments.find_one({"_id": enrollment_to_delete["_id"]})])

    # Remove one of the lessons from the newly created course
    lesson_to_remove = db.lessons.find_one({"course_id": new_course_ai_id, "order": 1})
    if lesson_to_remove:
        print_documents(f"Lessons in course {new_course_ai_id[:8]} before lesson removal", 
                       list(db.lessons.find({"course_id": new_course_ai_id}).sort("order", 1)))
        remove_lesson_from_course(lesson_to_remove["_id"])
        print_documents(f"Lessons in course {new_course_ai_id[:8]} after lesson removal", 
                       list(db.lessons.find({"course_id": new_course_ai_id}).sort("order", 1)))
    else:
        print("No lesson found to remove from the new AI course.")


    # --- Task 4.1: Complex Queries ---
    print("\n\n--- Running Complex Queries ---")
    print_documents("Courses ($50-$200)", find_courses_by_price_range(50, 200))
    print_documents("Users Joined Last 3 Months", get_users_joined_last_n_months(3))
    print_documents("Courses with 'AI' or 'Beginner' Tags", find_courses_with_specific_tags(["AI", "Beginner"]))
    print_documents("Assignments Due Next Week", get_assignments_due_next_week())

    # --- Task 4.2: Aggregation Pipeline ---
    print("\n\n--- Running Aggregation Pipelines ---")
    print_documents("Enrollments Per Course", get_enrollments_per_course())
    print_documents("Average Grade Per Student", get_average_grade_per_student())
    print_documents("Total Students Taught by Instructor", get_total_students_taught_by_instructor())
    print_documents("Monthly Enrollment Trends", get_monthly_enrollment_trends())


    # --- Task 5.2: Query Optimization (Analysis only) ---
    print("\n\n--- Running Query Optimization Analysis (using explain() and timing) ---")
    # Note: The actual optimization comes from applying indexes (Task 5.1).
    # This section demonstrates how to *check* performance improvements.

    analyze_query_performance("find_courses_by_price_range", None, min_price=50, max_price=150)
    analyze_query_performance("get_users_joined_last_n_months", None, num_months=3)
    analyze_query_performance("find_students_in_course", "Introduction to Python Programming")


    # --- Task 6.2: Error Handling Examples ---
    print("\n\n--- Running Error Handling Examples ---")
    # Ensure a test user exists for some error cases
    test_user_for_errors = db.users.find_one({"username": "testuser"})
    if not test_user_for_errors:
        test_user_id_err = str(uuid.uuid4())
        test_user_email_err = "test.error.user@example.com"
        db.users.insert_one({
            "_id": test_user_id_err, "username": "testuser", "email": test_user_email_err,
            "password_hash": "testpass", "role": "student", "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC), "first_name": "Test", "last_name": "Error",
            "profile": {"bio": "", "avatar": "", "skills": []}, "is_active": True
        })
        test_user_for_errors = db.users.find_one({"_id": test_user_id_err})
        print(f"Created a test user for error handling: {test_user_for_errors['email']} (ID: {test_user_for_errors['_id'][:8]})")
    
    # Duplicate Key Error (Existing Email)
    duplicate_email_user_data = {
        "_id": str(uuid.uuid4()), "username": "duplicate_email", "email": test_user_for_errors["email"],
        "password_hash": "some_hash", "role": "student", "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
        "first_name": "Dup", "last_name": "Email", "profile": {}, "is_active": True
    }
    attempt_insert_duplicate_user(duplicate_email_user_data)

    # Invalid Data Type Insertion (Email as int)
    invalid_email_user_data = {
        "_id": str(uuid.uuid4()), "username": "invalid_data_test", "email": 12345,
        "password_hash": "hash", "role": "student", "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
        "first_name": "Invalid", "last_name": "Type", "profile": {}, "is_active": True
    }
    attempt_insert_invalid_data_user(invalid_email_user_data)

    # Missing Required Field (missing 'username')
    missing_username_user_data = {
        "_id": str(uuid.uuid4()), "email": "missing.username@example.com", "password_hash": "hash",
        "role": "student", "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
        "first_name": "Missing", "last_name": "Field", "profile": {}, "is_active": True
    }
    attempt_insert_missing_fields_user(missing_username_user_data)

    # Invalid Enum Value (role as 'manager')
    invalid_enum_user_data = {
        "_id": str(uuid.uuid4()), "username": "invalid_role", "email": "invalid.role@example.com",
        "password_hash": "hash", "role": "manager", "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
        "first_name": "Invalid", "last_name": "Enum", "profile": {}, "is_active": True
    }
    attempt_insert_invalid_data_user(invalid_enum_user_data)


    # --- Final Step: Close Connection ---
    client.close()
    print("\n--- EduHub MongoDB Operations Script Finished. Connection Closed. ---")