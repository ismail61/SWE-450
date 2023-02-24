from flask import render_template, request, session, redirect, flash
from app import app
from app import db
import uuid
from tensorflow.keras.models import load_model
import cloudinary
import os
from cloudinary.uploader import upload
import numpy as np
import io
import soundfile
from datetime import datetime
import librosa
import librosa.display
from urllib.request import urlopen
import base64
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from urllib.parse import quote
from PIL import Image
import cv2
# import pickle
em = ['happy','sad','neutral','angry']
# em = ['fear', 'angry', 'neutral', 'happy', 'sad', 'surprise']
# em = ['neutral', 'calm', 'happy', 'sad', 'angry', 'fearful', 'disgust', 'surprised']
CAT3 = ["positive", "neutral", "negative"]
CAT6 = ['fear', 'angry', 'neutral', 'happy', 'sad', 'surprise']
COLOR_DICT = {
    "neutral": "grey",
    "positive": "green",
    "happy": "green",
    "surprise": "orange",
    "fear": "purple",
    "negative": "red",
    "angry": "red",
    "sad": "lightblue",
    "disgust":"brown"
}

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

def get_melspec(audio):
    y, sr = librosa.load(audio, sr=44100)
    X = librosa.stft(y)
    Xdb = librosa.amplitude_to_db(abs(X))
    img = np.stack((Xdb,) * 3, -1)
    img = img.astype(np.uint8)
    grayImage = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    grayImage = cv2.resize(grayImage, (224, 224))
    rgbImage = np.repeat(grayImage[..., np.newaxis], 3, -1)
    return (rgbImage, Xdb)

def plot_colored_polar(fig, predictions, categories, title="", colors=COLOR_DICT):
    N = len(predictions)
    ind = predictions.argmax()

    COLOR = colors[categories[ind]]
    sector_colors = [colors[i] for i in categories]

    fig.set_facecolor("#d1d1e0")
    ax = plt.subplot(111, polar="True")

    theta = np.linspace(0.0, 2 * np.pi, N, endpoint=False)
    for sector in range(predictions.shape[0]):
        radii = np.zeros_like(predictions)
        radii[sector] = predictions[sector] * 10
        width = np.pi / 1.8 * predictions
        c = sector_colors[sector]
        ax.bar(theta, radii, width=width, bottom=0.0, color=c, alpha=0.25)

    angles = [i / float(N) * 2 * np.pi for i in range(N)]
    angles += angles[:1]

    data = list(predictions)
    data += data[:1]
    plt.polar(angles, data, color=COLOR, linewidth=2)
    plt.fill(angles, data, facecolor=COLOR, alpha=0.25)

    ax.spines['polar'].set_color('lightgrey')
    ax.set_theta_offset(np.pi / 3)
    ax.set_theta_direction(-1)
    plt.xticks(angles[:-1], categories)
    ax.set_rlabel_position(0)
    plt.yticks([0, .25, .5, .75, 1], color="grey", size=8)

    plt.suptitle(title, color="darkblue", size=10)
    plt.title(f"BIG {N}\n", color=COLOR)
    plt.ylim(0, 1)
    plt.subplots_adjust(top=0.75)

