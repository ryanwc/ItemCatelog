from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, BaseMenuItem, Cuisine, RestaurantMenuItem

import RestaurantManager

import bleach


### Make a API Endpoints (for GET Requests)

@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)
        restaurantMenuItems = RestaurantManager.\
            getRestaurantMenuItems(restaurant_id=restaurant_id)
        return jsonify(RestaurantMenuItems=[i.serialize for i in restaurantMenuItems])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/JSON')
def RestaurantMenuItemJSON(restaurant_id, restaurantMenuItem_id):
        restaurantMenuItem = RestaurantManager.\
            getRestaurantMenuItem(restaurantMenuItem_id)
        return jsonify(RestaurantMenuItem=restaurantMenuItem.serialize)


### Retrieve and post data

@app.route('/')
@app.route('/index/')
def restaurantManagerIndex():
        return render_template("index.html")

@app.route('/cuisines/')
def cuisines():
        cuisines = RestaurantManager.getCuisines()

        return render_template("Cuisines.html",
                               cuisines=cuisines)

@app.route('/cuisines/add/', methods=['GET', 'POST'])
def addCuisine():
        if request.method == 'POST':

            RestaurantManager.addCuisine(bleach.clean(request.form['name']))

            flash("Cuisine '" + name + "' added to the database!")

            return redirect(url_for('cuisines'))
        else:

            return render_template('AddCuisine.html')

@app.route('/cuisines/<int:cuisine_id>/')
def cuisine(cuisine_id):
        cuisine = RestaurantManager.getCuisine(cuisine_id)
        restaurants = RestaurantManager.getRestaurants(cuisine_id=cuisine_id)
        baseMenuItems = RestaurantManager.\
                        getBaseMenuItems(cuisine_id=cuisine_id)
        restaurantMenuItems = RestaurantManager.\
                              getRestaurantMenuItems(cuisine_id=cuisine_id)

        if len(baseMenuItems) > 0:
            mostExpensiveBaseMenuItem = baseMenuItems[0]
            for item in baseMenuItems:
                if item.price > mostExpensiveBaseMenuItem.price:
                    mostExpensiveBaseMenuItem = item
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

@app.route('/cuisines/<int:cuisine_id>/edit/')
def editCuisine(cuisine_id):
        return "edit cuisine " + str(cuisine_id)

@app.route('/cuisines/<int:cuisine_id>/delete/', methods=['GET', 'POST'])
def deleteCuisine(cuisine_id):
        cuisine = RestaurantManager.getCuisine(cuisine_id)

        if request.method == 'POST':

            redirect(url_for('cuisines'))
        else:
            return render_template("DeleteCuisine.html",
                                   cuisine=cuisine)

@app.route('/restaurants/')
def restaurants():
        restaurants = RestaurantManager.getRestaurants()
        
        return render_template("Restaurants.html",
                               restaurants=restaurants)

@app.route('/restaurants/add/', methods=['GET','POST'])
def addRestaurant():
        if request.method == 'POST':

            name = bleach.clean(request.form['name'])

            if request.form['cuisineID'] == 'custom':
                custCuisineName = bleach.clean(request.form['customCuisine'])
                RestaurantManager.addCuisine(name=custCuisineName)
                custCuisine = RestaurantManager.getCuisine(name=custCuisineName)
                cuisine_id = custCuisine.id
            else:
                cuisine_id = request.form['cuisineID']

            cuisine = RestaurantManager.getCuisine(cuisine_id=cuisine_id)

            RestaurantManager.addRestaurant(
                name=name,
                cuisine_id=cuisine_id
            )

            if request.form['cuisineID'] == 'custom':
                flash("cuisine '" + cuisine.name + "' added to the " +\
                    "database!")

            flash("restaurant '" + name + "' with cuisine '" + cuisine.name +\
                "' added to the database!")

            return redirect(url_for('restaurants'))
        else:

            cuisines = RestaurantManager.getCuisines()
            return render_template('AddRestaurant.html', cuisines=cuisines)

@app.route('/restaurants/<int:restaurant_id>/')
def restaurant(restaurant_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)
        restaurantMenuItems = RestaurantManager.\
                              getRestaurantMenuItems(restaurant_id=restaurant_id)
        cuisine = RestaurantManager.getCuisine(restaurant.cuisine_id)

        numMenuItems = len(restaurantMenuItems)

        if numMenuItems > 0:
            mostExpensiveItem = restaurantMenuItems[0]
            for item in restaurantMenuItems:
                if item.price > mostExpensiveItem.price:
                    mostExpensiveItem = item
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
        cuisines = RestaurantManager.getCuisines()
        
        if request.method == 'POST':

            oldName = restaurant.name
            oldCuisine = RestaurantManager.\
                         getCuisine(cuisine_id=restaurant.cuisine_id)
            newName = None
            newCuisine = None
            newCuisineID = None
            
            if request.form['name']:
                newName = bleach.clean(request.form['name'])
                
            if request.form['cuisineID'] != "noNewCuisine":
                print "it was not -2"
                newCuisineID = request.form['cuisineID']
                newCuisine = RestaurantManager.\
                             getCuisine(cuisine_id=newCuisineID)

            RestaurantManager.editRestaurant(restaurant.id,
                newName=newName, newCuisine_id=newCuisineID)

            restaruant = RestaurantManager.getRestaurant(restaurant_id)

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
                                   cuisines=cuisines)

