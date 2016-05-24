from flask import Flask, render_template, request, redirect
from flask import url_for, flash, jsonify, send_from_directory
from flask import session as login_session
from flask import make_response
from werkzeug import secure_filename
import requests

import os

import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import traceback

import httplib2

import json

from database_setup import Base, Restaurant, BaseMenuItem, Cuisine
from database_setup import RestaurantMenuItem, User, Picture

import RestaurantManager

from decimal import *

import bleach

import random, string, decimal


###
### Global variables
###

app = Flask(__name__)

# set google client secrets
CLIENT_ID = json.loads(open('client_secrets.json', 
    'r').read())['web']['client_id']

# This is the path to the upload directory
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'pics')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# These are the extentions we allow to be uploaded
ALLOWED_PIC_EXTENSIONS = set(['png','PNG','jpg','JPG','jpeg','JPEG'])


###############################################################################
# Main Server Code
###############################################################################


###
### Login endpoints
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
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
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
    if result['issued_to'] != CLIENT_ID:
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
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id,app_secret,access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # strip expire tag from access token
    token = result.split("&")[0]

    url = "https://graph.facebook.com/v2.4/me?%s&fields=name,id,email" % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

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
    if 'credentials' not in login_session:
        if 'access_token' not in login_session['credentials']:

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
### JSON endpoints
###

@app.route('/cuisines/JSON/')
def cuisinesJSON():
    cuisines = RestaurantManager.getCuisines()

    return jsonify(Cuisines=[i.serialize for i in cuisines])

@app.route('/cuisines/<int:cuisine_id>/JSON/')
def cuisineJSON(cuisine_id):
    cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)
    baseMenuItems = RestaurantManager.\
                    getBaseMenuItems(cuisine_id=cuisine_id)
    restaurants = RestaurantManager.getRestaurants(cuisine_id=cuisine_id)
    restaurantMenuItems = RestaurantManager.\
                          getRestaurantMenuItems(cuisine_id=cuisine_id)

    return jsonify(Cuisine=cuisine.serialize,
                   BaseMenuItems=[i.serialize for i in baseMenuItems],
                   Restaurants=[i.serialize for i in restaurants],
                   RestaurantMenuItems=[i.serialize for i in restaurantMenuItems])

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/JSON/')
def baseMenuItemJSON(cuisine_id, baseMenuItem_id):
    baseMenuItem = RestaurantManager.\
        getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)
    restaurantMenuItems = RestaurantManager.\
                          getRestaurantMenuItems(baseMenuItem_id=baseMenuItem_id)

    return jsonify(BaseMenuItem=baseMenuItem.serialize,
                   RestaurantMenuItems=[i.serialize for i in restaurantMenuItems])

@app.route('/baseMenuItems/JSON/')
def baseMenuItemsJSON():

    baseMenuItems = RestaurantManager.getBaseMenuItems()

    return jsonify(BaseMenuItems=[i.serialize for i in baseMenuItems])

@app.route('/restaurants/JSON/')
def restaurantsJSON():
    restaurants = RestaurantManager.getRestaurants()

    return jsonify(Restaurants=[i.serialize for i in restaurants])

@app.route('/restaurants/<int:restaurant_id>/JSON/')
def restaurantJSON(restaurant_id):
    restaurant = RestaurantManager.getRestaurant(restaurant_id)

    restaurantMenuItems = RestaurantManager.\
        getRestaurantMenuItems(restaurant_id=restaurant_id)

    return jsonify(Restaurant=restaurant.serialize,
                   RestaurantMenuItems=[i.serialize for i in restaurantMenuItems])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/JSON/')
def restaurantMenuItemJSON(restaurant_id, restaurantMenuItem_id):
    restaurantMenuItem = RestaurantManager.\
        getRestaurantMenuItem(restaurantMenuItem_id)

    return jsonify(RestaurantMenuItem=restaurantMenuItem.serialize)


###
### Other endpoints
###

@app.route(app.config['UPLOAD_FOLDER']+'/<filename>/')
def uploaded_picture(filename):
    '''Serving an uploaded picture
    '''
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename) 


###
### HTML endpoints
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

    return render_template("index.html", state=state, 
                           client_login_session=client_login_session)

@app.route('/cuisines/')
def cuisines():
    ''' Display all cuisines
    '''
    cuisines = RestaurantManager.getCuisines()

    client_login_session = getClientLoginSession()

    return render_template("Cuisines.html", cuisines=cuisines,
                           client_login_session=client_login_session)

