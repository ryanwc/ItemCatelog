from flask import Blueprint, jsonify, send_from_directory
from restaurantmanager import DataManager, app

api_bp = Blueprint('api', __name__)

###
### picture serve endpoint
### 

@app.route(app.config['UPLOAD_FOLDER']+'/<filename>/')
def uploaded_picture(filename):
    '''Serve an uploaded picture
    '''
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename) 

###
### json endpoints
### 

@app.route('/menu_sections/JSON/')
def menuSectionsJSON():
    '''JSON endpoint for menu sections
    '''
    menuSections = DataManager.getMenuSections()

    return jsonify(MenuSections=[i.serialize for i in menuSections])

@app.route('/users/JSON/')
def usersJSON():
    '''JSON endpoint for all users
    '''
    users = DataManager.getUsers()

    return jsonify(Users=[i.serialize for i in users])

@app.route('/users/<int:user_id>/JSON/')
def userJSON(user_id):
    '''JSON endpoint for a single user
    '''
    user = DataManager.getUser(user_id)

    return jsonify(User=user.serialize)

@app.route('/cuisines/JSON/')
def cuisinesJSON():
    '''JSON endpoint for all cuisines
    '''
    cuisines = DataManager.getCuisines()

    return jsonify(Cuisines=[i.serialize for i in cuisines])

@app.route('/cuisines/<int:cuisine_id>/JSON/')
def cuisineJSON(cuisine_id):
    '''JSON endpoint for a single cuisine

    Includes all restaurants with that cuisine, all base menu items
    for that cuisine, and all restaurant menu items based on that cuisine
    '''
    cuisine = DataManager.getCuisine(cuisine_id=cuisine_id)
    baseMenuItems = DataManager.getBaseMenuItems(cuisine_id=cuisine_id)
    restaurants = DataManager.getRestaurants(cuisine_id=cuisine_id)
    restaurantMenuItems = DataManager.\
                          getRestaurantMenuItems(cuisine_id=cuisine_id)

    return jsonify(Cuisine=cuisine.serialize,
                   BaseMenuItems=[i.serialize for i in baseMenuItems],
                   Restaurants=[i.serialize for i in restaurants],
                   RestaurantMenuItems=\
                    [i.serialize for i in restaurantMenuItems])

@app.route('/base_menu_items/<int:baseMenuItem_id>/JSON/')
def baseMenuItemJSON(baseMenuItem_id):
    '''JSON endpoint for a single base menu item
    '''
    baseMenuItem = DataManager.\
        getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)
    restaurantMenuItems = DataManager.\
        getRestaurantMenuItems(baseMenuItem_id=baseMenuItem_id)

    return jsonify(BaseMenuItem=baseMenuItem.serialize,
        RestaurantMenuItems=[i.serialize for i in restaurantMenuItems])

@app.route('/base_menu_items/JSON/')
def baseMenuItemsJSON():
    '''JSON endpoint for all base menu items
    '''
    baseMenuItems = DataManager.getBaseMenuItems()

    return jsonify(BaseMenuItems=[i.serialize for i in baseMenuItems])

@app.route('/restaurants/JSON/')
def restaurantsJSON():
    '''JSON endpoint for all restaurants
    '''
    restaurants = DataManager.getRestaurants()

    return jsonify(Restaurants=[i.serialize for i in restaurants])

@app.route('/restaurants/<int:restaurant_id>/JSON/')
def restaurantJSON(restaurant_id):
    '''JSON endpoint for a single restaurant

    Includes all of the restaurant's menu items
    '''
    restaurant = DataManager.getRestaurant(restaurant_id)

    restaurantMenuItems = DataManager.\
        getRestaurantMenuItems(restaurant_id=restaurant_id)

    return jsonify(Restaurant=restaurant.serialize,
        RestaurantMenuItems=[i.serialize for i in restaurantMenuItems])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/JSON/')
def restaurantMenuItemJSON(restaurant_id, restaurantMenuItem_id):
    '''JSON endpoint for a single restaurant menu item
    '''
    restaurantMenuItem = DataManager.\
        getRestaurantMenuItem(restaurantMenuItem_id)

    return jsonify(RestaurantMenuItem=restaurantMenuItem.serialize)

@app.route('/restaurant_menu_items/JSON/')
def allRestaurantMenuItemsJSON():
    '''JSON endpoint for all restaurant menu items
    '''
    restaurantMenuItems = DataManager.getRestaurantMenuItems()

    return jsonify(RestaurantMenuItems=\
        [i.serialize for i in restaurantMenuItems])

@app.route('/pics/JSON/')
def picturesJSON():
    '''JSON endpoint for all pictures
    '''
    pictures = DataManager.getPictures()

    return jsonify(Pictures=[i.serialize for i in pictures])

@app.route('/pics/<int:picture_id>/JSON/')
def pictureJSON(picture_id):
    '''JSON endpoint for a single picture
    '''
    picture = DataManager.getPicture(picture_id)

    return jsonify(Picture=picture.serialize)

