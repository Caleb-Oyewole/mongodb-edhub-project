# mongodb-edhub-project
AltSchool Tinyuka Second Semester Project Exam
EduHub MongoDB Project Documentation
This repository contains Python scripts for managing the eduhub_db MongoDB database, designed for an online learning platform. It includes functionalities for setting up the database schema with validation, inserting sample data, performing basic CRUD (Create, Read, Update, Delete) operations, executing advanced queries and aggregations, optimizing query performance with indexing, and handling common database errors.

1. Project Setup Instructions
To get this project running on your local machine, follow these steps:

Prerequisites:
MongoDB Community Server: Download and install MongoDB from the official MongoDB website. Ensure it's running, typically on localhost:27017.

Python 3.x: Make sure you have Python installed. You can download it from python.org.

PyMongo Library: This is the Python driver for MongoDB. Install it using pip:

pip install pymongo

UUID and datetime (built-in): These standard Python libraries are used for generating unique IDs and handling dates/times.

Running the Project:
Save the Code:
Save the entire content of the eduhub_queries.py file (provided previously) into a file named eduhub_queries.py in a directory on your computer.

Open your Terminal or Command Prompt:
Navigate to the directory where you saved eduhub_queries.py.

Execute the Script:
Run the Python script. This single script contains a main execution block (if __name__ == "__main__":) that will sequentially perform all the setup, data insertion, and demonstration tasks.

python eduhub_queries.py

As the script runs, it will print messages to your console indicating the progress, successful operations, and any errors encountered during the demonstration of error handling.

Verify (Optional but Recommended):
You can use a tool like MongoDB Compass (a free GUI for MongoDB) to connect to mongodb://localhost:27017/ and visually inspect the eduhub_db database and its collections. You'll see the created collections and the sample data inserted.

2. Database Schema Documentation
The eduhub_db database consists of six collections, each with specific validation rules enforced by JSON Schema.

users Collection
Stores information about students and instructors.

_id: string (UUID, required, unique) - Primary key.

username: string (required, minLength: 3) - Unique user handle.

email: string (required, unique, email format) - Unique email address.

password_hash: string (required) - Hashed password.

role: string (required, enum: ["student", "instructor"]) - User's role on the platform.

created_at: date (required) - Timestamp of user creation.

updated_at: date (required) - Timestamp of last update.

first_name: string

last_name: string

profile: object (nested)

bio: string - User's biography.

avatar: string - URL to user's avatar image.

skills: array of string - List of skills.

is_active: boolean - Indicates if the user account is active (for soft-delete).

courses Collection
Stores information about courses offered.

_id: string (UUID, required, unique) - Primary key.

title: string (required, minLength: 5) - Course title.

description: string (required, minLength: 10) - Course description.

instructor_id: string (required, reference to users._id) - The ID of the instructor teaching the course.

category: string - E.g., "Programming", "Data Science".

level: string (enum: ["beginner", "intermediate", "advanced"]) - Course difficulty level.

duration: double (in hours) - Estimated course duration.

price: double - Course price.

tags: array of string - Keywords or tags associated with the course.

created_at: date (required) - Timestamp of course creation.

updated_at: date (required) - Timestamp of last update.

is_published: boolean - Indicates if the course is publicly visible.

enrollments Collection
Records student enrollments in courses.

_id: string (UUID, required, unique) - Primary key.

student_id: string (required, reference to users._id) - The ID of the enrolled student.

course_id: string (required, reference to courses._id) - The ID of the course enrolled in.

enrollment_date: date (required) - Date of enrollment.

status: string (required, enum: ["active", "completed", "dropped"]) - Enrollment status.

lessons Collection
Details individual lessons within courses.

_id: string (UUID, required, unique) - Primary key.

course_id: string (required, reference to courses._id) - The ID of the course this lesson belongs to.

title: string (required, minLength: 5) - Lesson title.

content: string (required, minLength: 20) - Lesson material (text, links, etc.).

order: int (required, minimum: 1) - Order of the lesson within the course.

created_at: date

updated_at: date

assignments Collection
Manages course assignments.

