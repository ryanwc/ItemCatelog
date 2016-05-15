from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask import session as login_session
from flask import make_response
from werkzeug import secure_filename
import requests

from wand.image import Image

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import traceback

import httplib2

import json

from database_setup import Base, Restaurant, BaseMenuItem, Cuisine, RestaurantMenuItem, User

import RestaurantManager

from decimal import *

import bleach

import random, string, decimal


app = Flask(__name__)

CLIENT_ID = json.loads(open('/vagrant/catalog/client_secrets.json', 
    'r').read())['web']['client_id']

# This is the path to the upload directory
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'pics')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# These are the extentions we allow to be uploaded
ALLOWED_PIC_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

### for returning uloaded images to the browser
@app.route('/pics/<filename>/')
def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'],filename) 

### ajax enpoint for google sign in authentication
@app.route('/gconnect', methods=['POST'])
def gconnect():
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
            oauth_flow = flow_from_clientsecrets('/vagrant/catalog/client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except:

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
        
        # verify that the access token is used for the intended user
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            response = make_response(json.dumps("Token's user ID doesn't match given user"), 401)
            response.headers['Content-Type'] = 'application/json'

            return response
        
        # verify that the access token is valid for this app
        if result['issued_to'] != CLIENT_ID:
            response = make_response(json.dumps("Token's client ID doesn't match app's ID"), 401)
            print "Token's client ID doesn't match match app's ID."
            response.headers['Content-Type'] = 'application/json'

            return response
            
        # check to see if the user is already logged into the system
        stored_credentials = login_session.get('credentials')
        stored_gplus_id = login_session.get('gplus_id')
        if stored_credentials is not None and gplus_id == stored_gplus_id:
            response = make_response(json.dumps("Current user is already connected."), 200)
            response.headers['Content-Type'] = 'application/json'
        
        # store the access token in the session for later use
        login_session['g_credentials'] = credentials
        login_session['credentials'] = {'access_token':access_token}
        login_session['gplus_id'] = gplus_id

        # get user info
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt':'json'}
        answer = requests.get(userinfo_url, params=params)
        data = json.loads(answer.text)


        #### DONE WITH GOOGLE STUFF needs own method combine with fbook

        login_session['email'] = data['email']
        login_session['username'] = data['name']
        login_session['picture'] = data['picture']

        # create the user if the user doesn't exist
        user = RestaurantManager.getUser(email=login_session['email'])
        if user is None:
            RestaurantManager.addUser(name=login_session['username'],
                                      email=login_session['email'],
                                      picture=login_session['picture'])
            user = RestaurantManager.getUser(email=login_session['email'])

        login_session['user_id'] = user.id
        login_session['username'] = user.name
        login_session['picture'] = user.picture

        # HTML output for successful authentication call
        output = ''
        output += '<div class="gSignIn">'
        output += '<h1>Welcome, '
        output += login_session['username']
        output += '!</h1>'
        output += '<img src="'
        output += login_session['picture']
        output += ' " style = "width: 200px; height: 200px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;">'
        output += '</div>'

        flash("you are now logged in as %s" % login_session['username'])

        return output

### ajax enpoint for facebook sign in authentication
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
        # confirm entity with correct 3rd party credentials is same entity 
        # that is trying to login from the current login page's session.
        print "connecting to facebook"

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

        # use token to get user info from API [why is this next line here?]
        userinfo_url = "https://graph.facebook.com/v2.4/me"
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

        # create the user if the user doesn't exist
        user = RestaurantManager.getUser(email=login_session['email'])
        if user is None:
            RestaurantManager.addUser(name=login_session['username'],
                                      email=login_session['email'],
                                      picture=login_session['picture'])
            user = RestaurantManager.getUser(email=login_session['email'])

        login_session['user_id'] = user.id
        # reset these to what the user has for our app
        login_session['username'] = user.name
        login_session['picture'] = user.picture

        # this is for my app checking for login status
        credentials = {'access_token':token}
        login_session['credentials'] = credentials

        # HTML output for successful authentication call
        output = ''
        output += '<div class="fbSignIn">'
        output += '<h1>Welcome, '
        output += login_session['username']
        output += '!</h1>'
        output += '<img src="'
        output += login_session['picture']
        output += ' " style = "width: 200px; height: 200px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;">'
        output += '</div>'

        flash("you are now logged in as %s" % login_session['username'])

        return output

# disconnect - logout a user that is currently logged in
@app.route('/disconnect', methods=['POST'])
def disconnect():
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
        
        logoutMessage += "Logged " + username + \
                         " out of Restaurant Manager"

        return logoutMessage

# disconnect - revoke a current user's google access token
@app.route('/gdisconnect', methods=['POST'])
def gdisconnect():
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

# disconnect - revoke a current user's fb access token
@app.route('/fbdisconnect', methods=['POST'])
def fbdisconnect():
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


### Make JSON API Endpoints

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
        baseMenuItem = RestaurantManager.getBaseMenuItem(baseMenuItem_id)
        restaurantMenuItems = RestaurantManager.\
                              getRestaurantMenuItems(baseMenuItem_id=baseMenuItem_id)

        return jsonify(BaseMenuItem=baseMenuItem.serialize,
                       RestaurantMenuItems=[i.serialize for i in restaurantMenuItems])

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

### Retrieve and post data

# create a state token to prevent request forgery
# store it in the session for later validation
@app.route('/')
@app.route('/index/')
@app.route('/login/')
def restaurantManagerIndex():
        state = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) 
                                      for x in xrange(32))
        login_session['state'] = state

        userName = None
        isAccessToken = 0
        access_token = None

        # check if logged in
        if 'credentials' in login_session:
            if 'access_token' in login_session['credentials']:
                userName = login_session['username']
                isAccessToken = 1

        return render_template("index.html",
                               state=state,
                               userName=userName,
                               isAccessToken=isAccessToken)

