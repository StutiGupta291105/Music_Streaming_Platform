from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_mysqldb import MySQL
import os
from flask import current_app
from werkzeug.utils import secure_filename
import os

dashboard = Blueprint('dashboard', __name__)
mysql = MySQL()

# Admin Dashboard Route
@dashboard.route('/dashboard/admin')
def admin_dashboard():
    if 'user_id' not in session or session['email'] != 'admin@example.com':
        return redirect(url_for('auth.login'))  # If not logged in as admin, redirect to login

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Users")
    users = cur.fetchall()

    cur.execute("SELECT * FROM Songs")
    songs = cur.fetchall()

    cur.execute("SELECT * FROM Artists")  # Fetch artists here
    artists = cur.fetchall()

    cur.close()

    return render_template('admin_dashboard.html', users=users, songs=songs, artists=artists)

# User Dashboard Route
@dashboard.route('/dashboard/user')
def user_dashboard():
    user_id = session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # If not logged in, redirect to login
    
    query = request.args.get('query', '').lower()


    cur = mysql.connection.cursor()
    user_id = session['user_id']
    cur.execute("SELECT song_id FROM Likes WHERE user_id = %s", (user_id,))
    liked_songs = cur.fetchall()
    liked_song_ids = [song[0] for song in liked_songs]
    if session['email'] == 'admin@example.com':
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()

        if query:
            cur.execute("""
                SELECT s.*, a.artist_name FROM songs s
                LEFT JOIN artists a ON s.artist_id = a.artist_id
                WHERE LOWER(s.song_title) LIKE %s
                   OR LOWER(s.album) LIKE %s
                   OR LOWER(s.genre) LIKE %s
                   OR LOWER(a.artist_name) LIKE %s
            """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
        else:
            cur.execute("""
                SELECT s.*, a.artist_name FROM songs s
                LEFT JOIN artists a ON s.artist_id = a.artist_id
            """)
        songs = cur.fetchall()
        return render_template('admin_dashboard.html', users=users, songs=songs)

    else:
        if query:
            cur.execute("""
                SELECT s.*, a.artist_name FROM songs s
                LEFT JOIN artists a ON s.artist_id = a.artist_id
                WHERE LOWER(s.song_title) LIKE %s
                   OR LOWER(s.album) LIKE %s
                   OR LOWER(s.genre) LIKE %s
                   OR LOWER(a.artist_name) LIKE %s
            """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
        else:
            cur.execute("""
                SELECT s.*, a.artist_name FROM songs s
                LEFT JOIN artists a ON s.artist_id = a.artist_id
            """)
        songs = cur.fetchall()
        cur.execute(""" SELECT s.*, a.artist_name FROM songs s LEFT JOIN artists a ON s.artist_id = a.artist_id WHERE s.song_id IN (%s) """, (','.join(str(id) for id in liked_song_ids),))  # Get liked songs
        playlist_songs = cur.fetchall()
        cur.execute("SELECT * FROM Playlists WHERE user_id = %s", (user_id,))
        playlists = cur.fetchall()
        cur.execute("SELECT * FROM Artists")  # Fetch artists here
        artists = cur.fetchall()

        cur.close()

    return render_template('user_dashboard.html', songs=songs, liked_song_ids=liked_song_ids, playlist_songs=playlist_songs, playlists=playlists, artists=artists)


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Upload Song Route (Only Admin)
@dashboard.route('/upload_songs', methods=['GET', 'POST'])
def upload_songs():
    if 'user_id' not in session or session['email'] != 'admin@example.com':
        return redirect(url_for('auth.login'))
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        title = request.form['title']
        artist_id = request.form['artist_id']  # Now taking artist ID instead of artist name
        album = request.form['album']
        genre = request.form['genre']
        duration = request.form['duration']
        release_date = request.form['release_date']
        file = request.files['file_path']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join('static', 'uploads', filename)
            file_path = save_path.replace("\\", "/")   # Store file path
            file.save(file_path)

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO songs (song_title, artist_id, album, genre, duration, release_date, file_path, image_path) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (title, artist_id, album, genre, duration, release_date, file_path))

            mysql.connection.commit()
            cur.close()

            return redirect(url_for('dashboard.show_dashboard'))

    # Fetch artists for dropdown
    cur.execute("SELECT artist_id, artist_name FROM artists")
    artists = cur.fetchall()
    cur.close()
        

      # Fetch all artists to populate the artist dropdown  

    return render_template('upload_songs.html', artists=artists)  # Render upload song page

@dashboard.route('/add_artist', methods=['GET', 'POST'])
def add_artist():
    # Check if user is logged in and is admin
    if 'user_id' not in session or session['email'] != 'admin@example.com':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        artist_name = request.form['artist_name']
        genre = request.form['genre']
        country = request.form['country']

        # Insert artist into the 'artists' table
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO artists (artist_name, genre, country) VALUES (%s, %s, %s)", 
                    (artist_name, genre, country))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('dashboard.show_dashboard'))  # Redirect to dashboard after adding the artist

    return render_template('add_artist.html')  # Render the form if GET request

