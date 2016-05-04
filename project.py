from flask import Flask
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/restaurants/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id)

    output = ''
    for i in items:
        output += i.name
        output += '<br>'
        output += i.description
        output += '<br>'
        output += i.price
        output += '<br><br>'
    return output

def newMenuItem(restaurant_id):
    return "page to create a new menu item"

def editMenuItem(restaurant_id, menu_id):
    return "page to edit a new menu item

def deleteMenuItem(restaurant_id, menu_id):
    return "page to delete a menu item"

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