@app.route('/cuisines/add/', methods=['GET', 'POST'])
def addCuisine():
    '''Serve form for adding a cuisine to the database
    '''
    if not isLoggedIn():

        flash("You must log in to add a cuisine")
        return redirect(url_for('restaurantManagerIndex'))

    client_login_session = getClientLoginSession()

    if request.method == 'POST':

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        name = validateUserInput(request.form['name'],
            'name', 'create', 'cuisine', maxlength=80, 
            required=True, unique=True)

        if name is None:
            return redirect(url_for('cuisines'))

        RestaurantManager.addCuisine(name)

        flash("Added cuisine '" + name + "' to the database!")

        return redirect(url_for('cuisines'))
    else:

        return render_template('AddCuisine.html',
                               hiddenToken=login_session['state'],
                               client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/')
def cuisine(cuisine_id):
    '''Serve cuisine info page
    '''
    cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)
    restaurants = RestaurantManager.\
                  getRestaurants(cuisine_id=cuisine_id)
    baseMenuItems = RestaurantManager.\
                    getBaseMenuItems(cuisine_id=cuisine_id)
    restaurantMenuItems = RestaurantManager.\
        getRestaurantMenuItems(cuisine_id=cuisine_id)
    sectionedBaseMenuItems = RestaurantManager.\
                             getBaseMenuItems(cuisine_id=cuisine_id,
                                              byMenuSection=True)

    client_login_session = getClientLoginSession()

    # get restaurants labeled with user or non-user
    restaurantDicts = {}
    for restaurant in restaurants:
        restaurantDict = {}
        restaurantDict = {'restaurant': restaurant}

        if (isLoggedIn() and 
            restaurant.user_id == login_session['user_id']):
            restaurantDict['ownership'] = 'user'
        else:
            restaurantDict['ownership'] = 'non-user'

        restaurantDicts[restaurant.id] = restaurantDict

    # get the base items with their children 
    # in format that plays nice with jinja
    # and labels things user or non-user
    # and also calculate some data about the items
    mostExpensiveBaseMenuItem = RestaurantManager.\
    getBaseMenuItem(baseMenuItem_id=-1)

    mostExpensiveRestaurantMenuItem = RestaurantManager.\
        getBaseMenuItem(baseMenuItem_id=-1)

    sectionedBaseItemsWithChildren = {}

    for section, baseItemList in sectionedBaseMenuItems.iteritems():

        sectionedBaseItemsWithChildren[section] = {}

        for baseItem in baseItemList:

            baseItemID = baseItem.id

            if baseItem.price > mostExpensiveBaseMenuItem.price:
                mostExpensiveBaseMenuItem = baseItem

            childrenItems = RestaurantManager.\
                getRestaurantMenuItems(baseMenuItem_id=baseItem.id)
            children = {}

            for item in childrenItems:

                if item.price > mostExpensiveRestaurantMenuItem.price:
                    mostExpensiveRestaurantMenuItem = item

                itemRestaurant = RestaurantManager.\
                                 getRestaurant(item.restaurant_id)
                itemUserID = itemRestaurant.user_id
                child = {}
                child['item'] = item

                if (isLoggedIn() and
                    itemUserID == login_session['user_id']):
                    child['ownership'] = 'user'
                else:
                    child['ownership'] = 'non-user'

                children[item.id] = child

            itemWithChildren = {'item':baseItem, 'children':children}
            sectionedBaseItemsWithChildren[section][baseItem.id] = \
                itemWithChildren

    # this means there were no items, so display N/A
    if mostExpensiveRestaurantMenuItem.id == -1:
        mostExpensiveRestaurantMenuItem.name = "N/A"
        mostExpensiveRestaurantMenuItem.price = "N/A"
        mostExpensiveRestaurantMenuItem.restaurant_id = "N/A"
    else:
        # display nicely
        mostExpensiveRestaurantMenuItem.price = \
            Decimal(mostExpensiveRestaurantMenuItem.price).\
            quantize(Decimal('0.01'))

    if mostExpensiveBaseMenuItem.id == -1:
        mostExpensiveBaseMenuItem.name = "N/A"
        mostExpensiveBaseMenuItem.price = "N/A"
    else:
        mostExpensiveBaseMenuItem.price = \
            Decimal(mostExpensiveBaseMenuItem.price).\
            quantize(Decimal('0.01'))

    return render_template("Cuisine.html",
        cuisine=cuisine,
        mostExpensiveBaseMenuItem=mostExpensiveBaseMenuItem,
        mostExpensiveRestaurantMenuItem=mostExpensiveRestaurantMenuItem,
        restaurantDicts=restaurantDicts,
        sectionedBaseItemsWithChildren=sectionedBaseItemsWithChildren,
        client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/edit/', methods=['GET', 'POST'])
def editCuisine(cuisine_id):
    '''Serve form to edit a cuisine
    '''
    if not isLoggedIn():

        flash("You must log in to edit a cuisine")
        return redirect(url_for('restaurantManagerIndex'))
    
    client_login_session = getClientLoginSession()

    cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)

    if request.method == 'POST':

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        oldName = cuisine.name

        newName = validateUserInput(request.form['name'],
            'name', 'edit', 'cuisine', maxlength=80, unique=True, 
            oldName=oldName, tableName='Cuisine')

        RestaurantManager.editCuisine(cuisine_id, newName=newName)
        
        if newName is not None:
            
            flash("Changed cuisine's name from '" + oldName +\
                "' to '" + newName + "'")

        return redirect(url_for('cuisine',
                                cuisine_id=cuisine_id))
    else:
        return render_template("EditCuisine.html",
                               cuisine=cuisine,
                               hiddenToken=login_session['state'],
                               client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/delete/', methods=['GET', 'POST'])
def deleteCuisine(cuisine_id):
    '''Serve form to delete a cuisine
    '''
    if not isLoggedIn():

        flash("You must log in to delete a cuisine")
        return redirect(url_for('restaurantManagerIndex'))
    
    client_login_session = getClientLoginSession()

    cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)

    if request.method == 'POST':

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        # all of this is for flash messaging
        cuisineName = cuisine.name
        cuisineID = cuisine.id
        restaurantMenuItems = RestaurantManager.\
                              getRestaurantMenuItems(cuisine_id=cuisine_id)
        numItemsReassigned = len(restaurantMenuItems)
        restaurants = RestaurantManager.\
                      getRestaurants(cuisine_id=cuisine_id)
        numRestaurantsReassigned = len(restaurants)
        baseMenuItems = RestaurantManager.\
                        getBaseMenuItems(cuisine_id=cuisine_id)
        numItemsDeleted = len(baseMenuItems)
        itemBaseForNoCuisine = RestaurantManager.\
            getBaseMenuItem(baseMenuItem_id=-1)

        # here is the logic
        restaurantBaseForNoCuisine = RestaurantManager.\
                                     getCuisine(cuisine_id=-1)

        RestaurantManager.deleteCuisine(cuisine_id)

        flash("reassigned " + str(numItemsReassigned) + \
            " restaurant menu items' base item to '" + \
            itemBaseForNoCuisine.name + "'")

        flash("reassigned " + str(numRestaurantsReassigned) + \
            " restaurants' cuisine to '" + \
            restaurantBaseForNoCuisine.name + "'")

        flash("deleted " + str(numItemsDeleted) + \
            " base menu items from the database")

        flash("deleted cuisine " + str(cuisineID) + " (" + \
            cuisineName + ") from the database")

        return redirect(url_for('cuisines'))
    else:
        return render_template("DeleteCuisine.html",
                               cuisine=cuisine,
                               hiddenToken=login_session['state'],
                               client_login_session=client_login_session)

@app.route('/restaurants/')
def restaurants():
    # set login HTML
    user_id = -99
    intLoginStatus = 0
    displayNoneIfLoggedIn = ""
    loginStatusMessage = "Not logged in"

    if isLoggedIn():

        user_id = login_session['user_id']
        displayNoneIfLoggedIn = "none"
        loginStatusMessage = "Logged in as " + login_session['username']
        # passed to javascript function
        intLoginStatus = 1

    cuisines = RestaurantManager.getCuisines()

    numRestaurants = 0
    # get restaurants labeled with user or non-user
    # sectioned by cuisine
    cuisineToRestaurantsDict = {}
    for cuisine in cuisines:

        cuisineToRestaurantsDict[cuisine.id] = {}
        cuisineToRestaurantsDict[cuisine.id]['cuisine'] = cuisine
        restaurants = RestaurantManager.\
                      getRestaurants(cuisine_id=cuisine.id)
        restaurantDicts = {}

        for restaurant in restaurants:

            numRestaurants = numRestaurants+1
            restaurantDict = {}
            restaurantDict['restaurant'] = restaurant
                      
            if (isLoggedIn() and
                restaurant.user_id == login_session['user_id']):

                restaurantDict['ownership'] = 'user'
            else:

                restaurantDict['ownership'] = 'non-user'

            restaurantDicts[restaurant.id] = restaurantDict

        cuisineToRestaurantsDict[cuisine.id]['restaurants'] = \
            restaurantDicts
    
    return render_template("Restaurants.html",
                    cuisineToRestaurantsDict=cuisineToRestaurantsDict,
                    numRestaurants=numRestaurants,
                    intLoginStatus=intLoginStatus,
                    displayNoneIfLoggedIn=displayNoneIfLoggedIn,
                    loginStatusMessage=loginStatusMessage,
                    user_id=user_id)

@app.route('/restaurants/add/', methods=['GET','POST'])
def addRestaurant():
    # set login HTML
    user_id = -99
    intLoginStatus = 0
    displayNoneIfLoggedIn = ""
    loginStatusMessage = "Not logged in"

    if isLoggedIn():

        user_id = login_session['user_id']
        displayNoneIfLoggedIn = "none"
        loginStatusMessage = "Logged in as " + login_session['username']
        # passed to javascript function
        intLoginStatus = 1
        
    else:

        flash("You must log in to add a restaurant")
        return redirect(url_for('restaurantManagerIndex'))

    if request.method == 'POST':

        if request.form['hiddenToken'] != login_session['state']:
            # not same entity that first came to login page
            # possible CSRF attack
            flash("An unknown error occurred.  Try signing out"+\
                ", signing back in, and repeating the operation.")

            return redirect(url_for('restaurantManagerIndex'))

        if not request.form['cuisineID']:

            flash("Did not add a restaurant; You did not provide "+\
                "a cuisine type.")
            return redirect(url_for('restaurants'))

        if not request.form['name']:

            flash("Did not add restaurant; you did not provide a name")
            return redirect(url_for('restaurants'))                

        name = bleach.clean(request.form['name'])

        if len(name) > 80:

            flash("Did not add restaurant; name too long")
            return redirect(url_for('restaurants'))    

        cuisine_id = request.form['cuisineID']

        cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)

        if request.files['pictureFile']:
            picFile = request.files['pictureFile']

            if allowed_pic(picFile.filename):
                # this name will be overwritten.
                # can't provide proper name now because 
                # don't have restaurant_id
                picFile.filename = secure_filename(picFile.filename)
                picture_id = RestaurantManager.\
                    addPicture(text=picFile.filename,
                        serve_type='upload')
            else:

                flash("Did not add restaurant; the uploaded pic was "+\
                    "not .png, .jpeg, or .jpg.")
                return redirect(url_for('restaurants'))   
        elif request.form['pictureLink']:

            pictureLink = bleach.clean(request.form['pictureLink'])

            if len(pictureLink) > 300:

                flash("Did not add resaurant; link was too long")
                return redirect(url_for('restaurants'))                  
            
            # print str(len(pictureLink))
            # print pictureLink[:7]
            if (len(pictureLink) < 7 or 
                (len(pictureLink) == 8 and 
                 pictureLink[:7] != 'http://') or
                (len(pictureLink) == 9 and 
                 pictureLink[:8] != 'https://') or
                (pictureLink[:7] != 'http://' and
                 pictureLink[:8] != 'https://')):

                flash("Did not add resaurant; the link was not a url")
                return redirect(url_for('restaurants'))  

            picture_id = RestaurantManager.addPicture(text=pictureLink, 
                                                      serve_type='link')
        else:
            
            flash("Did not add restaurant; you must provide a "+\
                    "picture.")
            return redirect(url_for('restaurants'))

        restaurant_id = RestaurantManager.addRestaurant(
                            name=name,
                            cuisine_id=cuisine.id,
                            user_id=login_session['user_id'],
                            picture_id=picture_id
                        )

        # if pic was uploaded, save actual file for serving
        # set the appropriate name in the database
        if picFile:
            picfilename = 'restaurant' + str(restaurant_id)
            picFile.save(os.path.join(app.config['UPLOAD_FOLDER'], \
                picfilename))
            RestaurantManager.editPicture(picture_id=picture_id,
                                          newText=picfilename)

        RestaurantManager.populateMenuWithBaseItems(restaurant_id)

        flash("restaurant '" + name + "' added to the database!")

        return redirect(url_for('restaurants'))
    else:

        cuisines = RestaurantManager.getCuisines()
        return render_template('AddRestaurant.html', 
                                cuisines=cuisines,
                                hiddenToken=login_session['state'],
                                intLoginStatus=intLoginStatus,
                                displayNoneIfLoggedIn=displayNoneIfLoggedIn,
                                loginStatusMessage=loginStatusMessage,
                                user_id=user_id)

