from pymongo import MongoClient

uri = "mongodb+srv://founders:wuhqHr5sAoBW32DL@cluster0.5ahszmy.mongodb.net/Pupil_teach"
client = MongoClient(uri)
db = client["Pupil_teach"]
print("Using database:", db.name)
print("Available collections:", db.list_collection_names())
grades = list(db["lesson_script"].find())
print("Fetched grades from MongoDB:", grades)