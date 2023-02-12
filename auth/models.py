from flask import request, render_template, flash, session, redirect
from app import db
import uuid

class Auth:

    def start_session(self, user):
        del user['password']
        session['logged_in'] = True
        session['user'] = user
        return redirect('/')

    def signUp(self):
        user = {
            '_id': uuid.uuid4().hex,
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
        }

        #check if user already exists
        alreadyExists = db.users.find_one({'email': user['email']})
        if alreadyExists:
            flash('This email already exists', 'error')
            return render_template('signup.html', email=user['email'], name = user['name'])
        
        if db.users.insert_one(user):
            return self.start_session(user)

        flash('Signup Failed', 'error')
        return render_template('signup.html', email=user['email'], name = user['name'])

    def signout(self):
        session.clear()
        return redirect('/auth/signin')

    def signIn(self):
        user = db.users.find_one({
            "email": request.form.get('email'),
            "password": request.form.get('password')
        })

        if user:
            return self.start_session(user)
        
        flash('Invalid Credentials', 'error')
        return render_template('signin.html', email=request.form.get('email'))