from flask import render_template, request, session, redirect, flash, url_for
from app import app
from app import db
import uuid
from tensorflow.keras.models import load_model
import cloudinary
import os
from cloudinary.uploader import upload
from datetime import datetime
import numpy as np
import io
import soundfile
import librosa
from urllib.request import urlopen
import pickle
em = ['happy','sad','neutral','angry']
# em = ['fear', 'angry', 'neutral', 'happy', 'sad', 'surprise']
# em = ['neutral', 'calm', 'happy', 'sad', 'angry', 'fearful', 'disgust', 'surprised']
CAT6 = ['fear', 'angry', 'neutral', 'happy', 'sad', 'surprise']

# Use pickle to load in the pre-trained model.
# with open('/home/bs1040/Old_PC/University/semester8/Thesis/Project/assets/cnn_model.pkl', 'rb') as f:
#     model = pickle.load(f)

# load models
model = load_model("/home/bs1040/Old_PC/University/semester8/Thesis/Project/assets/model3.h5")
gmodel = load_model("/home/bs1040/Old_PC/University/semester8/Thesis/Project/assets/model_mw.h5")

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

def get_mfccs(audio, limit):
    y, sr = librosa.load(audio)
    a = librosa.feature.mfcc(y, sr=sr, n_mfcc=40)
    print(a)
    if a.shape[1] > limit:
        mfccs = a[:, :limit]
    elif a.shape[1] < limit:
        mfccs = np.zeros((a.shape[0], limit))
        mfccs[:, :a.shape[1]] = a
    return mfccs

def save_audio(file):
    if not os.path.exists("audio1"):
        os.makedirs("audio1")
    folder = "audio1"
    # clear the folder to avoid storage overload
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

    path = 'audio1/' + file.filename + '.wav'
    with open(path, "wb") as f:
        f.write(file.getbuffer())
    return 0

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
            with soundfile.SoundFile(io.BytesIO(urlopen(uploadedResponse['url']).read())) as sound_file:
                # features = np.array(extract_feature(uploadedResponse['url'], mfcc=True, chroma=True, mel=True).reshape(1, -1))
                # f = np.expand_dims(features,axis=2)
 
                save_audio(file)
                # path = os.path.join("audio1", file.filename)
                path = 'audio1/' + file.filename + '.wav'
                mfccs = get_mfccs(path, model.input_shape[-1])
                mfccs = mfccs.reshape(1, *mfccs.shape)
                # re = (model.predict(mfccs)[0] > 0.5).astype("int32")
                pred = model.predict(mfccs)[0]
                # result = re[0]
                print(f"result11 : {pred}")
                print("result :", CAT6[pred.argmax()])
                
                # gender detection
                gmfccs = get_mfccs(path, gmodel.input_shape[-1])
                gmfccs = gmfccs.reshape(1, *gmfccs.shape)
                gpred = gmodel.predict(gmfccs)[0]
                ind = gpred.argmax()
                gdict = [["female", "woman.png"], ["male", "man.png"]]
                txt = "Predicted gender: " + gdict[ind][0]
                print(txt)

                # db.responses.insert_one({
                #     'url': uploadedResponse['url'],
                #     'userId': session['user']['_id'],
                #     'predict': em[result],
                #     'createdAt': datetime.datetime.now(),
                # })
                # return em[result]
                return CAT6[pred.argmax()]
        else:
            flash('Image Uploaed Failed')
            return redirect(request.url)

    else:
        flash('You need to login first')
        return render_template('signin.html')
        
    