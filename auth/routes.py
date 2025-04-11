from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL

auth = Blueprint('auth', __name__)

bcrypt = Bcrypt()
mysql = MySQL()

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (display_name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('auth.login'))

    return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", [email])
        user = cur.fetchone()

        if user and bcrypt.check_password_hash(user[2], password):  # user[2] is the password hash
            session['user_id'] = user[0]  # Save user ID to session
            session['email'] = user[1]  # Save user email to session
            session['display_name'] = user[3]  # Save display name to session

            if user[1] == 'admin@example.com':  # Admin email check
                return redirect(url_for('dashboard.admin_dashboard'))  # Redirect to admin dashboard
            else:
                return redirect(url_for('dashboard.user_dashboard'))  # Redirect to normal user dashboard

        else:
            return "Invalid credentials, please try again."

    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
