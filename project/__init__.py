from flask import Flask, request, jsonify, g
import os
import mysql.connector
from flask_login import LoginManager
from project.authentication import authentication_bp
from .recipe import recipe_bp
from flask_login import UserMixin
from flask_mail import Mail

# Initialize the login manager
login_manager = LoginManager()
login_manager.login_view = 'authentication.login'

# Initialize mail globally
mail = Mail()

def create_app():
    app = Flask(__name__)

    # Set allowed hosts
    ALLOWED_HOSTS = {'127.0.0.1', 'localhost', '192.168.16.101'}

    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # Initialize the login manager
    login_manager.init_app(app)

    @app.errorhandler(405)
    def methods(error):
        return jsonify({'error': 'Method Not Allowed'}), 405

    @app.before_request
    def before_request():
        g.db = mysql.connector.connect(
            user=os.environ['MYSQL_USER'],
            password=os.environ['MYSQL_PASSWORD'],
            host=os.environ['MYSQL_HOST'],
            database=os.environ['MYSQL_DB']
        )

        get_host = request.remote_addr
        if get_host not in ALLOWED_HOSTS:
            return jsonify({'error': 'Access Denied'}), 403

        raw_path = request.url
        if '//' in raw_path.split('://')[-1]:
            return jsonify({'error': 'Please Enter Valid Url'}), 404

    @app.after_request
    def after_request(response):
        g.db.close()
        return response
    
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
    app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True

    # Initialize mail with the app
    mail.init_app(app)

    # Register blueprints
    app.register_blueprint(authentication_bp, url_prefix='/auth')
    app.register_blueprint(recipe_bp)

    return app

class User(UserMixin):
    def __init__(self, user_id, email, username, password):
        self.id = user_id
        self.email = email
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    cursor = g.db.cursor()
    cursor.execute('SELECT id, email, username, password FROM tbl_users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    if user:
        return User(user[0], user[1], user[2], user[3])
    return None