_id: string (UUID, required, unique) - Primary key.

lesson_id: string (required, reference to lessons._id) - The ID of the lesson this assignment is for.

title: string (required, minLength: 5) - Assignment title.

description: string (required, minLength: 10) - Assignment description.

due_date: date (required) - Assignment due date.

max_score: double - Maximum possible score for the assignment.

created_at: date

updated_at: date

submissions Collection
Stores student submissions for assignments.

_id: string (UUID, required, unique) - Primary key.

assignment_id: string (required, reference to assignments._id) - The ID of the assignment submitted.

student_id: string (required, reference to users._id) - The ID of the student who submitted.

submission_date: date (required) - Date of submission.

content: string (required, minLength: 1) - Submission content (e.g., text, file path).

grade: double or null (0-100) - Grade received for the submission.

feedback: string or null - Instructor feedback.

created_at: date

updated_at: date

3. Query Explanations
The eduhub_queries.py script contains functions demonstrating various MongoDB operations.

Basic CRUD Operations (Part 3)
Create:

add_new_student(...): Inserts a new document into the users collection with role: "student".

create_new_course(...): Inserts a new document into the courses collection, referencing an instructor_id.

enroll_student_in_course(...): Creates a new enrollment document, linking a student_id and course_id.

add_new_lesson(...): Adds a lesson to a specific course_id, automatically managing the order field.

Read:

find_active_students(): Retrieves all users with role: "student" and is_active: True.

get_course_details_with_instructor(course_title_substring): Uses $lookup aggregation to get course details joined with instructor's name and email.

get_courses_by_category(category_name): Finds courses by a specific category.

find_students_in_course(course_title): Finds students enrolled in a specific course by title, using $lookup for joins.

search_courses_by_title_partial(search_term): Performs a case-insensitive, partial match search on course titles using $regex.

Update:

update_user_profile(...): Modifies fields within a user's document, including using $addToSet for adding skills to an array without duplicates.

mark_course_as_published(course_id, is_published): Changes the is_published status of a course.

update_assignment_grade(submission_id, new_grade, feedback): Updates the grade and feedback fields for a specific submission.

add_tags_to_course(course_id, new_tags): Adds new tags to a course's tags array using $addToSet to prevent duplicates.

Delete:

soft_delete_user(user_id): Sets is_active to False for a user, retaining historical data.

delete_enrollment(enrollment_id): Permanently removes an enrollment document.

remove_lesson_from_course(lesson_id): Deletes a lesson and automatically re-orders the remaining lessons in the same course.

Advanced Queries and Aggregation (Part 4)
Complex Queries:

find_courses_by_price_range(min_price, max_price): Uses $gte and $lte for numerical range queries.

get_users_joined_last_n_months(num_months): Filters users based on created_at timestamp within a dynamic date range using $gte.

find_courses_with_specific_tags(tags_list): Utilizes the $in operator to find documents where an array field contains any of the specified values.

get_assignments_due_next_week(): Queries assignments based on due_date falling within a calculated date range using $gte and $lte.

Aggregation Pipelines:

get_enrollments_per_course(): Counts total enrollments for each course using $group and $lookup.

get_average_grade_per_course(): Calculates average submission grades per course, involving multiple $lookup stages to join across collections.

get_course_count_by_category(): Groups courses by category and sums their counts.

get_average_grade_per_student(): Calculates each student's average grade from their submissions.

get_course_completion_rate(): Determines course completion rates based on enrollment status.

get_top_performing_students(limit): Finds top N students by average grade using $sort and $limit.

get_total_students_taught_by_instructor(): Counts distinct students taught by each instructor.

get_average_course_rating_per_instructor(): Averages grades for courses taught by each instructor.

get_revenue_generated_per_instructor(): Calculates simplified revenue per instructor based on course prices.

get_monthly_enrollment_trends(): Groups enrollments by year and month to show trends.

get_most_popular_course_categories(): Identifies top categories by course count.

get_student_engagement_by_submissions(): Measures engagement by total submissions per student.