@dashboard.route('/dashboard')
def show_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # Redirect to login if not logged in

    cur = mysql.connection.cursor()

    # If the user is admin, show all users and songs
    if session['email'] == 'admin@example.com':
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()

        cur.execute("SELECT * FROM songs")
        songs = cur.fetchall()

        cur.execute("SELECT * FROM artists")
        artists = cur.fetchall()  # ✅ Fetch artists here

        cur.close()
        return render_template('admin_dashboard.html', users=users, songs=songs)

    # If normal user, show only songs
    cur.execute("SELECT s.song_title, a.artist_name, s.album, s.genre, s.duration, s.release_date, s.file_path FROM songs s LEFT JOIN artists a ON s.artist_id = a.artist_id")
    songs = cur.fetchall()
    cur.close()
    return render_template('user_dashboard.html', songs=songs)


@dashboard.route('/delete_song/<int:song_id>', methods=['POST'])
def delete_song(song_id):
    if 'user_id' not in session or session['email'] != 'admin@example.com':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # First get the file path to delete the file from disk
    cur.execute("SELECT file_path FROM songs WHERE song_id = %s", (song_id,))
    result = cur.fetchone()
    if result:
        file_path = result[0]
        if os.path.exists(file_path):
            os.remove(file_path)

    # Then delete from database
    cur.execute("DELETE FROM songs WHERE song_id = %s", (song_id,))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('dashboard.user_dashboard'))

@dashboard.route('/edit_artist/<int:artist_id>', methods=['GET', 'POST'])
def edit_artist(artist_id):
    if 'user_id' not in session or session['email'] != 'admin@example.com':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # If the form is submitted
    if request.method == 'POST':
        artist_name = request.form['artist_name']
        genre = request.form['genre']
        country = request.form['country']

        # Update artist information in the database
        cur.execute("""
            UPDATE artists
            SET artist_name = %s, genre = %s, country = %s
            WHERE artist_id = %s
        """, (artist_name, genre, country, artist_id))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('dashboard.show_dashboard'))

    # If GET request, get the artist's current info to pre-fill the form
    cur.execute("SELECT * FROM artists WHERE artist_id = %s", (artist_id,))
    artist = cur.fetchone()
    cur.close()

    return render_template('edit_artist.html', artist=artist)

@dashboard.route('/delete_artist/<int:artist_id>', methods=['POST'])
def delete_artist(artist_id):
    if 'user_id' not in session or session['email'] != 'admin@example.com':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # Delete the artist from the database
    cur.execute("DELETE FROM artists WHERE artist_id = %s", (artist_id,))
    mysql.connection.commit()

    cur.close()

    return redirect(url_for('dashboard.show_dashboard'))

@dashboard.route('/like_song/<int:song_id>', methods=['POST'])
def like_song(song_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    # Check if already liked
    cur.execute("SELECT * FROM Likes WHERE user_id = %s AND song_id = %s", (user_id, song_id))
    already_liked = cur.fetchone()

    if not already_liked:
        cur.execute("INSERT INTO Likes (user_id, song_id) VALUES (%s, %s)", (user_id, song_id))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('dashboard.user_dashboard'))