@app.route('/cuisines/')
def cuisines():
        cuisines = RestaurantManager.getCuisines()

        return render_template("Cuisines.html",
                               cuisines=cuisines)

@app.route('/cuisines/add/', methods=['GET', 'POST'])
def addCuisine():
        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            # not logged in

                flash("You must log in to add a cuisine")
                return redirect('/login/')

        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

            name = bleach.clean(request.form['name'])

            RestaurantManager.addCuisine(name)

            flash("Added cuisine '" + name + "' to the database!")

            return redirect(url_for('cuisines'))
        else:

            return render_template('AddCuisine.html',
                                   hiddenToken=login_session['state'])

@app.route('/cuisines/<int:cuisine_id>/')
def cuisine(cuisine_id):
        cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)
        restaurants = RestaurantManager.getRestaurants(cuisine_id=cuisine_id)
        baseMenuItems = RestaurantManager.\
                        getBaseMenuItems(cuisine_id=cuisine_id)
        restaurantMenuItems = RestaurantManager.\
                              getRestaurantMenuItems(cuisine_id=cuisine_id)

        if len(baseMenuItems) > 0:
            # also put in normal dollar format
            mostExpensiveBaseMenuItem = baseMenuItems[0]
            for item in baseMenuItems:
                if item.price > mostExpensiveBaseMenuItem.price:
                    mostExpensiveBaseMenuItem = item
            mostExpensiveBaseMenuItem.price = Decimal(mostExpensiveBaseMenuItem.price).quantize(Decimal('0.01'))
        else:
            ## got to be a better way to do this
            mostExpensiveBaseMenuItem = RestaurantManager.getBaseMenuItem(-1)
            mostExpensiveBaseMenuItem.name = "N/A"
            mostExpensiveBaseMenuItem.price = "N/A"

        if len(restaurantMenuItems) > 0:
            mostExpensiveRestaurantMenuItem = restaurantMenuItems[0]
            for item in restaurantMenuItems:
                if item.price > mostExpensiveRestaurantMenuItem.price:
                    mostExpensiveRestaurantMenuItem = item
            mostExpensiveRestaurantMenuItem.price = Decimal(mostExpensiveRestaurantMenuItem.price).quantize(Decimal('0.01'))
        else:
            ## got to be a better way to do this
            mostExpensiveRestaurantMenuItem = RestaurantManager.getBaseMenuItem(-1)
            mostExpensiveRestaurantMenuItem.name = "N/A"
            mostExpensiveRestaurantMenuItem.price = "N/A"

        return render_template("Cuisine.html",
                               cuisine=cuisine,
                               mostExpensiveBaseMenuItem=mostExpensiveBaseMenuItem,
                               mostExpensiveRestaurantMenuItem=mostExpensiveRestaurantMenuItem,
                               restaurants=restaurants,
                               baseMenuItems=baseMenuItems,
                               restaurantMenuItems=restaurantMenuItems)