4. Performance Analysis Results (Part 5)
The analyze_query_performance function in eduhub_queries.py demonstrates how to use explain() and Python's time module to evaluate query efficiency.

Key Optimization Strategy: Indexing.

Here's a summary of expected performance improvements when relevant indexes are in place (as set up by create_all_indexes()):

User Email Lookup:

Query: db.users.find_one({"email": "..."})

Optimization: A unique index on users.email (email_1).

Expected explain() output: IXSCAN (Index Scan) will be the winning plan, indicating that MongoDB directly uses the index to find the document quickly, examining very few documents/keys.

Performance: Extremely fast, especially for large users collections.

Courses by Price Range:

Query: db.courses.find({"price": {"$gte": 50, "$lte": 200}})

Optimization: An index on courses.price (price_1).

Expected explain() output: IXSCAN on the price_1 index. MongoDB will efficiently traverse the index B-tree to find documents within the specified range.

Performance: Significant improvement over a full collection scan, especially when the price range is selective.

Users Joined Recently:

Query: db.users.find({"created_at": {"$gte": N_months_ago}})

Optimization: An index on users.created_at (created_at_1).

Expected explain() output: IXSCAN on created_at_1. The query optimizer uses the index to quickly locate documents within the date range.

Performance: Faster retrieval of recent users, avoiding scanning the entire collection.

Students Enrolled in a Specific Course (Aggregation with $lookup):

Query: Aggregation pipeline involving enrollments to users lookup for a specific course_id.

Optimization: Compound index on enrollments.student_id and enrollments.course_id (student_id_1_course_id_1), and individual indexes (student_id_1, course_id_1) for the localField and foreignField used in $lookup.

Expected explain() output: The IXSCAN stage within the $lookup and $match parts of the pipeline will confirm index usage, showing reduced totalKeysExamined and totalDocsExamined compared to an unindexed lookup.

Performance: Lookups become much more efficient as MongoDB can use indexes to quickly find matching documents in the joined collections.

General Observation:
Without indexes, MongoDB performs a COLLSCAN (Collection Scan), meaning it reads every document in the collection to find matches. This is very slow for large datasets. With appropriate indexes, MongoDB can use an IXSCAN (Index Scan), which is much faster as it only reads relevant parts of the index and then directly accesses the matching documents.

5. Challenges Faced and Solutions
Developing this MongoDB integration involved some common challenges related to Python environments and database interactions:

ModuleNotFoundError: No module named 'pymongo':

Challenge: This error repeatedly occurred even after pip install pymongo seemed successful. The core issue was having multiple Python installations (e.g., system Python and Anaconda Python), and the pip command installing pymongo into one environment while the script was being executed by another.

Solution: The most effective solution was to use the Anaconda Prompt and run pip install pymongo directly within that environment. This ensured that pymongo was installed into the active Python interpreter used by tools like Jupyter Notebooks. Alternatively, using the full path to the desired Python executable with -m pip install pymongo in a standard command prompt also worked.

AttributeError: type object 'Regex' has no attribute 'escape':

Challenge: When attempting to escape special characters in regular expressions used with MongoDB's $regex operator, the bson.regex.Regex.escape() method was incorrectly assumed.

Solution: The correct module for escaping regex special characters in Python is the standard re module. Replacing Regex.escape() with re.escape() (after adding import re) resolved the issue.

AttributeError: 'NoneType' object has no attribute 'copy':

Challenge: This error occurred in the print_documents helper function when trying to display a document that had been deleted (and thus find_one() returned None). The function was attempting to call .copy() on None.

Solution: Added an explicit check if doc is None: at the beginning of the loop in print_documents to handle None values gracefully, printing a "Document not found or deleted" message instead of raising an error.

DeprecationWarning: datetime.datetime.utcnow():

Challenge: Modern Python and datetime practices recommend using timezone-aware datetimes. utcnow() is being deprecated.

Solution: Replaced all instances of datetime.utcnow() with datetime.datetime.now(datetime.UTC) and ensured from datetime import UTC was present. This promotes more robust date and time handling.

These challenges highlight the importance of understanding Python's environment management, correct library usage, and robust error handling in database applications.
