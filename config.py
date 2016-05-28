import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = APP_ROOT + '/restaurantmanager/pics'
ALLOWED_EXTENSIONS = set(['png','PNG','jpg','JPG','jpeg','JPEG'])
DEBUG = False
SQLALCHEMY_ECHO = False