@app.route('/cuisines/<int:cuisine_id>/edit/', methods=['GET', 'POST'])
def editCuisine(cuisine_id):
        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must log in to edit a cuisine")
            return redirect('/login/')

        cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)

        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

            oldName = cuisine.name
            newName = None

            if request.form['name']:
                newName = bleach.clean(request.form['name'])

            if newName is not oldName:
                RestaurantManager.editCuisine(cuisine_id, newName=newName)
                
                flash("Changed cuisine's name from '" + oldName +\
                    "' to '" + newName + "'")

            return redirect(url_for('cuisine',
                                    cuisine_id=cuisine_id))
        else:
            return render_template("EditCuisine.html",
                                   cuisine=cuisine,
                                   hiddenToken=login_session['state'])

@app.route('/cuisines/<int:cuisine_id>/delete/', methods=['GET', 'POST'])
def deleteCuisine(cuisine_id):
        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must log in to delete a cuisine")
            return redirect('/login/')

        cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)

        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

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
            itemBaseForNoCuisine = RestaurantManager.getBaseMenuItem(-1)
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
                                   hiddenToken=login_session['state'])

@app.route('/restaurants/')
def restaurants():
        restaurants = RestaurantManager.getRestaurants()
        
        return render_template("Restaurants.html",
                               restaurants=restaurants)

@app.route('/restaurants/add/', methods=['GET','POST'])
def addRestaurant():
        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must log in to add a restaurant")
            return redirect('/login/')

        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

            name = bleach.clean(request.form['name'])

            if request.form['cuisineID'] == 'custom':
                custCuisineName = bleach.clean(request.form['customCuisine'])
                RestaurantManager.addCuisine(name=custCuisineName)
                custCuisine = RestaurantManager.getCuisine(name=custCuisineName)
                cuisine_id = custCuisine.id
            else:
                cuisine_id = request.form['cuisineID']

            cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)

            picFile = request.files['pictureFile']

            if picFile:
                if allowed_file(picFile.filename):
                    picFile.filename = secure_filename(picFile.filename)
                    # because we need to store the id of the restaurant with the upload
                    picture = 'temp'
            elif request.form['pictureLink']:
                picture = bleach.clean(request.form['pictureLink'])
            else:
                picture = "[No picture provided]"

            restaurant_id = RestaurantManager.addRestaurant(
                                name=name,
                                cuisine_id=cuisine_id,
                                user_id=login_session['user_id'],
                                picture=""
                            )

            if picFile:
                picfilename = 'restaurant' + str(restaurant_id)
                picFile.save(os.path.join(app.config['UPLOAD_FOLDER'], picfilename))
                RestaurantManager.editRestaurant(restaurant_id=restaurant_id,
                                                 newPicture=picfilename)

            if request.form['cuisineID'] == 'custom':
                flash("cuisine '" + cuisine.name + "' added to the " +\
                    "database!")
            else:
                RestaurantManager.\
                    populateMenuWithBaseItems(restaurant_id)

            flash("restaurant '" + name + "' with cuisine '" + cuisine.name +\
                "' added to the database!")

            return redirect(url_for('restaurants'))
        else:

            cuisines = RestaurantManager.getCuisines()
            return render_template('AddRestaurant.html', 
                                    cuisines=cuisines,
                                    hiddenToken=login_session['state'])

