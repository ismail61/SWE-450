from flask import Flask, render_template, request, session, redirect, flash
from app import app
from app import db
import uuid
from auth.models import Auth
import cloudinary
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url

#  Cloudinary Config
cloudinary.config(
  cloud_name = "ismail61",
  api_key = "529773689658652",
  api_secret = "RtwcBxtuJpk67hpuVkFpAT8dEyk",
  secure = True
)

@app.route('/auth/signup', methods = ['POST', 'GET'])
def signup():
    if(request.method == 'POST'):
        return Auth().signUp()
    else :
         if 'logged_in' in session and 'user' in session:
            return render_template('home.html')
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
            return render_template('home.html')
        else:
            return render_template('signin.html')

@app.route('/',  methods = ['GET', 'POST'])
def home():
    if request.method == "POST" and 'logged_in' in session and 'user' in session:
        f = request.files['audio_data']
        with open('audio.wav', 'wb') as audio:
            f.save(audio)
        print('file uploaded successfully')

        return render_template('index.html', request="POST")
    elif request.method == "GET"  and 'logged_in' in session and 'user' in session:
        return render_template('home.html')
    else:
        flash('You need to login first')
        return render_template('signin.html')

@app.route('/save-record', methods=['POST'])
def save_record():
    if 'logged_in' in session and 'user' in session:
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        file_name = 'thesis/' + str(uuid.uuid4()) + ".mp3"
        #  Upload
        uploadedResponse = upload(file,resource_type = "video",  public_id=file_name )
        if(uploadedResponse):
            db.images.insert_one({
                'url': uploadedResponse['url'],
                'userId': session['user']['_id']
            })
            return '<h1>Success</h1>' # TODO: sucess message
        else:
            flash('Image Uploaed Failed')
            return redirect(request.url)

    else:
        flash('You need to login first')
        return render_template('signin.html')
        
    