from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT']=1
app.config['SECRET_KEY'] = '21a00ee024ebe902cf1848208f5c1a29'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@app.after_request
def add_header(response):
    response.headers['Cache-Control']='no-store, no-cache, must-revalidate, post-check=0,max-age=0'
    response.headers['Pragma']= 'no-cache'
    response.headers['Expires']='-1'
    return response
from mess import routes