@app.route('/restaurants/<int:restaurant_id>/')
def restaurant(restaurant_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)
        restaurantMenuItems = RestaurantManager.\
                              getRestaurantMenuItems(restaurant_id=restaurant_id)
        cuisine = RestaurantManager.getCuisine(cuisine_id=restaurant.cuisine_id)

        numMenuItems = len(restaurantMenuItems)

        #pictureBinary = restaurant.picture
        #picture = Image(blob=pictureBinary)
        #picture.save(filename='restaurantPicture.png')
        #pictureFile = open('restaurantPicture.png')
        #print pictureFile
        print restaurant.picture

        #pictureFile.save(os.path.join(app.config['UPLOAD_FOLDER'], pictureFile.filename))

        if numMenuItems > 0:
            mostExpensiveItem = restaurantMenuItems[0]
            for item in restaurantMenuItems:
                if item.price > mostExpensiveItem.price:
                    mostExpensiveItem = item
                    mostExpensiveItem.price = Decimal(mostExpensiveItem.price).quantize(Decimal('0.01'))
            mostExpensiveItem.price = Decimal(mostExpensiveItem.price).quantize(Decimal('0.01'))
        else:
            ## got to be a better way to do this
            mostExpensiveItem = RestaurantManager.\
                                getBaseMenuItem(baseMenuItem_id=-1)
            mostExpensiveItem.name = 'N/A'
            mostExpensiveItem.price = 'N/A'

        return render_template('Restaurant.html', 
                               restaurant=restaurant, 
                               numMenuItems=numMenuItems,
                               mostExpensiveItem=mostExpensiveItem,
                               cuisine=cuisine)

@app.route('/restaurants/<int:restaurant_id>/edit/',
           methods=['GET','POST'])
def editRestaurant(restaurant_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)
        
        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must log in to edit a restaurant")
            return redirect('/login/')
        elif restaurant.user_id != login_session['user_id']:

            flash("You do not have permission to edit this restaurant")
            return redirect('/restaurants/'+str(restaurant.id)+'/')

        restaurant = RestaurantManager.getRestaurant(restaurant_id)
        cuisines = RestaurantManager.getCuisines()
        
        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

            oldName = restaurant.name
            oldCuisine = RestaurantManager.\
                         getCuisine(cuisine_id=restaurant.cuisine_id)
            oldPicture = restaurant.picture
            newName = None
            newCuisine = None
            newCuisineID = None
            newPicture = None
            
            if request.form['name']:
                newName = bleach.clean(request.form['name'])
                
            if request.form['cuisineID'] != "noNewCuisine":
                newCuisineID = request.form['cuisineID']
                newCuisine = RestaurantManager.\
                             getCuisine(cuisine_id=newCuisineID)

            if request.form['pictureLink'] or request.form['pictureFile']:
                if request.form['pictureLink']:
                    newPicture = bleach.clean(request.form['pictureLink'])

            RestaurantManager.editRestaurant(restaurant.id,
                newName=newName, newCuisine_id=newCuisineID,
                newPicture=newPicture)

            restaruant = RestaurantManager.getRestaurant(restaurant_id)

            if newName is not None:
                flash("changed " + restaurant.name + "'s (ID " + \
                    str(restaurant.id) + ") name from '" + oldName + \
                    "' to '" + newName + "'")

            if newCuisine is not None:
                flash("changed " + restaurant.name + "'s (ID " + \
                    str(restaurant.id) + ") cuisine from '"+ \
                    oldCuisine.name + "' to '" + newCuisine.name + "'")

            if newPicture is not None:
                flash("updated " + restaurant.name + "'s picture!")
            
            return redirect(url_for('restaurant',
                                    restaurant_id=restaurant_id))
        else:

            return render_template('EditRestaurant.html',
                                   restaurant=restaurant,
                                   cuisines=cuisines,
                                   hiddenToken=login_session['state'])