def get_title(predictions, categories=CAT6):
    title = f"Detected emotion: {categories[predictions.argmax()]} \
    - {predictions.max() * 100:.2f}%"
    return title

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
        
        # save the audio file into local disk
        save_audio(file)
        
        path = 'audio1/' + file.filename + '.wav'
        mfccs = get_mfccs(path, model.input_shape[-1])
        mfccs = mfccs.reshape(1, *mfccs.shape)
        pred = model.predict(mfccs)[0]

        # plot1
        pos = pred[3] + pred[5] * .5
        neu = pred[2] + pred[5] * .5 + pred[4] * .5
        neg = pred[0] + pred[1] + pred[4] * .5
        data3 = np.array([pos, neu, neg])
        txt = get_title(data3, CAT3)
        fig = plt.figure(figsize=(5, 5))
        plot_colored_polar(fig, predictions=data3, categories=CAT3, title=txt, colors=COLOR_DICT)
        img = io.BytesIO()
        plt.savefig(img, format = 'png')
        img.seek(0)
        plot_data1 = quote(base64.b64encode(img.read()).decode())


        # plot2
        txt = get_title(pred, CAT6)
        fig2 = plt.figure(figsize=(5, 5))
        plot_colored_polar(fig2, predictions=pred, categories=CAT6, title=txt, colors=COLOR_DICT)
        img = io.BytesIO()
        plt.savefig(img, format = 'png')
        img.seek(0)
        plot_data2 = quote(base64.b64encode(img.read()).decode())

        # gender detection plot
        gmfccs = get_mfccs(path, gmodel.input_shape[-1])
        gmfccs = gmfccs.reshape(1, *gmfccs.shape)
        gpred = gmodel.predict(gmfccs)[0]
        ind = gpred.argmax()
        gdict = [["female", "woman.png"], ["male", "man.png"]]
        txt = "Predicted gender: " + gdict[ind][0]
        img = Image.open("/home/bs1040/Old_PC/University/semester8/Thesis/Project/static/images/" + gdict[ind][1])
        fig4 = plt.figure(figsize=(3, 3))
        fig4.set_facecolor('#d1d1e0')
        plt.title(txt)
        plt.imshow(img)
        plt.axis("off")
        img = io.BytesIO()
        plt.savefig(img, format = 'png')
        img.seek(0)
        plot_data3 = quote(base64.b64encode(img.read()).decode())

        # mfccs plot
        fig = plt.figure(figsize=(10, 2))
        fig.set_facecolor('#d1d1e0')
        plt.title("MFCCs")
        wav, sr = librosa.load(path, sr=44100)
        Xdb = get_melspec(path)[1]
        mfccs = librosa.feature.mfcc(wav, sr=sr)
        librosa.display.specshow(mfccs, sr=sr, x_axis='time')
        plt.gca().axes.get_yaxis().set_visible(False)
        plt.gca().axes.spines["right"].set_visible(False)
        plt.gca().axes.spines["left"].set_visible(False)
        plt.gca().axes.spines["top"].set_visible(False)
        img = io.BytesIO()
        plt.savefig(img, format = 'png')
        img.seek(0)
        mfcc_plot = quote(base64.b64encode(img.read()).decode())

        # Mel-log-spectrogram
        Xdb = get_melspec(path)[1]
        fig2 = plt.figure(figsize=(10, 2))
        fig2.set_facecolor('#d1d1e0')
        plt.title("Mel-log-spectrogram")
        librosa.display.specshow(Xdb, sr=sr, x_axis='time', y_axis='hz')
        plt.gca().axes.get_yaxis().set_visible(False)
        plt.gca().axes.spines["right"].set_visible(False)
        plt.gca().axes.spines["left"].set_visible(False)
        plt.gca().axes.spines["top"].set_visible(False)
        img = io.BytesIO()
        plt.savefig(img, format = 'png')
        img.seek(0)
        spectrogram_plot = quote(base64.b64encode(img.read()).decode())

        file_name = 'thesis/' + str(uuid.uuid4()) + ".mp3"
        #  Upload Cloudinary
        uploadedResponse = upload(file,resource_type = "video",  public_id=file_name )
        if(uploadedResponse):
            db.responses.insert_one({
                'url': uploadedResponse['url'],
                'userId': session['user']['_id'],
                'predict': CAT6[pred.argmax()],
                'createdAt': datetime.now(),
            })
            # response
            response = {
                'resultPlot1': plot_data1,
                'resultPlot2': plot_data2,
                'resultPlot3': plot_data3,
                'mfccsPlot': mfcc_plot,
                'spectrogramPloat': spectrogram_plot,
            }
            return response
        else:
            flash('Image Uploaed Failed')
            return redirect(request.url)

    else:
        flash('You need to login first')
        return render_template('signin.html')
        
    