@app.route('/restaurants/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)

        if request.method == 'POST':

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
                                   restaurant=restaurant)

@app.route('/cuisines/<int:cuisine_id>/add/', methods=['GET','POST'])
def addBaseMenuItem(cuisine_id):
        cuisine = RestaurantManager.getCuisine(cuisine_id)

        if request.method == 'POST':

            name = bleach.clean(request.form['name'])
            description = bleach.clean(request.form['description'])
            price = bleach.clean(request.form['price'])

            RestaurantManager. addBaseMenuItem(name, cuisine_id,
                description=description, price=price)

            flash("added " + name + " to " + cuisine.name + "'s base menu")

            return redirect(url_for('cuisine', cuisine_id=cuisine.id))
        else:
            return render_template('AddBaseMenuItem.html',
                                   cuisine=cuisine)

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/')
def baseMenuItem(cuisine_id, baseMenuItem_id):
        baseMenuItem = RestaurantManager.getBaseMenuItem(baseMenuItem_id)
        cuisine = RestaurantManager.getCuisine(baseMenuItem.cuisine_id)
        restaurantMenuItems = RestaurantManager.\
                              getRestaurantMenuItems(baseMenuItem_id=baseMenuItem.id)
        timesOrdered = 0

        return render_template("BaseMenuItem.html",
                                baseMenuItem=baseMenuItem,
                                restaurantMenuItems=restaurantMenuItems,
                                cuisine=cuisine,
                                timesOrdered=timesOrdered)

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/edit/',
           methods=['POST','GET'])
def editBaseMenuItem(cuisine_id, baseMenuItem_id):
        baseMenuItem = RestaurantManager.\
                       getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)

        if request.method == 'POST':

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
                                   cuisine_id=cuisine_id)

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/delete/',
           methods=['GET','POST'])
def deleteBaseMenuItem(cuisine_id, baseMenuItem_id):
        baseMenuItem = RestaurantManager.\
                       getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)

        if request.method == 'POST':

            cuisine = RestaurantManager.getCuisine(cuisine_id)
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
                                   cuisine_id=cuisine_id)

@app.route('/restaurants/<int:restaurant_id>/menu/')
def restaurantMenu(restaurant_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)
        restaurantMenuItems = RestaurantManager.\
            getRestaurantMenuItems(restaurant_id=restaurant_id)

        return render_template('RestaurantMenu.html',
                               restaurant=restaurant,
                               items=restaurantMenuItems)

@app.route('/restaurants/<int:restaurant_id>/menu/add/',
           methods=['GET','POST'])
def addRestaurantMenuItem(restaurant_id):
        restaurant = RestaurantManager.getRestaurant(restaurant_id)
        baseMenuItems = RestaurantManager.getBaseMenuItems()

        if request.method == 'POST':

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
                                   baseMenuItems=baseMenuItems)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/')
def restaurantMenuItem(restaurant_id, restaurantMenuItem_id):
        restaurantMenuItem = RestaurantManager.\
                             getRestaurantMenuItem(restaurantMenuItem_id)

        restaurant = RestaurantManager.getRestaurant(restaurant_id)
        restaurantCuisineObj = RestaurantManager.getCuisine(restaurant.cuisine_id)
        restaurantCuisine = restaurantCuisineObj.name

        baseMenuItem = RestaurantManager.\
                       getBaseMenuItem(restaurantMenuItem.baseMenuItem_id)
        baseMenuItemCuisineObj = RestaurantManager.\
                                 getCuisine(baseMenuItem.cuisine_id)
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

        restaurantMenuItem = RestaurantManager.\
            getRestaurantMenuItem(restaurantMenuItem_id)
        
        if request.method == 'POST':

            oldName = restaurantMenuItem.name
            oldDescription = restaurantMenuItem.description
            oldPrice = restaurantMenuItem.price
            newName = None
            newDescription = None
            newPrice = None
            
            if request.form['name']:
                newName = bleach.clean(request.form['name'])
                
            if request.form['description']:
                newDescription = bleach.clean(request.form['description'])
                
            if request.form['price']:
                newPrice = bleach.clean(request.form['price'])

            RestaurantManager.editRestaurantMenuItem(restaurantMenuItem.id,
                newName=newName, newDescription=newDescription, newPrice=newPrice)

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
            
            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
        else:

            return render_template('EditRestaurantMenuItem.html',
                                   restaurant_id=restaurant_id,
                                   restaurantMenuItem=restaurantMenuItem)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/delete/',
           methods=['GET','POST'])
def deleteRestaurantMenuItem(restaurant_id, restaurantMenuItem_id):

        restaurantMenuItem = RestaurantManager.\
                             getRestaurantMenuItem(restaurantMenuItem_id)

        if request.method == 'POST':

            restaurantMenuItemName = restaurantMenuItem.name

            RestaurantManager.\
                deleteRestaurantMenuItem(restaurantMenuItem_id=restaurantMenuItem_id)

            flash("removed item " + str(restaurantMenuItem_id) + " (" + \
                  restaurantMenuItemName + ") from the menu and database")

            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
        else:
            return render_template('DeleteRestaurantMenuItem.html',
                                   restaurant_id=restaurant_id,
                                   restaurantMenuItem=restaurantMenuItem)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
