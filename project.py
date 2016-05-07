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
        session = RestaurantManager.getRestaurantDBSession()
        restaurant = RestaurantManager.getRestaurant(restaurant_id)
        items = session.query(RestaurantMenuItem).filter_by(restaurant_id=restaurant_id)
        session.close()
        return jsonify(RestaurantMenuItems=[i.serialize for i in items])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/JSON')
def RestaurantMenuItemJSON(restaurant_id, restaurantMenuItem_id):
        session = RestaurantManager.getRestaurantDBSession()
        item = session.query(RestaurantMenuItem).filter_by(id=restaurantMenuItem_id).one()
        session.close()
        return jsonify(RestaurantMenuItem=item.serialize)


### Retrieve and post data

@app.route('/')
@app.route('/index/')
def restaurantManagerIndex():
        return render_template("index.html")

@app.route('/cuisines/')
def cuisines():
        session = RestaurantManager.getRestaurantDBSession()
        cuisines = session.query(Cuisine).all()
        session.close()
        return render_template("Cuisines.html",
                               cuisines=cuisines)

@app.route('/cuisines/add/')
def addCuisine():
        return render_template('AddCuisine.html')

@app.route('/cuisines/<int:cuisine_id>/')
def cuisine(cuisine_id):
        return "cuisine " + str(cuisine_id)

@app.route('/cuisines/<int:cuisine_id>/edit/')
def editCuisine(cuisine_id):
        return "edit cuisine " + str(cuisine_id)

@app.route('/cuisines/<int:cuisine_id>/delete/')
def deleteCuisine(cuisine_id):
        return "delete cuisine " + str(cuisine_id)

@app.route('/restaurants/')
def restaurants():
        restaurants = RestaurantManager.getRestaurants()
        
        return render_template("Restaurants.html",
                               restaurants=restaurants)

@app.route('/restaurants/add/', methods=['GET','POST'])
def addRestaurant():
        if request.method == 'POST':

            if request.form['cuisineID'] == 'custom':
                cuisineName = bleach.clean(request.form['customCuisine'])
                RestaurantManager.addCuisine(name=name)
                custCuisine = RestaurantManager.getCuisine(cuisineName)
                cuisine_id = custCuisine.id
            else:
                cuisine_id = request.form['cuisineID']

            RestaurantManager.addRestaurant(
                name=bleach.clean(request.form['name']),
                cuisine_id=cuisine_id
            )

            flash("restaurant '" + name + "' with cuisine '" + cuisineName +\
                "' added to the database!")

            return redirect(url_for('Restaurants.html'))
        else:

            cuisines = RestaurantManager.getCuisines()
            return render_template('AddRestaurant.html', cuisines=cuisines)

@app.route('/restaurants/<int:restaurant_id>/')
def restaurant(restaurant_id):
        return "restaurant " + str(restaurant_id)

@app.route('/restaurants/<int:restaurant_id>/edit/')
def editRestaurant(restaurant_id):
        return "edit restaurant " + str(restaurant_id)

@app.route('/restaurants/<int:restaurant_id>/delete/')
def deleteRestaurant(restaurant_id):
        return "delete restaurant " + str(restaurant_id)

@app.route('/baseMenuItems/')
def baseMenuItems():
        return "base menu item list"

@app.route('/baseMenuItems/add/')
def addBaseMenuItem():
        return "add a base menu item"

@app.route('/baseMenuItems/<int:baseMenuItem_id>/')
def baseMenuItem(baseMenuItem_id):
        return "base menu item " + str(baseMenuItem_id)

@app.route('/baseMenuItems/<int:baseMenuItem_id>/edit/')
def editBaseMenuItem(baseMenuItem_id):
        return "edit menu item " + str(baseMenuItem_id)

@app.route('/baseMenuItems/<int:baseMenuItem_id>/delete/')
def deleteBaseMenuItem(baseMenuItem_id):
        return "delete base menu item " + str(baseMenuItem_id)