@app.route('/restaurants/<int:restaurant_id>/')
def restaurant(restaurant_id):
    # set login HTML
    user_id = -99
    intLoginStatus = 0
    displayNoneIfLoggedIn = ""
    loginStatusMessage = "Not logged in"

    if isLoggedIn():

        user_id = login_session['user_id']
        displayNoneIfLoggedIn = "none"
        loginStatusMessage = "Logged in as " + login_session['username']
        # passed to javascript function
        intLoginStatus = 1

    restaurant = RestaurantManager.getRestaurant(restaurant_id)
    owner = RestaurantManager.getUser(restaurant.user_id)
    restaurantMenuItems = RestaurantManager.\
                          getRestaurantMenuItems(restaurant_id=restaurant_id)
    cuisine = RestaurantManager.getCuisine(cuisine_id=restaurant.cuisine_id)

    picture = RestaurantManager.getPicture(restaurant.picture_id)

    numMenuItems = len(restaurantMenuItems)

    if numMenuItems > 0:
        mostExpensiveItem = restaurantMenuItems[0]
        for item in restaurantMenuItems:
            if item.price > mostExpensiveItem.price:
                mostExpensiveItem = item
                mostExpensiveItem.price = Decimal(mostExpensiveItem.price).quantize(Decimal('0.01'))
        mostExpensiveItem.price = Decimal(mostExpensiveItem.price).quantize(Decimal('0.01'))
    else:
        mostExpensiveItem = RestaurantManager.\
                            getBaseMenuItem(baseMenuItem_id=-1)
        mostExpensiveItem.name = 'N/A'
        mostExpensiveItem.price = 'N/A'

    return render_template('Restaurant.html', 
                           restaurant=restaurant, 
                           numMenuItems=numMenuItems,
                           mostExpensiveItem=mostExpensiveItem,
                           cuisine=cuisine,
                           picture=picture,
                           intLoginStatus=intLoginStatus,
                           loginStatusMessage=loginStatusMessage,
                           displayNoneIfLoggedIn=displayNoneIfLoggedIn,
                           user_id=user_id,
                           owner=owner)

@app.route('/restaurants/<int:restaurant_id>/edit/',
           methods=['GET','POST'])
def editRestaurant(restaurant_id):
    restaurant = RestaurantManager.getRestaurant(restaurant_id)

    # set login HTML and check permissions
    user_id = -99
    intLoginStatus = 0
    displayNoneIfLoggedIn = ""
    loginStatusMessage = "Not logged in"

    if isLoggedIn():

        displayNoneIfLoggedIn = "none"
        loginStatusMessage = "Logged in as " + login_session['username']
        # passed to javascript function
        intLoginStatus = 1
        user_id = login_session['user_id']
        
        if restaurant.user_id != login_session['user_id']:

            flash("You do not have permission to edit this restaurant")
            return redirect(url_for('restaurant',
                restaurant_id=restaurant.id))
    else:

        flash("You must log in to edit a restaurant")
        return redirect(url_for('restaurantManagerIndex'))

    restaurant = RestaurantManager.getRestaurant(restaurant_id)
    cuisines = RestaurantManager.getCuisines()
    picture = RestaurantManager.getPicture(restaurant.picture_id)
    
    if request.method == 'POST':

        if request.form['hiddenToken'] != login_session['state']:
            # not same entity that first came to login page
            # possible CSRF attack
            flash("An unknown error occurred.  Try signing out"+\
                ", signing back in, and repeating the operation.")

            return redirect(url_for('restaurantManagerIndex'))

        oldName = restaurant.name
        oldCuisine = RestaurantManager.\
                     getCuisine(cuisine_id=restaurant.cuisine_id)
        newName = None
        newCuisine = None
        newCuisineID = None
        
        if request.form['name']:
            newName = bleach.clean(request.form['name'])

            if len(newName) > 100:
                newName = None
                flash("Did not change name; it was too long")
            
        if request.form['cuisineID'] != "-1":
            newCuisineID = request.form['cuisineID']
            newCuisine = RestaurantManager.\
                         getCuisine(cuisine_id=newCuisineID)

        if request.form['pictureLink'] or request.files['pictureFile']:
            newText = None
            newServe_Type = None

            if request.files['pictureFile']: 
                # user uploaded a file
                picFile = request.files['pictureFile']

                if allowed_pic(picFile.filename):
                    # overwrites pic for restaurant if already there
                    newText = 'restaurant' + str(restaurant.id)
                    picFile.save(os.path.join(app.\
                        config['UPLOAD_FOLDER'], newText))
                else:

                    flash("Did not edit pic; uploaded pic was not "+\
                        ".png, .jpeg, or .jpg.  Did not change picture.")

                if picture.serve_type == 'link':

                    newServe_Type = 'upload'
            else:
                # user gave a link
                newText = bleach.clean(request.form['pictureLink'])

                if len(newText) > 300:

                    newText = None
                    flash("Did not edit pic; link too long")
                elif (len(pictureLink) < 7 or 
                      (len(pictureLink) == 8 and 
                       pictureLink[:7] != 'http://') or
                      (len(pictureLink) == 9 and 
                       pictureLink[:8] != 'https://') or
                      (pictureLink[:7] != 'http://' and
                       pictureLink[:8] != 'https://')):

                    newText = None
                    flash("Did not edit pic; the link was not a url")
                elif picture.serve_type == 'upload':
                    # change serve type and delete old, uploaded pic
                    newServe_Type = 'link'
                    relPath = 'pics/'+picture.text
                    os.remove(relPath)
            
            RestaurantManager.editPicture(restaurant.picture_id,
                                          newText=newText,
                                          newServe_Type=newServe_Type)

            if (newText is not None or newServe_Type is not None):
                flash("updated " + restaurant.name + "'s picture!")

        # we edited the pic directly, no need to include here
        RestaurantManager.editRestaurant(restaurant.id,
            newName=newName, newCuisine_id=newCuisineID)

        restaurant = RestaurantManager.getRestaurant(restaurant_id)

        if newName is not None:
            flash("changed " + restaurant.name + "'s (ID " + \
                str(restaurant.id) + ") name from '" + oldName + \
                "' to '" + newName + "'")

        if newCuisine is not None:
            flash("changed " + restaurant.name + "'s (ID " + \
                str(restaurant.id) + ") cuisine from '"+ \
                oldCuisine.name + "' to '" + newCuisine.name + "'")
        
        return redirect(url_for('restaurant',
                                restaurant_id=restaurant_id))
    else:

        return render_template('EditRestaurant.html',
                               restaurant=restaurant,
                               cuisines=cuisines,
                               hiddenToken=login_session['state'],
                               picture=picture,
                               intLoginStatus=intLoginStatus,
                               displayNoneIfLoggedIn=displayNoneIfLoggedIn,
                               loginStatusMessage=loginStatusMessage,
                               user_id=user_id)

