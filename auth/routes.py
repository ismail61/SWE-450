from flask import Flask, render_template, request
from app import app
from auth.models import Auth

@app.route('/auth/signup', methods = ['POST', 'GET'])
def signup():
    if(request.method == 'POST'):
        return Auth().signUp()
    else :
        return render_template('signup.html')

@app.route('/auth/signin', methods = ['POST', 'GET'])
def signin():
    if(request.method == 'POST'):
        return Auth().signIn()
    else :
        return render_template('signin.html')
