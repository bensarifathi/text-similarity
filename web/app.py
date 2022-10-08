from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from flask_pymongo import PyMongo
import bcrypt
import spacy

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://db:27017/users"
mongo = PyMongo(app)
api = Api(app)


####################################
def user_exist(username):
    if mongo.db.users.find({
        "username": username
    }).count() == 0:
        return False
    return True


####################################
def verify_pw(username, password):
    hashed_pw = mongo.db.users.find({
        "username": username
    })[0]["password"]
    # a = [user for user in hashed_pw]
    # print(a)
    if bcrypt.checkpw(password.encode(), hashed_pw):
        return True
    return False


####################################
def count_tokens(username):
    return mongo.db.users.find({
        "username": username
    })[0]["tokens"]


####################################

class Register(Resource):
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["password"]
        if user_exist(username):
            retJson = {
                "status": 301,
                "message": "Invalid username"
            }
            return jsonify(retJson)
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        mongo.db.users.insert({
            "username": username,
            "password": hashed_pw,
            "tokens": 6
        })
        retJson = {
            "status": 200,
            "msg": "You Successefully registred for the API"
        }
        return jsonify(retJson)

class Detect(Resource):
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["password"]
        text1 = posted_data["text1"]
        text2 = posted_data["text2"]
        if not user_exist(username):
            retJson = {
                "status": 301,
                "message": "Invalid username"
            }
            return jsonify(retJson)
        correct_pw = verify_pw(username, password)
        if not correct_pw:
            retJson = {
                "status": 302,
                "message": "Invalid username/password"
            }
            return jsonify(retJson)
        num_token = count_tokens(username)
        if num_token <= 0:
            retJson = {
                "status": 303,
                "message": "your out of Tokens please refill !"
            }
            return jsonify(retJson)
        nlp = spacy.load('en_core_web_sm')
        text1 = nlp(text1)
        text2 = nlp(text2)
        ratio = text1.similarity(text2)
        retJson = {
            "status": 200,
            "similarity": ratio,
            "message": "Similarity score calculated successfully !"
        }
        mongo.db.users.update({
            "username": username
        }, {
            "$set": {
                "tokens": num_token - 1
            }
        })
        return jsonify(retJson)

class Refill(Resource):
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["admin_pw"]
        refill_amounts = posted_data["refill"]

        if not user_exist(username):
            retJson = {
                "status": 301,
                "message": "Invalid username !"
            }
            return jsonify(retJson)
        correct_pw = "xyz123"
        if not password == correct_pw:
            retJson = {
                "status": 304,
                "message": "Invalid Admin password"
            }
            return jsonify(retJson)
        current_tokens = count_tokens(username)
        mongo.db.users.update({
            "username": username
        }, {
            "$set": {
                "tokens": current_tokens + refill_amounts
            }
        })
        retJson = {
            "status": 200,
            "message": "Refilled successfully !"
        }
        return jsonify(retJson)

api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