@app.route('/restaurants/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)

        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must log in to delete a restaurant")
            return redirect('/login')
        elif restaurant.user_id != login_session['user_id']:

            flash("You do not have permission to delete this restaurant")
            return redirect('/restaurants/'+str(restaurant.id)+'/')

        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

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
                                   hiddenToken=login_session['state'])

@app.route('/cuisines/<int:cuisine_id>/add/', methods=['GET','POST'])
def addBaseMenuItem(cuisine_id):
        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must log in to add a base menu item")
            return redirect('/login/')

        cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)

        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

            name = bleach.clean(request.form['name'])
            description = bleach.clean(request.form['description'])
            price = bleach.clean(request.form['price'])

            RestaurantManager. addBaseMenuItem(name, cuisine_id,
                description=description, price=price)

            flash("added '" + name + "'' to " + cuisine.name + "'s base menu")

            return redirect(url_for('cuisine', cuisine_id=cuisine.id))
        else:
            return render_template('AddBaseMenuItem.html',
                                   cuisine=cuisine)

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/')
def baseMenuItem(cuisine_id, baseMenuItem_id):
        baseMenuItem = RestaurantManager.getBaseMenuItem(baseMenuItem_id)
        baseMenuItem.price = Decimal(baseMenuItem.price).quantize(Decimal('0.01'))
        cuisine = RestaurantManager.getCuisine(cuisine_id=baseMenuItem.cuisine_id)
        restaurantMenuItems = RestaurantManager.\
                              getRestaurantMenuItems(baseMenuItem_id=baseMenuItem.id)
        timesOrdered = 0

        return render_template("BaseMenuItem.html",
                                baseMenuItem=baseMenuItem,
                                restaurantMenuItems=restaurantMenuItems,
                                cuisine=cuisine,
                                timesOrdered=timesOrdered,
                                hiddenToken=login_session['state'])

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/edit/',
           methods=['POST','GET'])
def editBaseMenuItem(cuisine_id, baseMenuItem_id):
        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must log in to edit a base menu item")
            return redirect('/login/')

        baseMenuItem = RestaurantManager.\
                       getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)
        cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)

        baseMenuItem.price = Decimal(baseMenuItem.price).quantize(Decimal('0.01'))

        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

            oldName = baseMenuItem.name
            oldDescription = baseMenuItem.description
            oldPrice = baseMenuItem.price
            newName = None
            newDescription = None
            newPrice = None
            
            if request.form['name']:
                newName = bleach.clean(request.form['name'])
                
            if request.form['description']:
                newDescription = bleach.clean(request.form['description'])
                
            if request.form['price']:
                newPrice = bleach.clean(request.form['price'])

            RestaurantManager.editBaseMenuItem(baseMenuItem.id,
                newName=newName, newDescription=newDescription, newPrice=newPrice)

            if newName is not None:
                flash("changed name from '"+oldName+"' to '"+newName+"'")

            if newDescription is not None:
                flash("changed description from '"+ oldDescription + "' to '" + \
                    newDescription + "'")

            if newPrice is not None:
                flash("changed price from '" + oldPrice + "' to '" + \
                    newPrice + "'")

            return redirect(url_for('baseMenuItem',
                                    cuisine_id=cuisine_id,
                                    baseMenuItem_id=baseMenuItem_id))
        else:
            return render_template("EditBaseMenuItem.html",
                                   baseMenuItem=baseMenuItem,
                                   cuisine=cuisine,
                                   hiddenToken=login_session['state'])

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/delete/',
           methods=['GET','POST'])
