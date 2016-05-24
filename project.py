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
    login_session['picture'] = data['picture']
    login_session['username'] = data['user_name']

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
    '''Serve info about all of the restaurants
    '''
    client_login_session = getClientLoginSession()

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

            numRestaurants += 1
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
                    client_login_session=client_login_session)

@app.route('/restaurants/add/', methods=['GET','POST'])
def addRestaurant():
    '''Serve form to add a restaurant
    '''
    if not isLoggedIn():

        flash("You must log in to add a restaurant")
        return redirect(url_for('restaurantManagerIndex'))
    
    client_login_session = getClientLoginSession()

    cuisines = RestaurantManager.getCuisines()

    if request.method == 'POST':

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        validCuisineIDs = {}
        for cuisine in cuisines:
            validCuisineIDs[str(cuisine.id)] = True

        cuisine_id = validateUserInput(request.form['cuisineID'],
                'cuisine_id', 'create', 'restaurant', 
                columnNameForMsg='cuisine', required=True,
                validInputs=validCuisineIDs)

        if cuisine_id is None:
            return redirect(url_for('restaurants'))               

        name = validateUserInput(request.form['name'], 'name', 'create',
            'restaurant', maxlength=100, required=True)

        if name is None:
            return redirect(url_for('restaurants'))    

        providedPic = validateUserPicture('create', 'restaurant',
            file=request.files['pictureFile'],
            link=request.form['pictureLink'],
            maxlength=300, required=True)

        if providedPic is None:
            return redirect(url_for('restaurants'))
        
        picture_id = RestaurantManager.addPicture(text=providedPic['text'], 
            serve_type=providedPic['serve_type'])

        restaurant_id = RestaurantManager.addRestaurant(
                            name=name,
                            cuisine_id=cuisine.id,
                            user_id=login_session['user_id'],
                            picture_id=picture_id
                        )

        # if pic was uploaded, now that we know item id, 
        # save actual file for serving and set the name in the database
        if providedPic['serve_type'] == 'upload':
            picfilename = 'restaurant' + str(restaurant_id)
            request.files['pictureFile'].save(os.path.\
                join(app.config['UPLOAD_FOLDER'], picfilename))
            RestaurantManager.editPicture(picture_id=picture_id,
                                          newText=picfilename)

        RestaurantManager.populateMenuWithBaseItems(restaurant_id)

        flash("restaurant '" + name + "' added to the database!")

        return redirect(url_for('restaurants'))
    else:

        return render_template('AddRestaurant.html', 
                                cuisines=cuisines,
                                hiddenToken=login_session['state'],
                                client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/')
def restaurant(restaurant_id):
    '''Serve info about a restaurant
    '''
    client_login_session = getClientLoginSession()

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
                mostExpensiveItem.price =\
                    Decimal(mostExpensiveItem.price).\
                    quantize(Decimal('0.01'))
        mostExpensiveItem.price =\
            Decimal(mostExpensiveItem.price).\
            quantize(Decimal('0.01'))
    else:
        mostExpensiveItem = RestaurantManager.\
                            getBaseMenuItem(baseMenuItem_id=-1)
        mostExpensiveItem.name = 'N/A'
        mostExpensiveItem.price = 'N/A'

    return render_template('Restaurant.html', restaurant=restaurant, 
                           numMenuItems=numMenuItems,
                           mostExpensiveItem=mostExpensiveItem,
                           cuisine=cuisine, picture=picture, owner=owner,
                           client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/edit/',
           methods=['GET','POST'])
def editRestaurant(restaurant_id):
    '''Serve form to add a restaurant menu item to a restaurant's menu
    '''
    restaurant = RestaurantManager.getRestaurant(restaurant_id)
    
    if not isLoggedIn():

        flash("You must log in to edit a restaurant")
        return redirect(url_for('restaurantManagerIndex'))

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to edit this restaurant")
        return redirect(url_for('restaurant',
            restaurant_id=restaurant.id))

    client_login_session = getClientLoginSession()

    restaurant = RestaurantManager.getRestaurant(restaurant_id)
    cuisines = RestaurantManager.getCuisines()
    picture = RestaurantManager.getPicture(restaurant.picture_id)
    
    if request.method == 'POST':

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        oldName = restaurant.name
        oldCuisine = RestaurantManager.\
                     getCuisine(cuisine_id=restaurant.cuisine_id)
        oldPicture = RestaurantManager.getPicture(restaurant.picture_id)
        
        newName = validateUserInput(request.form['name'], 'name',
            'edit', 'restaurant', maxlength=100)

        validCuisineIDs = {}
        for cuisine in cuisines:
            validCuisineIDs[str(cuisine.id)] = True

        # for 'do not change'
        validCuisineIDs['-2'] = True

        newCuisine_id = validateUserInput(request.form['cuisineID'],
                'cuisine_id', 'edit', 'restaurant',
                columnNameForMsg='cuisine', oldInput=str(oldCuisine.id),
                validInputs=validCuisineIDs)  

        if newCuisine_id == '-2':
            newCuisine_id = None

        providedPic = validateUserPicture('edit', 'base menu item',
            file=request.files['pictureFile'],
            link=request.form['pictureLink'], maxlength=300)

        if providedPic is not None:
            # delete the old pic if it was an upload and new is a link
            # or save the new pic if it was an upload
            if (providedPic['serve_type'] == 'link' and
                oldPicture.serve_type == 'upload'):

                relPath = 'pics/'+oldPicture.text
                os.remove(relPath)
                flash("deleted old uploaded pic")
            elif providedPic['serve_type'] == 'upload':
                picfilename = 'restaurant' + str(restaurant_id)
                request.files['pictureFile'].save(os.path.\
                    join(app.config['UPLOAD_FOLDER'], picfilename))
                providedPic['text'] = picfilename

            # edit the pic
            RestaurantManager.editPicture(restaurant.picture_id,
                newText=providedPic['text'], 
                newServe_Type=providedPic['serve_type'])

            flash("updated base menu item picture")

        # we edited the pic directly, no need to include here
        RestaurantManager.editRestaurant(restaurant.id,
            newName=newName, newCuisine_id=newCuisine_id)

        restaurant = RestaurantManager.getRestaurant(restaurant_id)

        if newName is not None:
            flash("changed " + restaurant.name + "'s (ID " + \
                str(restaurant.id) + ") name from '" + oldName + \
                "' to '" + newName + "'")

        if newCuisine_id is not None:
            flash("changed " + restaurant.name + "'s (ID " + \
                str(restaurant.id) + ") cuisine")
        
        return redirect(url_for('restaurant',
                                restaurant_id=restaurant_id))
    else:

        return render_template('EditRestaurant.html',
                               restaurant=restaurant,
                               cuisines=cuisines,
                               hiddenToken=login_session['state'],
                               picture=picture,
                               client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    '''Serve form to delete a restaurant
    '''
    restaurant = RestaurantManager.getRestaurant(restaurant_id)
    
    if not isLoggedIn():

        flash("You must log in to delete a restaurant")
        return redirect(url_for('restaurantManagerIndex'))

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to delete this restaurant")
        return redirect(url_for('restaurant',
            restaurant_id=restaurant.id))

    client_login_session = getClientLoginSession()

    if request.method == 'POST':

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

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
                               client_login_session=client_login_session)

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

        validMenuSectionIDs = {}
        for menuSection in menuSections:
            validMenuSectionIDs[str(menuSection.id)] = True

        menuSection_id = validate(request.form['menuSection'],
                'menuSection_id', 'create', 'base menu item',
                columnNameForMsg='menu section', required=True, 
                validInputs=validMenuSectionIDs)

        if menuSection_id is None:
            return redirect(url_for('cuisine', cuisine_id=cuisine.id))

        providedPic = validateUserPicture('create', 'base menu item',
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

        # if pic was uploaded, now that we know item id, 
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

        flash("You must log in to edit a base menu item")
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
        oldMenuSection_id = baseMenuItem.menuSection_id
        
        newName = validateUserInput(request.form['name'], 'name', 
            'edit', 'base menu item', maxlength=80, 
            unique=True, oldInput=oldName)
            
        newDescription = validateUserInput(request.form['description'],
            'description', 'edit', 'base menu item', maxlength=250,
            oldInput=oldDescription)

        newPrice = validateUserInput(request.form['price'], 'price',
            'edit', 'base menu item', maxlength=20,
            priceFormat=True, oldInput=str(oldPrice))

        validMenuSectionIDs = {}
        for menuSection in menuSections:
            validMenuSectionIDs[str(menuSection.id)] = True

        # for 'do not change'
        validMenuSectionIDs['-1'] = True

        newMenuSection_id = validate(request.form['menuSection'],
                'menuSection_id', 'edit', 'base menu item',
                columnNameForMsg='menu section',
                oldInput=str(oldMenuSection_id),
                validInputs=validMenuSectionIDs)

        if newMenuSection_id == '-1':
            newMenuSection_id = None

        providedPic = validateUserPicture('edit', 'base menu item',
            file=request.files['pictureFile'],
            link=request.form['pictureLink'], maxlength=300)

        if providedPic is not None:
            # delete the old pic if it was an upload and new is a link
            # or save the new pic if it was an upload
            if (providedPic['serve_type'] == 'link' and
                oldPicture.serve_type == 'upload'):
            
                relPath = 'pics/'+oldPicture.text
                os.remove(relPath)
                flash("deleted old uploaded pic")
            elif providedPic['serve_type'] == 'upload':

                picfilename = 'baseMenuItem' + str(baseMenuItem_id)
                request.files['pictureFile'].save(os.path.\
                    join(app.config['UPLOAD_FOLDER'], picfilename))
                providedPic['text'] = picfilename

            # edit the pic
            RestaurantManager.editPicture(baseMenuItem.picture_id,
                newText=providedPic['text'], 
                newServe_Type=providedPic['serve_type'])

            flash("updated base menu item picture")

        # we edited the pic directly, no need to include here
        RestaurantManager.editBaseMenuItem(baseMenuItem.id,
            newName=newName, newDescription=newDescription, 
            newPrice=newPrice, newMenuSection_id=newMenuSection_id)

        if newName is not None:
            flash("changed name from '"+oldName+"' to '"+newName+"'")

        if newDescription is not None:
            flash("changed description from '"+ oldDescription + "' to '" + \
                newDescription + "'")

        if newPrice is not None:
            flash("changed price from '" + str(oldPrice) + "' to '" + \
                str(newPrice) + "'")

        if menuSection_id is not Non:
            flash("changed menu section")

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

        flash("You must log in to delete a base menu item")
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

        flash("You must log in to add a restaurant menu item")
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

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        validBaseMenuItemIDs = {}
        for item in baseMenuItems:
            validBaseMenuItemIDs[str(item.id)] = True

        baseMenuItem_id = validateUserInput(request.form['baseMenuItemID'],
            'baseMenuItem_id', 'create', 'restaurant menu item',
            columnNameForMsg='base menu item',
            validInputs=validBaseMenuItemIDs, required=True)

        if baseMenuItem_id is None:
            return redirect(url_for('restaurantMenu', 
                restaurant_id=restaurant_id))

        baseMenuItem = RestaurantManager.\
            getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)

        # if a field is provided, use it, else use the base menu item's attr
        if request.form['name']:

            name = validateUserInput(request.form['name'], 'name', 'create',
                'restaurant menu item', maxlength=80, required=True)
            
            if name is None:
                return redirect(url_for('restaurantMenu', 
                    restaurant_id=restaurant_id))   
        else:

            name = baseMenuItem.name

        if request.form['description']:
        
            description = validateUserInput(request.form['description'],
                'description', 'create', 'restaurant menu item',
                maxlength=250, required=True)

            if description is None:
                return redirect(url_for('restaurantMenu', 
                    restaurant_id=restaurant_id))   
        else:

            description = baseMenuItem.description

        if request.form['price']:

            price = validateUserInput(request.form['price'], 'price', 
                'create', 'restaurant menu item', maxlength=20, 
                required=True, priceFormat=True)

            if price is None:
                return redirect(url_for('restaurantMenu', 
                    restaurant_id=restaurant_id))  
        else:

            price = baseMenuItem.price 

        if request.files['pictureFile'] or request.form['pictureLink']:
        
            providedPic = validateUserPicture('create', 'restaurant menu item',
                file=request.files['pictureFile'],
                link=request.form['pictureLink'],
                maxlength=300, required=True)

            if providedPic is None:
                return redirect(url_for('restaurantMenu', 
                    restaurant_id=restaurant_id))  
            else:           

                picture_id = RestaurantManager.\
                    addPicture(text=providedPic['text'], 
                        serve_type=providedPic['serve_type'])
        else:

            picture_id = baseMenuItem.picture_id

        validMenuSectionIDs = {}
        for menuSection in menuSections:
            validMenuSectionIDs[str(menuSection.id)] = True

        # if this is somehow None, 
        # the add function defaults to base item's attr
        menuSection_id = validateUserInput(request.form['menuSectionID'],
            'menuSection_id', 'create', 'restaurant menu item',
            columnNameForMsg='menu section',
            validInputs=validMenuSectionIDs, required=True)

        restaurantMenuItem_id = RestaurantManager.\
            addRestaurantMenuItem(name=name, restaurant_id=restaurant_id,
            description=description, price=price,
            baseMenuItem_id=baseMenuItem_id, picture_id=picture_id,
            menuSection_id=menuSection_id)

        # if pic was uploaded, now that we know item id, 
        # save actual file for serving and set the name in the database
        if (request.files['pictureFile'] and
            providedPic['serve_type'] == 'upload'):

            picfilename = 'restaurantMenuItem' + str(restaurantMenuItem_id)
            request.files['pictureFile'].save(os.path.\
                join(app.config['UPLOAD_FOLDER'], picfilename))
            RestaurantManager.editPicture(picture_id=picture_id,
                                          newText=picfilename)

        flash("menu item '" + name + "' added to the menu!")

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

    menuSections = RestaurantManager.getMenuSections()

    if request.method == 'POST':

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        oldName = restaurantMenuItem.name
        oldDescription = restaurantMenuItem.description
        oldPrice = restaurantMenuItem.price
        oldMenuSection_id = restaurantMenuItem.menuSection_id
        oldPicture = picture

        newName = validateUserInput(request.form['name'], 'name',
            'edit', 'restaurant menu item', maxlength=80, oldInput=oldName)
        
        newDescription = validateUserInput(request.form['description'],
            'description', 'edit', 'restaurant menu item', maxlength=250,
            oldInput=oldDescription)
            
        newPrice = validateUserInput(request.form['price'], 'price',
            'edit', 'restaurant menu item', maxlength=20, 
            oldInput=oldPrice, priceFormat=True)
            
        validMenuSectionIDs = {}
        for menuSection in menuSections:
            validMenuSectionIDs[str(menuSection.id)] = True

        # for 'do not change'
        validMenuSectionIDs['-1'] = True

        newMenuSection_id = validateUserInput(request.form['menuSection'],
                'menuSection_id', 'edit', 'restaurant menu item',
                columnNameForMsg='menu section',
                oldInput=str(oldMenuSection_id),
                validInputs=validMenuSectionIDs)

        if newMenuSection_id == '-1':
            newMenuSection_id = None

        providedPic = validateUserPicture('edit', 'restaurant menu item',
            file=request.files['pictureFile'], 
            link=request.form['pictureLink'], maxlength=300)

        if providedPic is not None:
            # delete the old pic if it was an upload and new is a link
            # or save the new pic if it was an upload
            if (providedPic['serve_type'] == 'link' and
                oldPicture.serve_type == 'upload'):
            
                relPath = 'pics/'+oldPicture.text
                os.remove(relPath)
                flash("deleted old uploaded pic")
            elif providedPic['serve_type'] == 'upload':

                picfilename = 'restaurantMenuItem' + \
                    str(restaurantMenuItem_id)
                request.files['pictureFile'].save(os.path.\
                    join(app.config['UPLOAD_FOLDER'], picfilename))
                providedPic['text'] = picfilename

            # edit the pic
            RestaurantManager.editPicture(restaurantMenuItem.picture_id,
                newText=providedPic['text'], 
                newServe_Type=providedPic['serve_type'])

            flash("updated restaurant menu item picture")

        # we edited the pic directly, no need to include here
        RestaurantManager.editRestaurantMenuItem(restaurantMenuItem.id,
            newName=newName, newDescription=newDescription, 
            newPrice=newPrice, newMenuSection_id=newMenuSection_id)

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

        if newMenuSection_id is not None:
            flash("changed the restaurant menu item's menu section")

        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:

        return render_template('EditRestaurantMenuItem.html',
                               restaurant=restaurant,
                               restaurantMenuItem=restaurantMenuItem,
                               menuSections=menuSections,
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

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        restaurantMenuItemName = restaurantMenuItem.name

        RestaurantManager.\
            deleteRestaurantMenuItem(restaurantMenuItem_id=\
                restaurantMenuItem_id)

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

    # calculate some stats to show
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
            user=user, picture=picture, userThings=userThings,
            numRestaurants=numRestaurants, numMenuItems=numMenuItems,
            mostExpensiveRest=mostExpensiveRest,
            mostExpensiveRestAvgPrice=mostExpensiveRestAvgPrice,
            leastExpensiveRest=leastExpensiveRest,
            leastExpensiveRestAvgPrice=leastExpensiveRestAvgPrice,
            mostExpensiveMenuItem=mostExpensiveMenuItem,
            leastExpensiveMenuItem=leastExpensiveMenuItem,
            client_login_session=client_login_session)
    else:

        return render_template('PublicUserProfile.html',
            user=user, picture=picture, userThings=userThings,
            numRestaurants=numRestaurants, numMenuItems=numMenuItems,
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

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        oldName = user.name
        oldPicture = picture
        
        newName = validateUserInput(request.form['name'], 'name',
            'edit', 'user', maxlength=30, oldInput=oldName,
            usernameFormat=True)       

        providedPic = validateUserPicture('edit', 'user',
            file=request.files['pictureFile'], 
            link=request.form['pictureLink'], maxlength=300)

        if providedPic is not None:
            # delete the old pic if it was an upload and new is a link
            # or save the new pic if it was an upload
            if (providedPic['serve_type'] == 'link' and
                oldPicture.serve_type == 'upload'):

                relPath = 'pics/'+oldPicture.text
                os.remove(relPath)
                flash("deleted old uploaded pic")
            elif providedPic['serve_type'] == 'upload':

                picfilename = 'user' + str(user_id)
                request.files['pictureFile'].save(os.path.\
                    join(app.config['UPLOAD_FOLDER'], picfilename))
                providedPic['text'] = picfilename
            
            # edit the pic
            print providedPic['serve_type']
            print providedPic['text']
            RestaurantManager.editPicture(user.picture_id,
                newText=providedPic['text'], 
                newServe_Type=providedPic['serve_type'])

            picture = RestaurantManager.getPicture(user.picture_id)

            login_session['picture'] = picture.text
            login_session['picture_serve_type'] = picture.serve_type
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

        checkCSRFAttack(request.form['hiddenToken'],
                        "url_for('restaurantManagerIndex')")

        RestaurantManager.deleteUser(user.id)

        disconnect()

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
                      columnNameForMsg=None, maxlength=None, 
                      required=False, unique=False, oldInput=None, 
                      tableName=None, priceFormat=False, 
                      validInputs=None, usernameFormat=False):
    '''Validate (and strip HTML) from user input

    Returns the validated name, 
    or none with a flahsed messageif the test fails.

    Args:
        userInput: the input to validate
        columnName: the name of the database column for this input
        columnNameForMsg: the name of the columm for user message.
            Pass None if same as columnName.
        CRUDtype: create, read, update, or delete
        itemNameForMsg: the name for this item in response text
            to the user
        maxlength: the max allowable length of this input
        required: true if form submission requires this input
        unique: whether this input needs to be unique in the table
        oldInput: for an edit -- the value to replace
        tableName only needed if unique is True.
        priceFormat: true if this input should be in standard price format
        validInputs: dictionary with keys that are the only valid inputs
        usernameFormat: true if the input should be a legal username
    '''
    if not columnNameForMsg:
        columnNameForMsg = columnName

    badResult = "Did not " + CRUDtype + " " + itemNameForMsg + ". "
    neutralResult = "Did not edit " + columnNameForMsg + ". "

    if not userInput or len(userInput) < 1:

        if required:

            flash(badResult + "Must provide a " + columnNameForMsg + ".")
        else:

            flash(neutralResult + "Nothing provided.")

        return None

    userInput = bleach.clean(userInput)

    if userInput and maxlength:
        if len(userInput) > maxlength:

            if required:

                flash(badResult + columnNameForMsg + "was too long.")
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

                flash(badResult + columnNameForMsg + " was not unique.")
            else: 

                flash(neutralResult + "It was not unique.")
            return None

    if userInput and oldInput:
        if userInput == oldInput:

            if required:

                flash(badResult + columnNameForMsg +\
                    " provided was same as before")
            else:

                flash(neutralResult + \
                    "The one provided was the same as before.")

            return None

    if userInput and validInputs:
        if userInput not in validInputs:

            if required:

                flash(badResult + columnNameForMsg + \
                    " was not a valid selection")
            else:

                flash(neutralResult + \
                    "It was not a valid selection.")

            return None

    if userInput and usernameFormat:
        match = \
            re.search(r"[^~`!@#\$%\^&\*\(\)_=\+\{}\[\]\\\|\.<>\?/;:]\+",
                userInput)
        if match is not None:

            if required:

                flash(badResult + columnNameForMsg + \
                    " was contained an illegal character.")
            else:

                flash(neutralResult + \
                    "It contained an illegal character.")

            return None

    return userInput

def validateUserPicture(CRUDtype, itemNameForMsg, file=None, link=None,
                        maxlength=None, required=False):
    '''Validate (and strip HTML from) a picture file or link 
    provided by a user.

    Returns dictionary with 'text' and 'serve_type' keys,
    or None if a test fails.

    Does NOT fail if, for an edit, provided pic is same as the old pic
    Does not provide a "unique" argument.

    Args:
        CRUDtype: create, read, update, or delete
        itemNameForMsg: the name for this item in response text
            to the user
        file: the file provided by the user
        link: the link provided by the user
        maxlength: the maximum allowable length for the pic's text
        required: true if form submission requires this input
    '''
    badResult = "Did not " + CRUDtype + itemNameForMsg + ". "
    neutralResult = "Did not edit picture. "   

    pictureDict = {}

    if file:

        print file.filename
        print "tehre was a file"
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

        print "was link"
        print link
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
