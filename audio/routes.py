from flask import render_template, request, session, redirect, flash, url_for
from app import app
from app import db
import uuid
import datetime
import cloudinary
from cloudinary.uploader import upload
import numpy as np
import io
import soundfile
import librosa
from urllib.request import urlopen
import pickle
em = ['happy','sad','neutral','angry']

# Use pickle to load in the pre-trained model.
with open('/home/bs1040/Old_PC/University/semester8/Thesis/Project/assets/cnn_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Extract Feature
def extract_feature(url, **kwargs):
    print('extract_feature function called')
    mfcc = kwargs.get("mfcc")
    chroma = kwargs.get("chroma")
    mel = kwargs.get("mel")
    contrast = kwargs.get("contrast")
    tonnetz = kwargs.get("tonnetz")

    # '/home/bs1040/Old_PC/University/semester8/Thesis/Project/audio/03-01-01-01-01-01-02.wav'
    with soundfile.SoundFile(io.BytesIO(urlopen(url).read())) as sound_file:
        X = sound_file.read(dtype="float32")
        sample_rate = sound_file.samplerate
        if chroma or contrast:
            stft = np.abs(librosa.stft(X))
        result = np.array([])
        if mfcc:
            mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=40).T, axis=0)
            result = np.hstack((result, mfccs))
        if chroma:
            chroma = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T,axis=0)
            result = np.hstack((result, chroma))
        if mel:
            mel = np.mean(librosa.feature.melspectrogram(X, sr=sample_rate).T,axis=0)
            result = np.hstack((result, mel))
        if contrast:
            contrast = np.mean(librosa.feature.spectral_contrast(S=stft, sr=sample_rate).T,axis=0)
            result = np.hstack((result, contrast))
        if tonnetz:
            tonnetz = np.mean(librosa.feature.tonnetz(y=librosa.effects.harmonic(X), sr=sample_rate).T,axis=0)
            result = np.hstack((result, tonnetz))
    return result


# Cloudinary Config
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


@app.route('/predict', methods=['POST'])
def make_prediction():
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
            features = np.array(extract_feature(uploadedResponse['url'], mfcc=True, chroma=True, mel=True).reshape(1, -1))
            f = np.expand_dims(features,axis=2)
            re = (model.predict(f)[0] > 0.5).astype("int32")
            result = re[0]
            print("result :", em[result])

            # db.responses.insert_one({
            #     'url': uploadedResponse['url'],
            #     'userId': session['user']['_id'],
            #     'predict': em[result],
            #     'createdAt': datetime.datetime.now(),
            # })
            return em[result]
        else:
            flash('Image Uploaed Failed')
            return redirect(request.url)

    else:
        flash('You need to login first')
        return render_template('signin.html')
        
    