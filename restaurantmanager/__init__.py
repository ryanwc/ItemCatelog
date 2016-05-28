from flask import Flask, session as login_session

app = Flask(__name__, instance_relative_config=True)

app.config.from_object('config')
app.config.from_pyfile('config.py')

from .home.home import home_bp
from .user.user import user_bp
from .cuisine.cuisine import cuisine_bp
from .restaurant.restaurant import restaurant_bp
from .api.api import api_bp

app.register_blueprint(home_bp, url_prefix='/home')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(cuisine_bp, url_prefix='/cuisine')
app.register_blueprint(restaurant_bp, url_prefix='/restaurant')
app.register_blueprint(api_bp, url_prefix='/api')
