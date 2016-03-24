from database_setup.py import Base, Restaruant, MenuItem

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from database_setup.py import Base, Restaurant, MenuItem


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