def deleteBaseMenuItem(cuisine_id, baseMenuItem_id):
        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must log in to delete a base menu item")
            return redirect('/login/')

        baseMenuItem = RestaurantManager.\
                       getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)

        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

            cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)
            restaurantMenuItems = RestaurantManager.\
                                  getRestaurantMenuItems(baseMenuItem_id=baseMenuItem_id)
            baseForNoCuisine = RestaurantManager.getBaseMenuItem(-1)

            RestaurantManager.deleteBaseMenuItem(baseMenuItem_id=baseMenuItem_id)

            flash("reassigned " + str(len(restaurantMenuItems)) + \
                " restaurant menu item's base to '" +\
                baseForNoCuisine.name + "'")
            flash("deleted " + baseMenuItem.name + " from " +\
                cuisine.name + "' menu (and from the database)")

            return redirect(url_for('cuisine',cuisine_id=cuisine_id))
        else:

            return render_template("DeleteBaseMenuItem.html",
                                   baseMenuItem=baseMenuItem,
                                   cuisine_id=cuisine_id,
                                   hiddenToken=login_session['state'])

@app.route('/restaurants/<int:restaurant_id>/menu/')
def restaurantMenu(restaurant_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)
        restaurantMenuItems = RestaurantManager.\
            getRestaurantMenuItems(restaurant_id=restaurant_id)

        # display nicely formatted
        for item in restaurantMenuItems:
            item.price = Decimal(item.price).quantize(Decimal('0.01'))

        if ('credentials' in login_session and
            'access_token' in login_session['credentials'] and
            restaurant.user_id == login_session['user_id']):
    
            return render_template('PrivateRestaurantMenu.html',
                                   restaurant=restaurant,
                                   items=restaurantMenuItems)
        else:

            return render_template('PublicRestaurantMenu.html',
                                   restaurant=restaurant,
                                   items=restaurantMenuItems)

@app.route('/restaurants/<int:restaurant_id>/menu/add/',
           methods=['GET','POST'])
def addRestaurantMenuItem(restaurant_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)
        
        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must log in add an item to this restaurant's menu")
            return redirect('/login/')
        elif restaurant.user_id != login_session['user_id']:

            flash("You do not have permission to add an item to "+\
                " this restaurant's menu")
            return redirect('/restaurants/'+str(restaurant.id)+'/menu/')

        baseMenuItems = RestaurantManager.getBaseMenuItems()

        # display nicely
        for item in baseMenuItems:
            item.price = Decimal(item.price).quantize(Decimal('0.01'))

        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

            RestaurantManager.addRestaurantMenuItem(
                name=bleach.clean(request.form['name']),
                restaurant_id=restaurant_id,
                description=bleach.clean(request.form['description']),
                price=bleach.clean(request.form['price']),
                baseMenuItem_id=request.form['baseMenuItemID']
            )

            flash("menu item '" + bleach.clean(request.form['name']) + \
                "' added to the menu!")

            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
        else:

            return render_template('AddRestaurantMenuItem.html',
                                   restaurant=restaurant,
                                   baseMenuItems=baseMenuItems,
                                   hiddenToken=login_session['state'])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/')
def restaurantMenuItem(restaurant_id, restaurantMenuItem_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)

        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must be logged in to view the details for this "+\
                " restaurant menu item")
            return redirect('/login/')
        elif restaurant.user_id != login_session['user_id']:

            flash("You do not have permission to view the details for this "+\
                "restaurant menu item")
            return redirect('/restaurants/'+str(restaurant.id)+'/menu/')

        restaurantMenuItem = RestaurantManager.\
                             getRestaurantMenuItem(restaurantMenuItem_id)
        restaurantMenuItem.price = Decimal(restaurantMenuItem.price).quantize(Decimal('0.01'))

        restaurantCuisineObj = RestaurantManager.\
                               getCuisine(cuisine_id=restaurant.cuisine_id)
        restaurantCuisine = restaurantCuisineObj.name

        baseMenuItem = RestaurantManager.\
                       getBaseMenuItem(restaurantMenuItem.baseMenuItem_id)
        baseMenuItem.price = Decimal(baseMenuItem.price).quantize(Decimal('0.01'))
        baseMenuItemCuisineObj = RestaurantManager.\
                                 getCuisine(cuisine_id=baseMenuItem.cuisine_id)
        baseMenuItemCuisine = baseMenuItemCuisineObj.name

        timesOrdered = 0

        return render_template("RestaurantMenuItem.html",
                               restaurantMenuItem=restaurantMenuItem,
                               restaurant=restaurant,
                               restaurantCuisine=restaurantCuisine,
                               baseMenuItem=baseMenuItem,
                               baseMenuItemCuisine=baseMenuItemCuisine,
                               timesOrdered=timesOrdered)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/edit/',
           methods=['GET','POST'])
