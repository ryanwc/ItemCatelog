from oauth2client.client import flow_from_clientsecrets

SECRET_KEY = "super_secret_key"
DEBUG = True
SQLALCHEMY_ECHO = True
G_CLIENT_ID = "446362929824-aoa0sov3apqfqin1njstj6hu078e49ap.apps.googleusercontent.com"
G_OAUTH_FLOW = flow_from_clientsecrets('instance/g_client_secrets.json', scope='')
FB_APP_ID = "1106203452759411"
FB_APP_SECRET = "52a0f9d61955b99954d44a87638877e5"