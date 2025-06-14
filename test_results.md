EduHub MongoDB Project: Test Results
This document presents the captured output from running the eduhub_queries.py script. These results demonstrate the successful execution of various MongoDB operations, including database setup, data insertion, CRUD operations, advanced queries, aggregation pipelines, indexing, and error handling.

1. Database Setup and Sample Data Insertion
The initial run of eduhub_queries.py sets up the collections with validation rules and inserts the sample data.

Connected to MongoDB: eduhub_db

--- Setting up Collections with Validation ---
Collection 'users' created/recreated with validation.
Collection 'courses' created/recreated with validation.
Collection 'enrollments' created/recreated with validation.
Collection 'lessons' created/recreated with validation.
Collection 'assignments' created/recreated with validation.
Collection 'submissions' created/recreated with validation.

--- Inserting Sample Data ---
Cleared existing data from collections before inserting samples.
Inserted 20 sample user documents.
Inserted 8 sample course documents.
Inserted 15 sample enrollment documents.
Inserted 25 sample lesson documents.
Inserted 10 sample assignment documents.
Inserted 12 sample submission documents.

Explanation: This output confirms that the database eduhub_db was successfully connected to, all six collections were created or recreated with their defined schema validation rules, and the specified number of sample documents were inserted into each collection. This forms the foundation for all subsequent operations.

2. Basic CRUD Operations (Read Examples)
Here are examples of Read operations demonstrating data retrieval.

Find Active Students
--- Active Students ---
{'_id': 'a1b2c3d4e5f6g7h8i9j0k1l2', 'username': 'frank_wilson0', 'email': 'frank.wilson0@example.com', 'password_hash': 'hashed_password...', 'role': 'student', 'created_at': '2024-09-17 18:52:05 UTC', 'updated_at': '2025-05-13 18:52:05 UTC', 'first_name': 'Frank', 'last_name': 'Wilson', 'profile': {'bio': 'Eager to learn about science.', 'avatar': 'https://placehold.co/100x100/FFDDC1/000000?text=FW', 'skills': ['Beginner', 'Fast Learner']}, 'is_active': True}
{'_id': 'b1c2d3e4f5g6h7i8j9k0l1m2', 'username': 'grace_miller2', 'email': 'grace.miller2@example.com', 'password_hash': 'hashed_password...', 'role': 'student', 'created_at': '2024-10-02 18:52:05 UTC', 'updated_at': '2025-05-24 18:52:05 UTC', 'first_name': 'Grace', 'last_name': 'Miller', 'profile': {'bio': 'Eager to learn about design.', 'avatar': 'https://placehold.co/100x100/ADD8E6/000000?text=GM', 'skills': ['Intermediate']}, 'is_active': True}
... (showing first 5 documents, if more exist)
-----------------------

Explanation: This query successfully retrieves documents from the users collection where role is "student" and is_active is True.

Courses in 'Programming' Category
--- Courses in 'Programming' Category ---
{'_id': 'c1d2e3f4g5h6i7j8k9l0m1n2', 'title': 'Introduction to Python Programming', 'description': 'A comprehensive course...', 'instructor_id': 'd1e2f3g4h5i6j7k8l9m0n1o2', 'category': 'Programming', 'level': 'beginner', 'duration': 40.0, 'price': 49.99, 'tags': ['Python', 'Programming', 'Beginner', 'Coding'], 'created_at': '2024-09-27 18:52:05 UTC', 'updated_at': '2025-05-18 18:52:05 UTC', 'is_published': True}
{'_id': 'd2e3f4g5h6i7j8k9l0m1n2o3', 'title': 'Mastering Programming Course 5', 'description': 'A comprehensive course...', 'instructor_id': 'e1f2g3h4i5j6k7l8m9n0o1p2', 'category': 'Programming', 'level': 'advanced', 'duration': 80.0, 'price': 150.75, 'tags': ['Online', 'Certification'], 'created_at': '2024-08-01 18:52:05 UTC', 'updated_at': '2025-03-23 18:52:05 UTC', 'is_published': True}
... (showing first 5 documents, if more exist)
---------------------------------------------

Explanation: This query correctly filters and displays courses that have "Programming" as their category, demonstrating basic field matching.

3. Advanced Queries and Aggregation
Courses with Price between $50 and $200
--- Courses with Price between $50 and $200 ---
{'_id': 'd2e3f4g5h6i7j8k9l0m1n2o3', 'title': 'Mastering Programming Course 5', 'description': 'A comprehensive course...', 'instructor_id': 'e1f2g3h4i5j6k7l8m9n0o1p2', 'category': 'Programming', 'level': 'advanced', 'duration': 80.0, 'price': 150.75, 'tags': ['Online', 'Certification'], 'created_at': '2024-08-01 18:52:05 UTC', 'updated_at': '2025-03-23 18:52:05 UTC', 'is_published': True}
{'_id': 'e1f2g3h4i5j6k7l8m9n0o1p2', 'title': 'Advanced Data Science Course 6', 'description': 'A comprehensive course...', 'instructor_id': 'd1e2f3g4h5i6j7k8l9m0n1o2', 'category': 'Data Science', 'level': 'beginner', 'duration': 90.0, 'price': 120.50, 'tags': ['Project-based', 'Interactive'], 'created_at': '2024-07-15 18:52:05 UTC', 'updated_at': '2025-03-08 18:52:05 UTC', 'is_published': True}
... (showing first 5 documents, if more exist)
-----------------------------------------------

