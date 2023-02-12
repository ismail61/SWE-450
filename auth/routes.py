from flask import render_template, request, session, redirect, flash
from app import app
from auth.models import Auth

@app.route('/auth/signup', methods = ['POST', 'GET'])
def signup():
    if(request.method == 'POST'):
        return Auth().signUp()
    else :
         if 'logged_in' in session and 'user' in session:
            return redirect('/')
            # return render_template('home.html')7
         else:
            return render_template('signup.html')


@app.route('/user/signout')
def signout():
  return Auth().signout()


@app.route('/auth/signin', methods = ['POST', 'GET'])
def signin():
    if(request.method == 'POST'):
        return Auth().signIn()
    else :
        if 'logged_in' in session and 'user' in session:
            return redirect('/')
        else:
            return render_template('signin.html')