@dashboard.route('/playlist')
def user_playlist():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT s.song_id, s.song_title, a.artist_name, s.album, s.genre, s.duration, s.release_date, s.file_path
        FROM Likes l
        JOIN Songs s ON l.song_id = s.song_id
        LEFT JOIN Artists a ON s.artist_id = a.artist_id
        WHERE l.user_id = %s
    """, (user_id,))
    songs = cur.fetchall()
    cur.close()

    return render_template('playlist.html', songs=songs)


@dashboard.route('/unlike_song/<int:song_id>', methods=['POST'])
def unlike_song(song_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # Redirect to login if the user is not logged in

    user_id = session['user_id']

    # Delete the song from the Likes table to "unlike" it
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM Likes WHERE user_id = %s AND song_id = %s", (user_id, song_id))
        mysql.connection.commit()
    except Exception as e:
        print(f"Error unliking song: {e}")
    finally:
        cur.close()

    # Redirect to the user dashboard after unliking the song
    return redirect(url_for('dashboard.user_dashboard'))

# Create Playlist Route
@dashboard.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        playlist_name = request.form['playlist_name']
        user_id = session['user_id']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Playlists (user_id, playlist_name) VALUES (%s, %s)", (user_id, playlist_name))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('dashboard.user_dashboard'))

    return render_template('create_playlist.html')

# Add Song to Playlist Route
@dashboard.route('/add_to_playlist', methods=['POST'])
def add_to_playlist():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    playlist_id = request.form['playlist_id']
    song_id = request.form['song_id']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO Playlist_Songs (playlist_id, song_id) VALUES (%s, %s)", (playlist_id, song_id))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('dashboard.user_dashboard'))


# View Playlists Route
@dashboard.route('/view_playlists')
def view_playlists():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Playlists WHERE user_id = %s", (user_id,))
    playlists = cur.fetchall()

    # Fetch songs for each playlist
    playlists_with_songs = []
    for playlist in playlists:
        cur.execute("""
            SELECT s.song_title, a.artist_name, s.album
            FROM Playlist_Songs ps
            JOIN Songs s ON ps.song_id = s.song_id
            LEFT JOIN Artists a ON s.artist_id = a.artist_id
            WHERE ps.playlist_id = %s
        """, (playlist[0],))
        songs = cur.fetchall()
        playlists_with_songs.append((playlist, songs))

    cur.close()
    return render_template('view_playlists.html', playlists_with_songs=playlists_with_songs)

# Delete Playlist Route
@dashboard.route('/delete_playlist/<int:playlist_id>', methods=['POST'])
def delete_playlist(playlist_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # First delete songs linked to this playlist
    cur.execute("DELETE FROM playlist_songs WHERE playlist_id = %s", (playlist_id,))

    # Now delete the playlist
    cur.execute("DELETE FROM playlists WHERE playlist_id = %s", (playlist_id,))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('dashboard.user_dashboard'))

@dashboard.route('/profile', methods=['GET', 'POST'])
def user_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        new_password = request.form['new_password']
        cur.execute("UPDATE users SET password = %s WHERE id = %s", (new_password, user_id))
        mysql.connection.commit()
        message = "Password updated successfully!"
    else:
        message = None

    cur.execute("SELECT display_name, email FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()

    return render_template('profile.html', user=user, message=message)



# Route for displaying all liked songs
@dashboard.route('/liked_songs', methods=['GET'])
def liked_songs():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()  # Redirect to login if user is not logged in
    
    # Query to fetch the liked songs for the logged-in user
    cur.execute("""
        SELECT s.song_id, s.song_title, s.artist_id, s.album, s.genre, s.duration, s.release_date, s.file_path
        FROM songs s
        INNER JOIN Likes l ON s.song_id = l.song_id
        WHERE l.user_id = %s
    """, (user_id,))

    liked_songs = cur.fetchall()

    # Close the database connection
    cur.close()


    # Render the liked songs page
    return render_template('liked_songs.html', liked_songs=liked_songs)

@dashboard.route('/view_single_playlist', methods=['GET'])
def view_single_playlist():
    playlist_id = request.args.get('playlist_id')

    if not playlist_id:
        return redirect(url_for('dashboard.user_dashboard'))

    cur = mysql.connection.cursor()
    

    # Fetch playlist name
    cur.execute("SELECT playlist_name FROM Playlists WHERE playlist_id = %s", (playlist_id,))
    playlist = cur.fetchone()

    # Fetch songs in the playlist
    cur.execute("""
        SELECT s.song_id, s.song_title, s.album, s.genre, s.duration, s.release_date, s.file_path, a.artist_name
        FROM Songs s
        JOIN Playlist_Songs ps ON s.song_id = ps.song_id
        LEFT JOIN Artists a ON s.artist_id = a.artist_id
        WHERE ps.playlist_id = %s
    """, (playlist_id,))
    songs = cur.fetchall()

    # Fetch liked songs by the user
    cur.execute("SELECT song_id FROM Likes WHERE user_id = %s", (session['user_id'],))
    liked_song_ids = [row[0] for row in cur.fetchall()]

    cur.close()

    return render_template('playlist_songs.html', songs=songs, playlist=playlist, liked_song_ids=liked_song_ids)
