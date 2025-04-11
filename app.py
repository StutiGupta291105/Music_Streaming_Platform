from flask import Flask, render_template, session, redirect, url_for
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_session import Session
import os

from auth.routes import auth
from dashboard.routes import dashboard 
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'stuti123' 
app.config['MYSQL_DB'] = 'music_db'
mysql = MySQL(app)

app.secret_key = "your_secret_key"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
bcrypt = Bcrypt(app)

app.register_blueprint(auth) 
app.register_blueprint(dashboard) 

@app.route('/')
def home():
    return "Flask App with Authentication!" 

if __name__ == '__main__':
    app.run(debug=True)