@app.route('/restaurants/<int:restaurant_id>/menu/')
def restaurantMenu(restaurant_id):
        session = RestaurantManager.getRestaurantDBSession()
        restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        items = session.query(RestaurantMenuItem).filter_by(restaurant_id=restaurant_id)
        session.close()
        return render_template('RestaurantMenu.html',
                               restaurant=restaurant,
                               items=items)

@app.route('/restaurants/<int:restaurant_id>/menu/add/',
           methods=['GET','POST'])
def addRestaurantMenuItem(restaurant_id):
        if request.method == 'POST':

            RestaurantManager.addRestaurantMenuItem(
                name=bleach.clean(request.form['name']),
                restaurant_id=restaurant_id,
                description=bleach.clean(request.form['description']),
                price=bleach.clean(request.form['price'])
            )

            flash("menu item '" + name + "' added to the menu!")

            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
        else:

            return render_template('AddRestaurantMenuItem.html',
                                   restaurant_id=restaurant_id)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/')
def restaurantMenuItem(restaurant_id, restaurantMenuItem_id):
        return "item " + str(restaurantMenuItem_id) + " at " +\
            str(restaurant_id)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/edit/',
           methods=['GET','POST'])
def editRestaurantMenuItem(restaurant_id, restaurantMenuItem_id):
        session = RestaurantManager.getRestaurantDBSession()

        item = session.query(RestaurantMenuItem).filter_by(id=restaurnatMenuItem_id).one()
        oldName = item.name
        oldDescription = item.description
        oldPrice = item.price
        
        if request.method == 'POST':

            changeName = False
            changeDescription = False
            changePrice = False
            
            if request.form['name']:
                newName = bleach.clean(request.form['name'])
                session.query(RestaurantMenuItem).filter(RestaurantMenuItem.id==restaurantMenuItem_id).\
                        update({'name':newName})
                changeName = True
                
            if request.form['description']:
                newDescription = bleach.clean(request.form['description'])
                session.query(RestaurantMenuItem).filter(RestaurantMenuItem.id==restaurantMenuItem_id).\
                        update({'description':newDescription})
                changeDescription = True
                
            if request.form['price']:
                newPrice = bleach.clean(request.form['price'])
                session.query(RestaurantMenuItem).filter(RestaurantMenuItem.id==restaurantMenuItem_id).\
                        update({'price':newPrice})
                changePrice = True
                
            session.commit()

            if changeName:
                flash("restaurant menu item " + str(item.id) + "'s name changed from '"+\
                      oldName + "' to '" + newName + "'")

            if changeDescription:
                flash("restaurant menu item " + str(item.id) + "'s description changed "\
                      "from '"+ oldDescription + "' to '" + \
                      newDescription + "'")

            if changePrice:
                flash("restaurant menu item " + str(item.id) + "'s price changed from '"+\
                      oldPrice + "' to '" + newPrice + "'")

            session.close()
            
            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
        else:

            session.close()
            return render_template('EditRestaurantMenuItem.html',
                                   restaurant_id=restaurant_id,
                                   restaurantMenuItem=item)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/delete/',
           methods=['GET','POST'])
def deleteRestaurantMenuItem(restaurant_id, restaurantMenuItem_id):
        if request.method == 'POST':

            session = session.getRestaurantDBSession()

            itemToDelete = session.query(RestaurantMenuItem).\
                           filter(RestaurantMenuItem.id==RestaurantMenuItem_id).one()
            session.delete(itemToDelete)
            session.commit()
            session.close()
            flash("menu item " + str(itemToDelete.id) + " (" + \
                  itemToDelete.name + ") deleted from the menu and database")
            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
        else:
            return render_template('DeleteRestaurantMenuItem.html',
                                   restaurant_id=restaurant_id,
                                   restaurantMenuItem_id=restaurantMenuItem_id)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
