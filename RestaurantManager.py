from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Restaurant, MenuItem


def getRestaurantDBSession():
    """Return an interactive session with the restaurant menu database
    """
    engine = create_engine('sqlite:///restaurantmenu.db')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session

def getRestaurants():
    """Return a list of all restaurants ordered by ID
    """
    session = getRestaurantDBSession()
    
    restaurants = session.query(Restaurant).order_by(Restaurant.id)
    
    session.close()
    return restaurants

def getMenuItems():
    """Return a list of all menu items ordered by restaurant ID
    """
    session = getRestaurantDBSession()

    menuItems = session.query(MenuItem).order_by(MenuItem.restaurant_id)

    session.close()
    return menuItems

def getPopularCuisines():
    """Return a list of all cuisines offered by at least three restaurants
    """
    session = getRestaurantDBSession()

    numPerCuisine = session.query(Restaurant.foodType,
                                  func.count(Restaurant.foodType).label('No')).\
                                  group_by(Restaurant.foodType)
    popCuisines = []

    for cuisine in numPerCuisine:
        if cuisine.No >= 3:
            popCuisines.append(cuisine)

    session.close()
    return popCuisines

    