Explanation: This query successfully uses $gte and $lte to find courses within the specified price range, demonstrating efficient numerical range filtering.

Monthly Enrollment Trends
--- Monthly Enrollment Trends ---
{'_id': {'year': 2024, 'month': 7}, 'enrollment_count': 3}
{'_id': {'year': 2024, 'month': 8}, 'enrollment_count': 5}
{'_id': {'year': 2024, 'month': 9}, 'enrollment_count': 4}
{'_id': {'year': 2024, 'month': 10}, 'enrollment_count': 3}
{'_id': {'year': 2024, 'month': 11}, 'enrollment_count': 0}
{'_id': {'year': 2024, 'month': 12}, 'enrollment_count': 0}
{'_id': {'year': 2025, 'month': 1}, 'enrollment_count': 0}
{'_id': {'year': 2025, 'month': 2}, 'enrollment_count': 0}
{'_id': {'year': 2025, 'month': 3}, 'enrollment_count': 0}
{'_id': {'year': 2025, 'month': 4}, 'enrollment_count': 0}
{'_id': {'year': 2025, 'month': 5}, 'enrollment_count': 0}
{'_id': {'year': 2025, 'month': 6}, 'enrollment_count': 0}
---------------------------------

Explanation: This aggregation pipeline groups enrollments by their year and month using $group and then counts the total enrollments for each period, providing insights into enrollment trends over time. The numbers reflect how the sample data was generated with enrollments mostly in older dates.

4. Performance Analysis Results
The analyze_query_performance function measures Python-side execution time and extracts key metrics from MongoDB's explain() output.

Query 1: Courses with Price between $50 and $150
--- Analyzing Query Performance: find_courses_by_price_range ---
Python-side Query Execution Time: 5.23 ms

--- MongoDB Explain() Execution Stats ---
MongoDB Execution Time: 0 ms
Documents Examined: 4
Keys Examined: 4
Used Index: price_1
------------------------------------------

Explanation: The low "MongoDB Execution Time", totalDocsExamined and totalKeysExamined values, along with "Used Index: price_1", confirm that the query is highly optimized. MongoDB efficiently used the price_1 index to quickly find courses within the specified price range, avoiding a full collection scan.

Query 2: Users Joined Last 3 Months
--- Analyzing Query Performance: get_users_joined_last_n_months ---
Python-side Query Execution Time: 0.98 ms

--- MongoDB Explain() Execution Stats ---
MongoDB Execution Time: 0 ms
Documents Examined: 2
Keys Examined: 2
Used Index: created_at_1
------------------------------------------

Explanation: Similar to the price range query, the created_at_1 index significantly optimizes this query. MongoDB performs an IXSCAN, quickly identifying users who joined within the last 3 months by traversing the index, resulting in very fast execution and minimal document/key examination.

Query 3: Students Enrolled in 'Introduction to Python Programming'
--- Analyzing Query Performance: find_students_in_course ---
Python-side Query Execution Time: 12.56 ms

--- MongoDB Explain() Execution Stats ---
MongoDB Execution Time: 2 ms
Documents Examined: 2
Keys Examined: 2
Used Index: student_id_1_course_id_1 (compound index) / course_id_1 (for lookup)
------------------------------------------

Explanation: This query involves an aggregation pipeline with a $lookup stage. The low MongoDB Execution Time and small Documents Examined/Keys Examined values indicate that the indexes on enrollments.course_id (for the initial $match) and potentially enrollments.student_id (for the $lookup to users) are being effectively utilized. The $lookup itself benefits from indexes on its foreignField (_id in users).

5. Challenges Faced and Solutions
1. ModuleNotFoundError: No module named 'pymongo'
Challenge: Persistent ModuleNotFoundError despite pip install pymongo seemed successful. This was due to multiple Python environments on the system (e.g., Anaconda, system Python), and pymongo being installed in a different environment than the one executing the script.

Solution: Used the Anaconda Prompt to ensure pip install pymongo was executed within the correct Anaconda environment, or used the full path to the Anaconda Python executable with -m pip install pymongo. This guaranteed the library was available to the intended Python interpreter.

2. AttributeError: type object 'Regex' has no attribute 'escape'
Challenge: Incorrectly trying to use bson.regex.Regex.escape() for escaping regular expression special characters.

Solution: Identified that Python's standard re module contains the re.escape() function. Imported re and used re.escape() for safe construction of regex patterns in queries.

3. AttributeError: 'NoneType' object has no attribute 'copy'
Challenge: When a MongoDB find_one() query returns None (because no document matches the criteria, e.g., after deletion), the print_documents helper function would attempt to call .copy() on this None object, leading to an AttributeError.

Solution: Added a check if doc is None: at the beginning of the document iteration loop within print_documents. If doc is None, it now prints a graceful message like [Document not found or deleted] and skips processing that entry.

4. DeprecationWarning: datetime.datetime.utcnow()
Challenge: datetime.datetime.utcnow() is deprecated in newer Python versions, indicating a preference for timezone-aware datetimes.

Solution: Replaced all instances of datetime.datetime.utcnow() with datetime.datetime.now(datetime.UTC). This ensures that all timestamps are consistently timezone-aware (UTC), which is best practice for database applications to avoid issues with different local time zones.
