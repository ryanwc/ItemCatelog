from flask import Flask, render_template, request, redirect, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

import RestaurantManager

import bleach

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/restaurants/<int:restaurant_id>/menu/')
def restaurantMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id)
    
    return render_template('RestaurantMenu.html',
                           restaurant=restaurant,
                           items=items)

@app.route('/restaurants/<int:restaurant_id>/menu/add/',
           methods=['GET','POST'])
def newMenuItem(restaurant_id):
    if request.method == 'POST':
        name = bleach.clean(request.form['name'])
        description = bleach.clean(request.form['description'])
        price = bleach.clean(request.form['price'])
        newItem = MenuItem(name=name,
                           restaurant_id=restaurant_id,
                           description=description,
                           price=price)
        session.add(newItem)
        session.commit()
        flash("menu item '" + name + "' added to the menu!")
        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:
        return render_template('AddMenuItem.html',
                               restaurant_id=restaurant_id)

@app.route('/restaurants/<int:restaurant_id>/menu/edit/<int:menuItem_id>/',
           methods=['GET','POST'])
def editMenuItem(restaurant_id, menuItem_id):
        item = session.query(MenuItem).filter_by(id=menuItem_id).one()
        oldName = item.name
        oldDescription = item.description
        oldPrice = item.price
        
        if request.method == 'POST':

            changeName = False
            changeDescription = False
            changePrice = False
            
            if request.form['name']:
                newName = bleach.clean(request.form['name'])
                session.query(MenuItem).filter(MenuItem.id==menuItem_id).\
                        update({'name':newName})
                changeName = True
                
            if request.form['description']:
                newDescription = bleach.clean(request.form['description'])
                session.query(MenuItem).filter(MenuItem.id==menuItem_id).\
                        update({'description':newDescription})
                changeDescription = True
                
            if request.form['price']:
                newPrice = bleach.clean(request.form['price'])
                session.query(MenuItem).filter(MenuItem.id==menuItem_id).\
                        update({'price':newPrice})
                changePrice = True
                
            session.commit()

            if changeName:
                flash("menu item " + str(item.id) + "'s name changed from '"+\
                      oldName + "' to '" + newName + "'")

            if changeDescription:
                flash("menu item " + str(item.id) + "'s description changed "\
                      "from '"+ oldDescription + "' to '" + \
                      newDescription + "'")

            if changePrice:
                flash("menu item " + str(item.id) + "'s price changed from '"+\
                      oldPrice + "' to '" + newPrice + "'")
            
            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
        else:
            return render_template('EditMenuItem.html',
                                   restaurant_id=restaurant_id,
                                   menuItem=item)

@app.route('/restaurants/<int:restaurant_id>/menu/delete/<int:menuItem_id>/',
           methods=['GET','POST'])
def deleteMenuItem(restaurant_id, menuItem_id):
        if request.method == 'POST':
            itemToDelete = session.query(MenuItem).\
                           filter(MenuItem.id==menuItem_id).one()
            session.delete(itemToDelete)
            session.commit()
            flash("menu item " + str(itemToDelete.id) + " (" + \
                  itemToDelete.name + ") deleted from the menu and database")
            return redirect(url_for('restaurantMenu',
                                    restaurant_id=restaurant_id))
        else:
            return render_template('DeleteMenuItem.html',
                                   restaurant_id=restaurant_id,
                                   menuItem_id=menuItem_id)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
