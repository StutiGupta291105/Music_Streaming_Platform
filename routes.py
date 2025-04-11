from flask import Blueprint, render_template, session, redirect, url_for, request, current_app
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import os

mysql = MySQL()
routes = Blueprint('routes', __name__)

# Dashboard Route
@routes.route('/dashboard')
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
        return render_template('admin_dashboard.html', users=users, songs=songs)

    # If normal user, show only songs
    cur.execute("SELECT * FROM songs")
    songs = cur.fetchall()
    return render_template('user_dashboard.html', songs=songs)

# File Upload Configuration
