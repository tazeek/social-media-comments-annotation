from pymongo import ASCENDING, MongoClient

MONGO_URI = ""

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

# 2. Force a connection request by pinging the admin database
# The 'ping' command is lightweight and doesn't require specific privileges
client.admin.command('ping')
print("✅ Connection successful!")

collection = client["reddit_annotation"]["annotator_submissions"]

employee_1 = {
    "name": "Alice Smith",
    "role": "Software Engineer",
    "department": "Engineering",
    "age": 29
}

result_one = collection.insert_one(employee_1)
print(f"Successfully inserted one document with ID: {result_one.inserted_id}")

