from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Restaurant, BaseMenuItem, RestaurantMenuItem, Cuisine


def populateMenuWithBaseItems(restaurant_id):
        session = getRestaurantDBSession()

        restaurant = session.query(Restaurant).\
                     filter_by(id=restaurant_id).one()

        # do not add any menu items if the restaurant has no specific cuisine
        if restaurant.cuisine_id is -1:
            session.close()
            return

        baseMenuItems = session.query(BaseMenuItem).\
                        filter_by(id=restaurant.cuisine_id)
        
        for baseMenuItem in baseMenuItems:
            restaurantMenuItem = RestaurantMenuItem(name=baseMenuItem.name,
                                          description=baseMenuItem.description,
                                          price=baseMenuItem.price,
                                          baseMenuItem_id=baseMenuItem.id,
                                          restaurant_id=restaurant.id)
            session.add(restaurantMenuItem)

        session.commit()
        session.close()


def getRestaurantDBSession():
    """Return an interactive session with the restaurant menu database
    """
    engine = create_engine('sqlite:///restaurants.db')
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

def getRestaurant(rest_id):
    """Return the restaurant with the given ID

    Args:
      rest_id: the id of the restaurant to get
    """
    session = getRestaurantDBSession()

    restaurant = session.query(Restaurant).\
                 filter(Restaurant.id==rest_id).first()

    return restaurant

def getMenuItems():
    """Return a list of all menu items ordered by restaurant ID
    """
    session = getRestaurantDBSession()

    menuItems = session.query(MenuItem).order_by(MenuItem.restaurant_id)

    session.close()
    return menuItems

def getMenuItems(rest_id):
    """Return a list of all menu items for a specific restaurant

    Args:
        rest_id: the id of the restaurant whose menu items to get
    """
    session = getRestaurantDBSession()

    menuItems = session.query(MenuItem).filter_by(restaurant_id=rest_id)

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