@app.route('/restaurants/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    restaurant = RestaurantManager.getRestaurant(restaurant_id)

    # set login HTML
    intLoginStatus = 0
    displayNoneIfLoggedIn = ""
    loginStatusMessage = "Not logged in"
    user_id = -99

    if isLoggedIn():

        displayNoneIfLoggedIn = "none"
        loginStatusMessage = "Logged in as " + login_session['username']
        # passed to javascript function
        intLoginStatus = 1
        user_id = login_session['user_id']

        if restaurant.user_id != login_session['user_id']:

            flash("You do not have permission to delete this restaurant")
            return redirect(url_for('restaurants',
                restaurant_id=restaurant.id))

    else:
        
        flash("You must log in to delete a restaurant")
        return redirect(url_for('restaurantManagerIndex'))

    if request.method == 'POST':

        if request.form['hiddenToken'] != login_session['state']:
            # not same entity that first came to login page
            # possible CSRF attack
            flash("An unknown error occurred.  Try signing out"+\
                ", signing back in, and repeating the operation.")

            return redirect(url_for('restaurantManagerIndex'))

        restaurantMenuItems = RestaurantManager.\
                              getRestaurantMenuItems(restaurant_id=restaurant_id)

        RestaurantManager.deleteRestaurant(restaurant_id)

        flash("deleted " + str(len(restaurantMenuItems)) + \
            " restaurant menu items from the database")

        flash("deleted restaurant " + str(restaurant.id) + " (" + \
            restaurant.name + ") from the database")
        
        return redirect(url_for('restaurants'))
    else:   
        
        return render_template('DeleteRestaurant.html',
                               restaurant=restaurant,
                               hiddenToken=login_session['state'],
                               intLoginStatus=intLoginStatus,
                               loginStatusMessage=loginStatusMessage,
                               displayNoneIfLoggedIn=displayNoneIfLoggedIn,
                               user_id=user_id)

@app.route('/cuisines/<int:cuisine_id>/add/', methods=['GET','POST'])
def addBaseMenuItem(cuisine_id):
    '''Serve form to add a base menu item
    '''
    if not isLoggedIn():

        flash("You must log in to add a base menu item")
        return redirect(url_for('restaurantManagerIndex'))
    
    client_login_session = getClientLoginSession()

    cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)
    menuSections = RestaurantManager.getMenuSections()

    if request.method == 'POST':

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        name = validateUserInput(request.form['name'],
            'name', 'create', 'base menu item', maxlength=80, 
            required=True, unique=True, tableName='BaseMenuItem')

        if name is None:
            return redirect(url_for('cuisine', cuisine_id=cuisine.id))

        description = \
            validateUserInput(request.form['description'],
                'description', 'create', 'base menu item',
                maxlength=250, required=True)

        if description is None:
            return redirect(url_for('cuisine', cuisine_id=cuisine.id))

        price = validateUserInput(request.form['price'],
            'price', 'create', 'base menu item', maxlength=20,
            required=True, priceFormat=True)

        if price is None:
            return redirect(url_for('cuisine', cuisine_id=cuisine.id))

        # need to validate 'select' input?
        # seems like it can't be None or malicious
        menuSection_id = request.form['menuSection']

        providedPic = validateUserPicture('create',
            file=request.files['pictureFile'],
            link=request.form['pictureLink'],
            maxlength=300, required=True)

        if providedPic is None:
            return redirect(url_for('cuisine', cuisine_id=cuisine.id))
        
        picture_id = RestaurantManager.addPicture(text=providedPic['text'], 
            serve_type=providedPic['serve_type'])

        baseMenuItem_id = RestaurantManager.\
            addBaseMenuItem(name, cuisine_id, description=description, 
            price=price, menuSection_id=menuSection_id, 
            picture_id=picture_id)

        # if pic was uploaded, now that item was created, 
        # save actual file for serving and set the name in the database
        if providedPic['serve_type'] == 'upload':
            picfilename = 'baseMenuItem' + str(baseMenuItem_id)
            request.files['pictureFile'].save(os.path.\
                join(app.config['UPLOAD_FOLDER'], picfilename))
            RestaurantManager.editPicture(picture_id=picture_id,
                                          newText=picfilename)

        flash("added '" + name + "' to " + cuisine.name + \
            "'s base menu")

        return redirect(url_for('cuisine', cuisine_id=cuisine.id))
    else:
        return render_template('AddBaseMenuItem.html',
                            cuisine=cuisine,
                            menuSections=menuSections,
                            hiddenToken=login_session['state'],
                            client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/')
def baseMenuItem(cuisine_id, baseMenuItem_id):
    '''Serve a base menu item
    '''
    client_login_session = getClientLoginSession()

    baseMenuItem = RestaurantManager.\
        getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)
    baseMenuItem.price = Decimal(baseMenuItem.price).\
        quantize(Decimal('0.01'))
    cuisine = RestaurantManager.\
        getCuisine(cuisine_id=baseMenuItem.cuisine_id)
    restaurantMenuItems = RestaurantManager.\
        getRestaurantMenuItems(baseMenuItem_id=baseMenuItem.id)
    picture = RestaurantManager.getPicture(baseMenuItem.picture_id)
    menuSection = RestaurantManager.\
        getMenuSection(menuSection_id=baseMenuItem.menuSection_id)
    timesOrdered = 0

    return render_template("BaseMenuItem.html",
                            baseMenuItem=baseMenuItem,
                            restaurantMenuItems=restaurantMenuItems,
                            cuisine=cuisine,
                            timesOrdered=timesOrdered,
                            picture=picture,
                            menuSection=menuSection,
                            client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/edit/',
           methods=['POST','GET'])
def editBaseMenuItem(cuisine_id, baseMenuItem_id):
    '''Serve form to edit a base menu item
    '''
    if not isLoggedIn():

        flash("You must log in to add a base menu item")
        return redirect(url_for('restaurantManagerIndex'))
    
    client_login_session = getClientLoginSession()

    baseMenuItem = RestaurantManager.\
                   getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)
    cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)

    baseMenuItem.price = Decimal(baseMenuItem.price).quantize(Decimal('0.01'))

    picture = RestaurantManager.getPicture(baseMenuItem.picture_id)

    if request.method == 'POST':

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        oldName = baseMenuItem.name
        oldDescription = baseMenuItem.description
        oldPrice = baseMenuItem.price
        oldPicture = picture
        
        newName = validateUserInput(request.form['name'], 'name', 
            'edit', 'base menu item', unique=True, oldInput=oldName)
            
        newDescription = validateUserInput(request.form['description'],
            'description', 'edit', 'base menu item', oldInput=oldDescription)

        newPrice = validateUserInput(request.form['price'], 'price',
            'edit', 'base menu item', priceFormat=True, oldInput=oldPrice)

        providedPic = validateUserPicture('edit',
            file=request.files['pictureFile'],
            link=request.form['pictureLink'], maxlength=300)

        if providedPic is not None:
            #edit the pic
            RestaurantManager.editPicture(baseMenuItem.picture_id,
                newText=providedPic['text'], 
                newServe_Type=providedPic['serve_type'])

            flash("updated base menu item picture")

            # delete the old pic if it was an upload and new is a link
            if (providedPic['serve_type'] == 'link' and
                oldPicture.serve_type == 'upload'):
            
                relPath = 'pics/'+oldPicture.text
                os.remove(relPath)
                flash("deleted old uploaded pic")

        # we edited the pic directly, no need to include here
        RestaurantManager.editBaseMenuItem(baseMenuItem.id,
            newName=newName, newDescription=newDescription, 
            newPrice=newPrice)

        # if pic was uploaded, now that item was created, 
        # save actual file for serving and set the name in the database
        if providedPic['serve_type'] == 'upload':
            picfilename = 'baseMenuItem' + str(baseMenuItem_id)
            request.files['pictureFile'].save(os.path.\
                join(app.config['UPLOAD_FOLDER'], picfilename))
            RestaurantManager.editPicture(picture_id=oldPicture.id,
                                          newText=picfilename)

        if newName is not None:
            flash("changed name from '"+oldName+"' to '"+newName+"'")

        if newDescription is not None:
            flash("changed description from '"+ oldDescription + "' to '" + \
                newDescription + "'")

        if newPrice is not None:
            flash("changed price from '" + str(oldPrice) + "' to '" + \
                str(newPrice) + "'")

        return redirect(url_for('baseMenuItem',
                                cuisine_id=cuisine_id,
                                baseMenuItem_id=baseMenuItem_id))
    else:
        return render_template("EditBaseMenuItem.html",
                               baseMenuItem=baseMenuItem,
                               cuisine=cuisine,
                               hiddenToken=login_session['state'],
                               picture=picture,
                               client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/delete/',
           methods=['GET','POST'])
