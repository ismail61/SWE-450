from flask import Flask, render_template
app = Flask(__name__)

from auth.routes import *

# print('Hello World!')
dataS = {
    'helloW': 'Hello World!'
}

# @app.route('/')
# def home():
#     return render_template('layout.html', data = dataS)

# @app.route('/sign-in')
# def about():
#     return render_template('sign-in.html')

# @app.route('/sign-up')
# def signUp():
#     return render_template('sign-up.html')

if __name__ == '__main__':
    app.run(debug=True)