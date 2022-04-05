from pymongo import MongoClient

data = MongoClient('mongodb+srv://Subrata2001:Subrata2001@cluster0.ywnwn.mongodb.net/MimirQuiz?retryWrites=true&w=majority')
db = data.get_database("MimirQuiz")
mimir_details = db.mimir_details