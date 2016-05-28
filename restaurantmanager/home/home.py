from flask import (Blueprint, render_template, request, redirect, url_for, 
    flash, send_from_directory, session as login_session, make_response)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from oauth2client.client import FlowExchangeError

import json, httplib2, requests, traceback, random, string

import restaurantmanager.DataManager
from restaurantmanager.utils import getClientLoginSession
from restaurantmanager import app

home_bp = Blueprint('home', __name__, 
    template_folder='templates', static_folder='static')

###
### Homepage
###

@app.route('/')
@app.route('/index/')
@app.route('/login/')
def restaurantManagerIndex():
    '''Serve the homepage
    '''
    # create a state token to prevent CSRF
    # store it in the session for later validation
    state = ''.join(random.choice(string.ascii_uppercase + \
        string.ascii_lowercase + string.digits) for x in xrange(32))
    login_session['state'] = state

    client_login_session = getClientLoginSession()

    # for writing all existing db data to .json
    #writeTablesToJSON('initial_data/')

    return render_template("index.html", state=state, 
                           client_login_session=client_login_session)

##
### Login/logout endpoints
###

@app.route('/gconnect', methods=['POST'])
def gconnect():
    '''Ajax enpoint for google sign in authentication
    '''
    # confirm entity with correct 3rd party credentials is same entity 
    # that is trying to login from the current login page's session.
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 
            401)
        response.headers['Content-Type'] = 'application/json'

        return response

    code = request.data

    try:
        # upgrade the authorization code into a credentials object
        # i.e., give google the data (one time code) the entity to be 
        # authenticated supposedly got from google and have google 
        # return credentials if the data is correct
        oauth_flow = config['G_OAUTH_FLOW']
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except:
        traceback.print_exc()
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    # check that the access token from google is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
       % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # if there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

        return response
    
    # verify that the access token is used for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user"), 401)
        response.headers['Content-Type'] = 'application/json'

        return response
    
    # verify that the access token is valid for this app
    if result['issued_to'] != config['G_CLIENT_ID']:
        response = make_response(json.dumps("Token's client ID doesn't match app's ID"), 401)
        response.headers['Content-Type'] = 'application/json'

        return response
        
    # check to see if the google account is already logged into the system
    if ('gplus_id' in login_session and
        login_session['gplus_id'] == gplus_id):
        response = make_response(json.dumps("Current user is already connected."), 200)
        response.headers['Content-Type'] = 'application/json'

        return response
    
    # store relevant credentials
    login_session['g_credentials'] = credentials
    login_session['credentials'] = {'access_token':access_token}
    login_session['gplus_id'] = gplus_id

    # get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt':'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)

    login_session['email'] = data['email']
    login_session['picture'] = data['picture']
    login_session['username'] = data['name']

    setProfile()

    return getSignInAlert()

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    '''Ajax endpoint for facebook sign in authentication
    '''
    # confirm entity with correct 3rd party credentials is same entity 
    # that is trying to login from the current login page's session.
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 
            401)
        response.headers['Content-Type'] = 'application/json'

        return response

    access_token = request.data

    # exchange short-lived client token for long-lived server-side token
    app_id = config['FB_APP_ID']
    app_secret = config['FB_APP_SECRET']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id,app_secret,access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # strip expire tag from access token
    token = result.split("&")[0]

    url = "https://graph.facebook.com/v2.4/me?%s&fields=name,id,email" % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    # facebook uses separate api call to get pic
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data['data']['url']

    # store relevant credentials
    credentials = {'access_token':token}
    login_session['credentials'] = credentials

    setProfile()

    return getSignInAlert()

@app.route('/disconnect', methods=['POST'])
def disconnect():
    '''Logout a user that is currently logged in
    '''
    # only disconnects if valid credentials exist
    if not isLoggedIn():

        response = make_response(json.dumps('No user logged in'), 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    disconnectResult = None

    if 'gplus_id' in login_session:

        disconnectResult = gdisconnect()
    elif 'facebook_id' in login_session:

        disconnectResult = fbdisconnect()

    logoutMessage = ""

    if disconnectResult is not None:
        if disconnectResult['success']:

            logoutMessage += disconnectResult['message']
            logoutMessage += ";  "
        else:

            response = make_response(json.dumps('Failed to revoke '+\
                'third party authorization'), 401)
            response.headers['Content-Type'] = 'application/json'

            return response

    username = login_session['username']

    del login_session['credentials']
    del login_session['user_id']
    del login_session['username']
    del login_session['picture']
    del login_session['email']
    del login_session['picture_serve_type']


    print 'deleted login session'

    logoutMessage += "Logged " + username + \
                     " out of Restaurant Manager"

    return logoutMessage

@app.route('/gdisconnect', methods=['POST'])
def gdisconnect():
    '''Disconnect a user from Google oauth
    '''
    access_token = login_session['credentials']['access_token']
    
    # execute HTTP GET request to revoke current token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    disconnectResult = {'success':False, 
                        'message':'Failed to disconnect from Google'}

    if result['status'] == '200':

        del login_session['g_credentials']
        del login_session['gplus_id']
        disconnectResult['success'] = True
        disconnectResult['message'] = 'Disconnected from Google'

    return disconnectResult

@app.route('/fbdisconnect', methods=['POST'])
def fbdisconnect():
    '''Disconnect a user from Facebook oauth
    '''
    # only disconnects if current user has access token (i.e., is logged in)
    access_token = login_session['credentials']['access_token']
    
    # execute HTTP GET request to revoke current token
    facebook_id = login_session['facebook_id']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    ## I guess the above line never fails?

    del login_session['facebook_id']
    disconnectResult = {'success':True, 
                        'message':'Disconnected from Facebook'}

    return disconnectResult

###
### picture serve endpoint
### (does this belong in another module? utils?)

@app.route(app.config['UPLOAD_FOLDER']+'/<filename>/')
def uploaded_picture(filename):
    '''Serve an uploaded picture
    '''
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename) 
