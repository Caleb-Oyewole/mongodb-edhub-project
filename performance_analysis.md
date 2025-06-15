Performance Analysis Results 
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
