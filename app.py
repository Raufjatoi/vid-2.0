from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from pytube import YouTube
import os
from apiclient.discovery import build
from moviepy.editor import VideoFileClip, vfx

app = Flask(__name__, static_folder='static')

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
AUDIO_FOLDER = 'audio'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

# Ensure the folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# YouTube Data API key
API_KEY = 'AIzaSyCkv1WqlKPN6sUajP3OhmYnUvUZ4UOa_zQ'

# Video editing progress
progress = {}

def get_recommendations(max_results=6):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.videos().list(
        part='snippet',
        chart='mostPopular',
        maxResults=max_results
    )
    response = request.execute()
    return response['items']

@app.route('/')
def index():
    videos = get_recommendations()
    return render_template('index.html', videos=videos)

@app.route('/play', methods=['POST'])
def play_video():
    video_url = None
    recommended_videos = []

    if 'video' in request.files:
        file = request.files['video']
        if file.filename == '':
            return redirect(request.url)
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        video_url = url_for('static', filename=f'uploads/{filename}')
    
    elif 'youtube_url' in request.form:
        youtube_url = request.form['youtube_url']
        yt = YouTube(youtube_url)
        video_url = yt.streams.filter(progressive=True, file_extension='mp4').first().url
        recommended_videos = get_recommendations()

    return render_template('player.html', video_url=video_url, recommended_videos=recommended_videos)

@app.route('/generate-more', methods=['POST'])
def generate_more():
    videos = get_recommendations(max_results=100)
    return render_template('index.html', videos=videos)

@app.route('/search', methods=['POST'])
def search_videos():
    search_query = request.form['search_query']
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    youtube_request = youtube.search().list(
        q=search_query,
        part='snippet',
        type='video',
        maxResults=6
    )
    response = youtube_request.execute()
    videos = response['items']
    return render_template('index.html', videos=videos)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/edit')
def edit():
    return render_template('edit.html')

@app.route('/convert')
def convert():
    return render_template('convert.html')

@app.route('/edit-video', methods=['POST'])
def edit_video():
    uploaded_file = request.files['video']
    effect = request.form['effect']

    if uploaded_file.filename == '':
        return redirect(url_for('edit'))

    video_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
    uploaded_file.save(video_path)
    
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], uploaded_file.filename)
    
    clip = VideoFileClip(video_path)
    if effect == 'grayscale':
        clip = clip.fx(vfx.blackwhite)
    elif effect == 'blur':
        clip = clip.fx(vfx.gaussian_blur)
    elif effect == 'speed':
        clip = clip.fx(vfx.speedx, factor=2)
    
    clip.write_videofile(processed_path, logger=None)
    
    return send_from_directory(app.config['PROCESSED_FOLDER'], uploaded_file.filename)

@app.route('/convert-video', methods=['POST'])
def convert_video():
    uploaded_file = request.files['video']
    
    if uploaded_file.filename == '':
        return redirect(url_for('convert'))

    video_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
    uploaded_file.save(video_path)
    
    audio_path = os.path.join(app.config['AUDIO_FOLDER'], f"{os.path.splitext(uploaded_file.filename)[0]}.mp3")
    
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path)
    
    return send_from_directory(app.config['AUDIO_FOLDER'], f"{os.path.splitext(uploaded_file.filename)[0]}.mp3")

if __name__ == '__main__':
    app.run(debug=True)
