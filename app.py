from flask import Flask
import pymongo

app = Flask(__name__)
app.secret_key = 'super secret key'

# Connect to MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client.thesis

#routes
from auth.routes import *
from audio.routes import *

# main
if __name__ == '__main__':
    app.run(debug=True)