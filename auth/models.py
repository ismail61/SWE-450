from flask import Flask, jsonify

class Auth:

    def signUp(self):
        user = {
            '_id': '',
            'name': '',
            'email': '',
            'password': '',
        }
        return jsonify(user), 200

    def signIn(self):
        user = {
            '_id': '',
            'name': '',
            'email': '',
            'password': '',
        }
        return jsonify(user), 200