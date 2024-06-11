# app.py
from flask import Flask, render_template, request, redirect, url_for
from pytube import YouTube
import os
from apiclient.discovery import build

app = Flask(__name__, static_folder='static')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# YouTube Data API key
API_KEY = 'AIzaSyCkv1WqlKPN6sUajP3OhmYnUvUZ4UOa_zQ'

def get_recommendations(max_results=6):
    # Initialize YouTube Data API client
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    # Fetch recommended videos
    request = youtube.videos().list(
        part='snippet',
        chart='mostPopular',  # You can change this to 'trending' or other options
        maxResults=max_results  # Number of recommended videos to fetch
    )
    response = request.execute()
    return response['items']

@app.route('/')
def index():
    # Get recommended YouTube videos
    videos = get_recommendations()
    return render_template('index.html', videos=videos)

@app.route('/play', methods=['POST'])
def play_video():
    video_url = None
    recommended_videos = []

    if 'video' in request.files:
        # Handle uploaded video
        file = request.files['video']
        if file.filename == '':
            return redirect(request.url)
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        file.save(file_path)
        video_url = url_for('static', filename=f'uploads/{filename}')
    
    elif 'youtube_url' in request.form:
        # Handle YouTube video URL
        youtube_url = request.form['youtube_url']
        yt = YouTube(youtube_url)
        video_title = yt.title
        video_url = yt.streams.filter(progressive=True, file_extension='mp4').first().url
        recommended_videos = get_recommendations()  # Fetch recommended videos for display

    return render_template('player.html', video_url=video_url, recommended_videos=recommended_videos)

@app.route('/generate-more', methods=['POST'])
def generate_more():
    # Get additional recommendations
    videos = get_recommendations(max_results=100)  # Fetch 6 more recommendations
    return render_template('index.html', videos=videos)

@app.route('/search', methods=['POST'])
def search_videos(search_query):
    # Initialize YouTube Data API client
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    # Search for videos
    request = youtube.search().list(
        q=search_query,
        part='snippet',
        type='video',
        maxResults=6  # Number of search results to fetch
    )
    response = request.execute()
    return response['items']

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
