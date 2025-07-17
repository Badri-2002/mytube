from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

# Flask app setup
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create upload folder if not exists
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Connect to SQLite DB (creates file if not exists)
conn = sqlite3.connect('mytube.db', check_same_thread=False)
cursor = conn.cursor()

# Create table (only runs once)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        filename TEXT,
        likes INTEGER DEFAULT 0
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER,
        username TEXT,
        comment_text TEXT
    )
''')
conn.commit()
cursor.close()

# Homepage: show videos
@app.route('/')
def homepage():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos")
    videos = []
    for row in cursor.fetchall():
        video_id, title, filename, likes = row
        cursor.execute("SELECT username, comment_text FROM comments WHERE video_id = ?", (video_id,))
        comments = [{"username": c[0], "text": c[1]} for c in cursor.fetchall()]
        videos.append({
            "id": video_id,
            "title": title,
            "filename": filename,
            "likes": likes,
            "comments": comments
        })
    cursor.close()
    return render_template('homepage.html', videos=videos)

# Like a video
@app.route('/like/<int:video_id>', methods=['POST'])
def like_video(video_id):
    cursor = conn.cursor()
    cursor.execute("UPDATE videos SET likes = likes + 1 WHERE id = ?", (video_id,))
    conn.commit()
    cursor.close()
    return redirect(url_for('homepage'))

# Add a comment
@app.route('/comment/<int:video_id>', methods=['POST'])
def comment_video(video_id):
    username = request.form['username']
    comment = request.form['comment']
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comments (video_id, username, comment_text) VALUES (?, ?, ?)",
                   (video_id, username, comment))
    conn.commit()
    cursor.close()
    return redirect(url_for('homepage'))

# Upload a new video
@app.route('/upload', methods=['GET', 'POST'])
def upload_video():
    if request.method == 'POST':
        title = request.form['title']
        video = request.files['video']
        if video.filename != '':
            filename = video.filename
            video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Insert into database
            cursor = conn.cursor()
            cursor.execute("INSERT INTO videos (title, filename) VALUES (?, ?)", (title, filename))
            conn.commit()
            cursor.close()

            return redirect(url_for('homepage'))
    return render_template('upload.html')

# Start the server
if __name__ == '__main__':
    print("✅ Flask app starting...")
    app.run(debug=True, host='127.0.0.1', port=5052)