def editRestaurantMenuItem(restaurant_id, restaurantMenuItem_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)

        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must log in edit this restaurant's menu")
            return redirect('/login/')
        elif restaurant.user_id != login_session['user_id']:

            flash("You do not have permission to edit this "+\
                "restaurant menu item")
            return redirect('/restaurants/'+str(restaurant.id)+'/menu/')

        restaurantMenuItem = RestaurantManager.\
            getRestaurantMenuItem(restaurantMenuItem_id)

        restaurantMenuItem.price = Decimal(restaurantMenuItem.price).quantize(Decimal('0.01'))
        
        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

            oldName = restaurantMenuItem.name
            oldDescription = restaurantMenuItem.description
            oldPrice = restaurantMenuItem.price
            oldPicture = restaurantMenuItem.picture
            newName = None
            newDescription = None
            newPrice = None
            newPicture = None

            
            if request.form['name']:
                newName = bleach.clean(request.form['name'])
                
            if request.form['description']:
                newDescription = bleach.clean(request.form['description'])
                
            if request.form['price']:
                newPrice = bleach.clean(request.form['price'])

            if request.form['pictureLink'] or request.form['pictureFile']:
                if request.form['pictureLink']:
                    newPicture = bleach.clean(request.form['pictureLink'])

            RestaurantManager.editRestaurantMenuItem(restaurantMenuItem.id,
                newName=newName, newDescription=newDescription, 
                newPrice=newPrice, newPicture=newPicture)

            if newName is not None:
                flash("changed restaurant menu item " + str(restaurantMenuItem.id) + \
                    "'s name from '" + oldName + "' to '" + newName + "'")

            if newDescription is not None:
                flash("changed restaurant menu item " + str(restaurantMenuItem.id) + \
                    "'s description from '"+ oldDescription + "' to '" + \
                    newDescription + "'")

            if newPrice is not None:
                flash("changed restaurant menu item " + str(restaurantMenuItem.id) + \
                    "'s price from '" + oldPrice + "' to '" + \
                    newPrice + "'")
            
            if newPicture is not None:
                flash("updated restaurant menu item picture!")

            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
        else:

            return render_template('EditRestaurantMenuItem.html',
                                   restaurant=restaurant,
                                   restaurantMenuItem=restaurantMenuItem,
                                   hiddenToken=login_session['state'])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/delete/',
           methods=['GET','POST'])
def deleteRestaurantMenuItem(restaurant_id, restaurantMenuItem_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)

        if ('credentials' not in login_session or
            'access_token' not in login_session['credentials']):
            
            flash("You must log in delete this restaurant menu item")
            return redirect('/login/')
        elif restaurant.user_id != login_session['user_id']:

            flash("You do not have permission to delete this "+\
                "restaurant menu item")
            return redirect('/restaurants/'+str(restaurant.id)+'/menu/')

        restaurantMenuItem = RestaurantManager.\
                             getRestaurantMenuItem(restaurantMenuItem_id)

        if request.method == 'POST':

            if request.form['hiddenToken'] != login_session['state']:
                # not same entity that first came to login page
                # possible CSRF attack
                flash("An unknown error occurred.  Try signing out"+\
                    ", signing back in, and repeating the operation.")

                return redirect(url_for('login'))

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
                                   hiddenToken=login_session['state'])

# for checking picture filename input
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_PIC_EXTENSIONS

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
