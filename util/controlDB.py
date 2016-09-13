from pymongo import MongoClient
import os

mongoUrl = "mongodb://localhost:27017"
client = MongoClient(mongoUrl)
db = client.CheckList
#db.Zrunning.drop()
#db.Crunning.drop()
#db.RobotTimeStamp.drop()
#db.BenderTimeStamp.drop()


