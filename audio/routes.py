from flask import render_template, request, session, redirect, flash, url_for
from app import app
from app import db
import uuid
import datetime
import cloudinary
from cloudinary.uploader import upload

#  Cloudinary Config
cloudinary.config(
  cloud_name = "ismail61",
  api_key = "529773689658652",
  api_secret = "RtwcBxtuJpk67hpuVkFpAT8dEyk",
  secure = True
)

@app.route('/',  methods = ['GET'])
def home():
    if  'logged_in' in session and 'user' in session:
        response = db.responses.find({
            'userId': session['user']['_id']
        }).sort('createdAt', -1)
        audios = list(response)
        return render_template('home.html', audios = audios)
    else:
        flash('You need to login first')
        return render_template('signin.html')


@app.route('/predict-record', methods=['POST'])
def predict_record():
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
        #  Upload Cloudinary
        uploadedResponse = upload(file,resource_type = "video",  public_id=file_name )
        if(uploadedResponse):
            db.responses.insert_one({
                'url': uploadedResponse['url'],
                'userId': session['user']['_id'],
                'predict': 'happy',
                'createdAt': datetime.datetime.now(),
            })
            flash('Predict Successfully Done')
            return '<h1>Success</h1>' # TODO: sucess message
        else:
            flash('Image Uploaed Failed')
            return redirect(request.url)

    else:
        flash('You need to login first')
        return render_template('signin.html')
        
    