def deleteBaseMenuItem(cuisine_id, baseMenuItem_id):
    '''Serve form to delete a base menu item
    '''
    if not isLoggedIn():

        flash("You must log in to add a base menu item")
        return redirect(url_for('restaurantManagerIndex'))
    
    client_login_session = getClientLoginSession()

    baseMenuItem = RestaurantManager.\
                   getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)

    if request.method == 'POST':

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)
        restaurantMenuItems = RestaurantManager.\
            getRestaurantMenuItems(baseMenuItem_id=baseMenuItem_id)
        baseForNoCuisine = RestaurantManager.\
            getBaseMenuItem(baseMenuItem_id=-1)

        RestaurantManager.deleteBaseMenuItem(baseMenuItem_id=baseMenuItem_id)

        flash("reassigned " + str(len(restaurantMenuItems)) + \
            " restaurant menu items' base to '" +\
            baseForNoCuisine.name + "'")
        flash("deleted " + baseMenuItem.name + " from " +\
            cuisine.name + "'s base menu and from the database")

        return redirect(url_for('cuisine',cuisine_id=cuisine_id))
    else:

        return render_template("DeleteBaseMenuItem.html",
                            baseMenuItem=baseMenuItem,
                            cuisine_id=cuisine_id,
                            hiddenToken=login_session['state'],
                            client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/menu/')
def restaurantMenu(restaurant_id):
    '''Serve a restaurant's menu
    '''
    restaurant = RestaurantManager.getRestaurant(restaurant_id)

    sectionedItems = RestaurantManager.\
                     getRestaurantMenuItems(restaurant_id=restaurant_id,
                                            byMenuSection=True)

    for menuSection, items in sectionedItems.iteritems():
        for item in items:
            # ensure display nicely formatted
            item.price = Decimal(item.price).quantize(Decimal('0.01'))

    if (isLoggedIn() and
        restaurant.user_id == login_session['user_id']):

        return render_template('PrivateRestaurantMenu.html',
                               restaurant=restaurant,
                               sectionedItems=sectionedItems)
    else:

        return render_template('PublicRestaurantMenu.html',
                               restaurant=restaurant,
                               sectionedItems=sectionedItems)

@app.route('/restaurants/<int:restaurant_id>/menu/add/',
           methods=['GET','POST'])
def addRestaurantMenuItem(restaurant_id):
    '''Serve form to add a restaurant menu item to a restaurant's menu
    '''
    restaurant = RestaurantManager.getRestaurant(restaurant_id)
    
    if not isLoggedIn():

        flash("You must log in to add a base menu item")
        return redirect(url_for('restaurantManagerIndex'))

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to add an item to "+\
            " this restaurant's menu")
        return redirect(url_for('restaurantMenu',
            restaurant_id=restaurant.id))  
    
    client_login_session = getClientLoginSession()

    baseMenuItems = RestaurantManager.getBaseMenuItems()

    for item in baseMenuItems:
        pic = RestaurantManager.getPicture(item.picture_id)
        item.picText = pic.text
        item.picServeType = pic.serve_type

    menuSections = RestaurantManager.getMenuSections()

    # display nicely
    for item in baseMenuItems:
        item.price = Decimal(item.price).quantize(Decimal('0.01'))

    if request.method == 'POST':

        if request.form['hiddenToken'] != login_session['state']:
            # not same entity that first came to login page
            # possible CSRF attack
            flash("An unknown error occurred.  Try signing out"+\
                ", signing back in, and repeating the operation.")

            return redirect(url_for('restaurantManagerIndex'))

        name = None
        description = None
        price = None
        picture_id = None

        if request.form['name']:
            name = bleach.clean(request.form['name'])

            if len(name) > 80:

                flash("Did not add item; name too long")
                return redirect(url_for('restaurantMenu',
                    restaurant_id=restaurant_id))

        if request.form['description']:
            description = bleach.clean(request.form['description'])

            if len(description) > 250:

                flash("Did not add item; description too long")
                return redirect(url_for('restaurantMenu',
                    restaurant_id=restaurant_id))

        if request.form['price']:
            price = bleach.clean(request.form['price'])

            if len(price) > 20:

                flash('Did not add item; price was too long.')
                return redirect(url_for('restaurantMenu',
                    restaurant_id=restaurant.id))

            match = re.search(r'[0-9]*(.[0-9][0-9])?', price)

            if match.group(0) != price:

                flash("Did not add item; price was in an invalid "+\
                    "format.  Use only numerals optionally followed "+\
                    "by a decimal and two more numerals.")
                return redirect(url_for('restaurantMenu', 
                    restaurant_id=restaurant_id))        

        if request.files['pictureFile']:
            picFile = request.files['pictureFile']

            if allowed_pic(picFile.filename):
                # this name will be overwritten.
                # can't provide proper name now because 
                # don't have restaurant_id
                picFile.filename = secure_filename(picFile.filename)
                picture_id = RestaurantManager.\
                    addPicture(text=picFile.filename,
                        serve_type='upload')
            else:

                flash("Did not add restaurant menu item; uploaded pic "+\
                    "was not .png, .jpeg, or .jpg.")
                return redirect(url_for('restaurantMenu'),
                                        restaurant_id=restaurant.id)
        elif request.form['pictureLink']:

            pictureLink = bleach.clean(request.form['pictureLink'])

            if (len(pictureLink) < 7 or 
                (len(pictureLink) == 8 and 
                 pictureLink[:7] != 'http://') or
                (len(pictureLink) == 9 and 
                 pictureLink[:8] != 'https://') or
                (pictureLink[:7] != 'http://' and
                 pictureLink[:8] != 'https://')):

                flash("Did not add item; the link was not a url")
                return redirect(url_for('restaurants'))

            picture_id = RestaurantManager.addPicture(text=pictureLink, 
                                                      serve_type='link')

        # everything defaults to base attribute if none
        RestaurantManager.addRestaurantMenuItem(
            name=name,
            restaurant_id=restaurant_id,
            description=description,
            price=price,
            baseMenuItem_id=request.form['baseMenuItemID'],
            picture_id=picture_id
        )

        # if pic was uploaded, save actual file for serving
        # set the appropriate name in the database
        if request.files['pictureFile']:
            picfilename = 'restaurantMenuItem' + str(restaurant_id)
            picFile.save(os.path.join(app.config['UPLOAD_FOLDER'], picfilename))
            RestaurantManager.editPicture(picture_id=picture_id,
                                          newText=picfilename)

        if name is not None:
            flash("menu item '" + name + "' added to the menu!")
        else:
            flash("added an item to the menu!")

        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:

        return render_template('AddRestaurantMenuItem.html',
                               restaurant=restaurant,
                               baseMenuItems=baseMenuItems,
                               menuSections=menuSections,
                               hiddenToken=login_session['state'],
                               client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/')
def restaurantMenuItem(restaurant_id, restaurantMenuItem_id):
    '''Serve a restaurant menu item
    '''
    restaurant = RestaurantManager.getRestaurant(restaurant_id)

    if not isLoggedIn():

        flash("You must log in to view this item's details")
        return redirect(url_for('restaurantManagerIndex'))

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to view this item's details")
        return redirect(url_for('restaurantMenu',
            restaurant_id=restaurant.id))  
    
    client_login_session = getClientLoginSession()

    restaurantMenuItem = RestaurantManager.\
                         getRestaurantMenuItem(restaurantMenuItem_id)
    restaurantMenuItem.price = Decimal(restaurantMenuItem.price).\
        quantize(Decimal('0.01'))

    restaurantCuisineObj = RestaurantManager.\
                           getCuisine(cuisine_id=restaurant.cuisine_id)
    restaurantCuisine = restaurantCuisineObj.name
    restaurantMenuItemSection = RestaurantManager.\
        getMenuSection(menuSection_id=restaurantMenuItem.menuSection_id)

    baseMenuItem = RestaurantManager.\
        getBaseMenuItem(baseMenuItem_id=restaurantMenuItem.baseMenuItem_id)
    baseMenuItem.price = Decimal(baseMenuItem.price).quantize(Decimal('0.01'))
    baseMenuItemCuisineObj = RestaurantManager.\
                             getCuisine(cuisine_id=baseMenuItem.cuisine_id)
    baseMenuItemCuisine = baseMenuItemCuisineObj.name

    baseMenuItemSection = RestaurantManager.\
        getMenuSection(menuSection_id=baseMenuItem.menuSection_id)

    picture = RestaurantManager.getPicture(restaurantMenuItem.picture_id)

    timesOrdered = 0

    return render_template("RestaurantMenuItem.html",
                    restaurantMenuItem=restaurantMenuItem,
                    restaurant=restaurant,
                    restaurantCuisine=restaurantCuisine,
                    baseMenuItem=baseMenuItem,
                    baseMenuItemCuisine=baseMenuItemCuisine,
                    timesOrdered=timesOrdered,
                    picture=picture,
                    restaurantMenuItemSection=restaurantMenuItemSection,
                    baseMenuItemSection=baseMenuItemSection,
                    client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/edit/',
           methods=['GET','POST'])
def editRestaurantMenuItem(restaurant_id, restaurantMenuItem_id):
    '''Serve a form to edit a restaurant menu item
    '''
    restaurant = RestaurantManager.getRestaurant(restaurant_id)

    if not isLoggedIn():

        flash("You must log in to edit this item")
        return redirect(url_for('restaurantManagerIndex'))

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to edit this item")
        return redirect(url_for('restaurantMenu',
            restaurant_id=restaurant.id))  
    
    client_login_session = getClientLoginSession()

    user_id = restaurant.user_id
    restaurantMenuItem = RestaurantManager.\
        getRestaurantMenuItem(restaurantMenuItem_id)

    restaurantMenuItem.price = Decimal(restaurantMenuItem.price).quantize(Decimal('0.01'))
    
    picture = RestaurantManager.getPicture(restaurantMenuItem.picture_id)

    if request.method == 'POST':

        if request.form['hiddenToken'] != login_session['state']:
            # not same entity that first came to login page
            # possible CSRF attack
            flash("An unknown error occurred.  Try signing out"+\
                ", signing back in, and repeating the operation.")

            return redirect(url_for('restaurantManagerIndex'))

        oldName = restaurantMenuItem.name
        oldDescription = restaurantMenuItem.description
        oldPrice = restaurantMenuItem.price
        newName = None
        newDescription = None
        newPrice = None
        newPicture = None

        if request.form['name']:
            newName = bleach.clean(request.form['name'])

            if len(newName) > 80:

                newName = None
                flash("Did not change name; it was too long")
            
        if request.form['description']:
            newDescription = bleach.clean(request.form['description'])

            if len(newDesription) > 250:

                newDesription = None
                flash("Did not change description; it was too long")
            
        if request.form['price']:
            newPrice = bleach.clean(request.form['price'])
            match = re.search(r'[0-9]*(.[0-9][0-9])?', newPrice)

            if len(newPrice) > 20:

                newPrice = None
                flash("Did not change price; it's too long.")
            elif match.group(0) != newPrice:

                newPrice = None
                flash("Did not change price; it was in an invalid "+\
                    "format.  Use only numerals optionally followed "+\
                    "by a decimal and two more numerals.")

        if request.form['pictureLink'] or request.files['pictureFile']:
            newText = None
            newServe_Type = None

            if request.files['pictureFile']: 
                # user uploaded a file
                picFile = request.files['pictureFile']

                if allowed_pic(picFile.filename):
                    # overwrites pic for restaurant menu item if already there
                    newText = 'restaurantMenuItem' +\
                        str(restaurantMenuItem.id)
                    picFile.save(os.path.join(app.\
                        config['UPLOAD_FOLDER'], newText))

                    if picture.serve_type == 'link':

                        newServe_Type = 'upload'
                else:

                    flash("Sorry, the uploaded pic was not .png, "+\
                        ".jpeg, or .jpg.  Did not change picture.")
            else:
                # user gave a link
                newText = bleach.clean(request.form['pictureLink'])

                if len(newText) > 300:
                    newText = None
                    flash("Did not change pic; link too long")
                elif (len(pictureLink) < 7 or 
                      (len(pictureLink) == 8 and 
                       pictureLink[:7] != 'http://') or
                      (len(pictureLink) == 9 and 
                       pictureLink[:8] != 'https://') or
                      (pictureLink[:7] != 'http://' and
                       pictureLink[:8] != 'https://')):

                    newText = None
                    flash("Did not change pic; the link was not a url")  
                elif picture.serve_type == 'upload':
                    # change serve type and delete old, uploaded pic
                    newServe_Type = 'link'
                    relPath = 'pics/'+picture.text
                    os.remove(relPath)
            
            RestaurantManager.editPicture(restaurantMenuItem.picture_id,
                                          newText=newText,
                                          newServe_Type=newServe_Type)

            if (newText is not None or newServe_Type is not None):
                flash("updated " + restaurantMenuItem.name + "'s picture!")

        # we edited the pic directly, no need to include here
        RestaurantManager.editRestaurantMenuItem(restaurantMenuItem.id,
            newName=newName, newDescription=newDescription, 
            newPrice=newPrice)

        if newName is not None:
            flash("changed restaurant menu item " + \
                str(restaurantMenuItem.id) + \
                "'s name from '" + oldName + "' to '" + newName + "'")

        if newDescription is not None:
            flash("changed restaurant menu item " + \
                str(restaurantMenuItem.id) + \
                "'s description from '"+ oldDescription + "' to '" + \
                newDescription + "'")

        if newPrice is not None:
            flash("changed restaurant menu item " + \
                str(restaurantMenuItem.id) + \
                "'s price from '" + str(oldPrice) + "' to '" + \
                str(newPrice) + "'")

        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:

        return render_template('EditRestaurantMenuItem.html',
                               restaurant=restaurant,
                               restaurantMenuItem=restaurantMenuItem,
                               hiddenToken=login_session['state'],
                               picture=picture,
                               client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/delete/',
           methods=['GET','POST'])
def deleteRestaurantMenuItem(restaurant_id, restaurantMenuItem_id):
    '''Serve a form to delete a restaurant menu item
    '''
    restaurant = RestaurantManager.getRestaurant(restaurant_id)

    if not isLoggedIn():

        flash("You must log in to delete this item")
        return redirect(url_for('restaurantManagerIndex'))

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to delete this item")
        return redirect(url_for('restaurantMenu',
            restaurant_id=restaurant.id))  
    
    client_login_session = getClientLoginSession()

    restaurantMenuItem = RestaurantManager.\
                         getRestaurantMenuItem(restaurantMenuItem_id)

    if request.method == 'POST':

        if request.form['hiddenToken'] != login_session['state']:
            # not same entity that first came to login page
            # possible CSRF attack
            flash("An unknown error occurred.  Try signing out"+\
                ", signing back in, and repeating the operation.")

            return redirect(url_for('restaurantManagerIndex'))

        restaurantMenuItemName = restaurantMenuItem.name

        RestaurantManager.\
            deleteRestaurantMenuItem(restaurantMenuItem_id=restaurantMenuItem_id)

        flash("removed item " + str(restaurantMenuItem_id) + " (" + \
              restaurantMenuItemName + ") from the menu and database")

        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:
        return render_template('DeleteRestaurantMenuItem.html',
                               restaurant=restaurant,
                               restaurantMenuItem=restaurantMenuItem,
                               hiddenToken=login_session['state'],
                               client_login_session=client_login_session)

@app.route('/users/', methods=['GET'])
def users():
    '''Serve information about all users
    '''
    client_login_session = getClientLoginSession()

    users = RestaurantManager.getUsers()

    return render_template('Users.html', users=users,
                           client_login_session=client_login_session)

@app.route('/users/<int:user_id>/', methods=['GET'])
def user(user_id):
    '''Serve a user's profile
    '''
    client_login_session = getClientLoginSession()

    user = RestaurantManager.getUser(user_id=user_id)
    picture = RestaurantManager.getPicture(user.picture_id)
    userThings = RestaurantManager.getUserThings(user.id)

    loggedInStats = {}

    numRestaurants = 0

    mostExpensiveRest = None
    mostExpensiveRestAvgPrice = None
    leastExpensiveRest = None
    leastExpensiveRestAvgPrice = None

    numMenuItems = 0

    mostExpensiveMenuItem = None
    leastExpensiveMenuItem = None

    for restaurantID in userThings:

        numRestaurants = numRestaurants + 1
        numItemsThisRestaurant = 0
        totalRestaurantPrices = 0
        thisRestaurantAvgItemPrice = None

        for menuSectionName in userThings[restaurantID]['items']:

            for item in userThings[restaurantID]['items'][menuSectionName]:

                item.price = Decimal(item.price).\
                    quantize(Decimal('0.01'))
                numMenuItems = numMenuItems + 1
                numItemsThisRestaurant = numItemsThisRestaurant + 1

                if mostExpensiveMenuItem is None:
                    mostExpensiveMenuItem = item
                elif item.price > mostExpensiveMenuItem.price:
                    mostExpensiveMenuItem = item
                elif (leastExpensiveMenuItem is None and
                    numMenuItems > 1):
                    leastExpensiveMenuItem = item
                elif (item.price < leastExpensiveMenuItem.price and
                      numMenuItems > 1):
                    leastExpensiveMenuItem = item

                totalRestaurantPrices = totalRestaurantPrices + item.price

        if numItemsThisRestaurant > 0:
            thisRestaurantAvgItemPrice = \
                totalRestaurantPrices/numItemsThisRestaurant
        else:
            thisRestaurantAvgItemPrice = None

        if (mostExpensiveRest is None and
            numItemsThisRestaurant > 0):

            mostExpensiveRest = \
                userThings[restaurantID]['restaurant']
            mostExpensiveRestAvgPrice = thisRestaurantAvgItemPrice

        elif thisRestaurantAvgItemPrice > mostExpensiveRestAvgPrice:

            mostExpensiveRest = \
                userThings[restaurantID]['restaurant']
            mostExpensiveRestAvgPrice = thisRestaurantAvgItemPrice
        elif (leastExpensiveRest is None and
              numRestaurants > 1 and
              numItemsThisRestaurant > 0):
            leastExpensiveRest = \
                userThings[restaurantID]['restaurant']
            leastExpensiveRestAvgPrice = thisRestaurantAvgItemPrice
        elif (thisRestaurantAvgItemPrice < \
                leastExpensiveRestAvgPrice and
              numRestaurants > 1):
            leastExpensiveRest = \
                userThings[restaurantID]['restaurant']
            leastExpensiveRestAvgPrice = thisRestaurantAvgItemPrice

    if mostExpensiveRestAvgPrice:
        mostExpensiveRestAvgPrice = \
            Decimal(mostExpensiveRestAvgPrice).\
            quantize(Decimal('0.01'))
    
    if leastExpensiveRestAvgPrice:
        leastExpensiveRestAvgPrice = \
            Decimal(leastExpensiveRestAvgPrice).\
            quantize(Decimal('0.01'))

    if (isLoggedIn() and
        login_session['user_id'] == user.id):
        # could put stats in a loginStats dictionary
        return render_template('PrivateUserProfile.html',
            user=user,
            picture=picture,
            userThings=userThings,
            numRestaurants=numRestaurants,
            numMenuItems=numMenuItems,
            mostExpensiveRest=mostExpensiveRest,
            mostExpensiveRestAvgPrice=mostExpensiveRestAvgPrice,
            leastExpensiveRest=leastExpensiveRest,
            leastExpensiveRestAvgPrice=leastExpensiveRestAvgPrice,
            mostExpensiveMenuItem=mostExpensiveMenuItem,
            leastExpensiveMenuItem=leastExpensiveMenuItem,
            client_login_session=client_login_session)
    else:

        return render_template('PublicUserProfile.html',
                               user=user,
                               picture=picture,
                               userThings=userThings,
                               numRestaurants=numRestaurants,
                               numMenuItems=numMenuItems,
                               client_login_session=client_login_session)

@app.route('/users/<int:user_id>/edit/', methods=['GET','POST'])
def editUser(user_id):
    '''Serve a form to edit a user
    '''
    user = RestaurantManager.getUser(user_id)

    if not isLoggedIn():

        flash("You must log in to edit this profile")
        return redirect(url_for('restaurantManagerIndex'))

    if user.id != login_session['user_id']:

        flash("You do not have permission to edit this profile")
        return redirect(url_for('user', user_id=user.id))  
    
    client_login_session = getClientLoginSession()

    picture = RestaurantManager.getPicture(user.picture_id)

    if request.method == 'POST':

        if request.form['hiddenToken'] != login_session['state']:
            # not same entity that first came to login page
            # possible CSRF attack
            flash("An unknown error occurred.  Try signing out"+\
                ", signing back in, and repeating the operation.")

            return redirect(url_for('restaurantManagerIndex'))

        oldName = user.name
        newName = None
        
        if request.form['name']:
            newName = bleach.clean(request.form['name'])
            # in spirit of trying to include names from other scripts
            # (like chinese, thai)
            match = \
                re.search(r"[^~`!@#\$%\^&\*\(\)_=\+\{}\[\]\\\|\.<>\?/;:]\+"\
                , newName)
            if match is not None:

                newName = None
                flash("Did not change username; contained an "+\
                    "illegal character")
            elif len(newName) > 30:

                newName = None
                flash("Did not change username; it was too long")             

        if request.form['pictureLink'] or request.files['pictureFile']:

            newText = None
            newServe_Type = None

            if request.files['pictureFile']: 
                # user uploaded a file
                picFile = request.files['pictureFile']

                if allowed_pic(picFile.filename):
                    # overwrites pic for base menu item if already there
                    newText = 'user' + str(user.id)
                    picFile.save(os.path.join(app.config['UPLOAD_FOLDER'],\
                        newText))

                    if picture.serve_type == 'link':
                        # change type and delete any old, uploaded pic
                        newServe_Type = 'upload'
                else:

                    flash("Did not change pic; the uploaded pic was not "+\
                        ".png, .jpeg, or .jpg.")
            else:
                # user gave a link
                newText = bleach.clean(request.form['pictureLink'])

                if len(newText) > 300:

                    newText = None
                    flash('Did not change pic; link too long')
                elif (len(pictureLink) < 7 or 
                      (len(pictureLink) == 8 and 
                       pictureLink[:7] != 'http://') or
                     (len(pictureLink) == 9 and 
                      pictureLink[:8] != 'https://') or
                     (pictureLink[:7] != 'http://' and
                      pictureLink[:8] != 'https://')):

                    flash("Did change pic; the link was not a url")
                elif picture.serve_type == 'upload':
                    # change type and delete any old, uploaded pic
                    newServe_Type = 'link'
                    relPath = 'pics/'+picture.text
                    os.remove(relPath)
            
            RestaurantManager.editPicture(user.picture_id,
                newText=newText,
                newServe_Type=newServe_Type)

            if (newText is not None or newServe_Type is not None):
                flash("updated your picture!")

        # we edited the pic directly, no need to include here
        RestaurantManager.editUser(user.id, newName=newName)

        if newName is not None:

            login_session['username'] = newName
            flash("changed your username from '" + oldName +\
                "' to '"+newName+"'")

        return redirect(url_for('user', user_id=user.id))
    else:

        return render_template('EditUser.html',
                           user=user,
                           picture=picture,
                           hiddenToken=login_session['state'],
                           client_login_session=client_login_session)

@app.route('/users/<int:user_id>/delete/', methods=['GET','POST'])
def deleteUser(user_id):
    '''Serve a form to delete a user
    '''
    user = RestaurantManager.getUser(user_id)

    if not isLoggedIn():

        flash("You must log in to delete this profile")
        return redirect(url_for('restaurantManagerIndex'))

    if user.id != login_session['user_id']:

        flash("You do not have permission to delete this profile")
        return redirect(url_for('user', user_id=user.id))  
    
    client_login_session = getClientLoginSession()

    if request.method == 'POST':

        if request.form['hiddenToken'] != login_session['state']:
            # not same entity that first came to login page
            # possible CSRF attack
            flash("An unknown error occurred.  Try signing out"+\
                ", signing back in, and repeating the operation.")

            return redirect(url_for('restaurantManagerIndex'))

        RestaurantManager.deleteUser(user.id)

        flash(disconnect())

        flash("deleted " + user.name + " from " +\
            "the database")

        return redirect(url_for('users'))

    return render_template('DeleteUser.html',
                           user=user,
                           hiddenToken=login_session['state'],
                           client_login_session=client_login_session)


###############################################################################
# Helper Functions
###############################################################################

def allowed_pic(filename):
    '''Return true if the file name is a valid pic filename
    '''
    return ('.' in filename and 
            filename.rsplit('.', 1)[1] in ALLOWED_PIC_EXTENSIONS)

def isLoggedIn():
    '''Return true if the user is logged in
    '''
    return ('credentials' in login_session and
            'access_token' in login_session['credentials'] and
            'user_id' in login_session)

def setProfile():
    '''Populate the login session with the logged in user's settings
    '''
    user = RestaurantManager.getUser(email=login_session['email'])

    # create the user if the user doesn't exist
    if user is None:
        picture_id = RestaurantManager.addPicture(text=login_session['picture'],
                                                  serve_type='link')
        RestaurantManager.addUser(name=login_session['username'],
                                  email=login_session['email'],
                                  picture_id=picture_id)
        user = RestaurantManager.getUser(email=login_session['email'])

    # set this user's saved settings for our app
    picture = RestaurantManager.getPicture(user.picture_id)
    login_session['user_id'] = user.id
    login_session['username'] = user.name
    login_session['picture'] = picture.text
    login_session['picture_serve_type'] = picture.serve_type

def getSignInAlert():
    ''' Return a JSON-format object representing a successful signin
    '''
    outputDict = {}

    outputDict['loginMessage'] = "Welcome, " + \
        login_session['username'] + "!"
    outputDict['picture'] = login_session['picture']
    outputDict['picture_serve_type'] = login_session['picture_serve_type']

    flash("you are now logged in as %s" % login_session['username'])

    return json.dumps(outputDict)

def getClientLoginSession():
    ''' Return a dict with entries for setting dynamic client-side content

    Also avoids passing all of current session.
    '''
    client_login_session = {}
    client_login_session['username'] = ""
    client_login_session['user_id'] = -99
    client_login_session['message'] = 'Not logged in'

    if isLoggedIn():

        client_login_session['username'] = login_session['username']
        client_login_session['user_id'] = login_session['user_id']
        client_login_session['message'] = "Logged in as " + \
            login_session['username']

    return client_login_session

###
### Form validation
###

def checkCSRFAttack(currentState, redirectURL):
    '''Validate the request came from the same session that logged in
    at the homepage.
    '''
    if currentState != login_session['state']:
        flash("An unknown error occurred.  Sorry!  Try signing out, "+\
            "signing back in, and repeating the operation.")
        return redirect(redirectURL)

def validateUserInput(userInput, columnName, CRUDtype, itemNameForMsg, 
                      maxlength=None, required=False, unique=False, 
                      oldInput=None, tableName=None, priceFormat=False):
    '''Validate (and strip HTML) from user input

    Returns the validated name, 
    or none with a flahsed messageif the test fails.

    Args:
        userInput: the input to validate
        columnName: the name of the database column for this input
        CRUDtype: create, read, update, or delete
        itemNameForMsg: the name for this item in response text
            to the user
        required: true if form submission requires this input
        unique: whether this input needs to be unique in the table
        oldInput: for an edit -- the value to replace
        tableName only needed if unique is True.
    '''
    badResult = "Did not " + CRUDtype + " " + itemNameForMsg + ". "
    neutralResult = "Did not edit " + columnName + ". "

    if not userInput or len(userInput) < 1:

        if required:

            flash(badResult + "Must provide a " + columnName + ".") 
        else:

            flash(neutralResult + "Nothing provided.")

        return None

    userInput = bleach.clean(userInput)

    if userInput and maxlength:
        if len(userInput) > maxlength:

            if required:

                flash(badResult + columnName + "was too long.")
            else:
                flash(neutralResult + "It was too long.")

            return None

    if userInput and priceFormat:

        match = re.search(r'[0-9]*(.[0-9][0-9])?', userInput)

        if match.group(0) != userInput:

            if required:
                flash(badResult + "Price was in an invalid format.")
            else:

                flash(neutralResult + "It was in an invalid format.")

            return None

        userInput = Decimal(userInput).quantize(Decimal('0.01'))

    if userInput and unique:
        if not isUnique(userInput, columnName, tableName):
            
            if required:

                flash(badResult + columnName + " was not unique.")
            else: 

                flash(neutralResult + "It was not unique.")
            return None

    if userInput and oldInput:
        if userInput == oldInput:

            if required:

                flash(neutralResult + columnName +\
                    "provided is same as before")
            else:

                flash(neutralResult + \
                    "The one provided was the same as before.")

            return None

    return userInput

def validateUserPicture(CRUDtype, file=None, link=None,
                        maxlength=None, unique=False, required=False):
    '''Validate (and strip HTML from) a picture file or link 
    provided by a user.

    Returns dictionary with 'text' and 'serve_type' keys,
    or None if a test fails.

    Does NOT fail if, for an edit, provided pic is same as the old pic
    '''
    badResult = "Did not " + CRUDtype + " picture. "
    neutralResult = "Did not edit picture. "   

    pictureDict = {}

    if file:

        file.filename = bleach.clean(file.filename)

        if allowed_pic(file.filename):
            # this name will be overwritten eventually
            # but better safe than sorry
            file.filename = secure_filename(file.filename)
            
            pictureDict['text'] = file.filename
            pictureDict['serve_type'] = 'upload'
        else:
            
            if required:
                flash(badResult + "the uploaded pic was not "+\
                        ".png, .jpeg, or .jpg.")
            else:
                flash(neutralResult + "the uploaded pic was not "+\
                        ".png, .jpeg, or .jpg.")               

            return None
    elif link:

        link = bleach.clean(link)

        if maxlength:
            if len(link) > maxlength:

                if required:

                    flash(badResult + "The link was too long.")
                else:

                    flash(neutralResult + "The link was too long.")

                return None

        if not isURL(link):

            if required:
                
                flash(badResult + "The link was not a url.")
            else:

                flash(neutralResult + "The link was not a url.")

            return None

        pictureDict['text'] = link
        pictureDict['serve_type'] = 'link'

    # if there was input provided
    if 'text' in pictureDict:

        return pictureDict
    else:

        if required:
            
            flash(badResult + 'You must provide a picture.')
        else:

            flash(neutralResult + 'You did not provide one.')

        return None

def isUnique(value, columnName, tableName):
    '''Return true if value is unique for a column within a table

    Incomplete method, but does what I need it to do for now.
    '''
    sameValue = None

    # syntax for python switch statement? hashtag no internet connection
    if tableName == 'BaseMenuItem':
        if columnName == 'name':
            sameValue = RestaurantManager.\
                        getBaseMenuItem(baseMenuItemName=value)
    elif tableName == 'Cuisine':
        if columnName == 'name':
            sameValue = RestaurantManager.getCuisine(name=value)

    if not sameValue:
        return True
    else:
        return False 

def isURL(string):
    '''Return whether a string represents a valid url

    Just checks for beginning http:// or https:// followed by a char
    '''
    if (len(string) < 8 or 
        (len(string) == 7 and string[:6] != 'http://') or
        (len(string) == 8 and string[:7] != 'https://') or
        (string[:6] != 'http://' and string[:7] != 'https://')):

        return True;
    else:

        return False;

###############################################################################
###############################################################################

###
### Set properties if this app is the main program
###

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
