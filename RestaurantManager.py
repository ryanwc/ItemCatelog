from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Restaurant, BaseMenuItem, RestaurantMenuItem, Cuisine


def populateMenuWithBaseItems(restaurant_id):
    """Add all of a restaurant's base items base on its cuisine
    """
        session = getRestaurantDBSession()

        restaurant = session.query(Restaurant).\
                     filter_by(id=restaurant_id).one()

        # do not add any menu items if the restaurant has no specific cuisine
        if restaurant.cuisine_id is -1:
            session.close()
            return

        baseMenuItems = session.query(BaseMenuItem).\
                        filter_by(id=restaurant.cuisine_id).all()
        
        for baseMenuItem in baseMenuItems:
            restaurantMenuItem = RestaurantMenuItem(name=baseMenuItem.name,
                                          description=baseMenuItem.description,
                                          price=baseMenuItem.price,
                                          baseMenuItem_id=baseMenuItem.id,
                                          restaurant_id=restaurant.id)
            session.add(restaurantMenuItem)

        session.commit()
        session.close()

def addRestaurantMenuItem(name, description=None, price=None, course=None,
                          restaurant_id, baseMenuItem_id):
    """Add an item to a restaurant's menu
    """
        session = getRestaurantDBSession()

        restaurantMenuItem = RestaurantMenuItem(name=name, 
                                                description=description,
                                                price=price, course=course,
                                                restaurant_id=restaurant_id,
                                                baseMenuItem_id=baseMenuItem_id)

        session.add(restaurantMenuItem)
        session.commit()
        session.close()

def addBaseMenuItem(name, description=None, price=None,
                    course=None, cuisine_id):
    """Add an item to a cuisine's base item list
    """
        session = getRestaurantDBSession()

        baseMenuItem = BaseMenuItem(name=name, description=description,
                                    price=price, course=course,
                                    cuisine_id=cuisine_id)

        session.commit()
        session.close()

def addCuisine(name):
    """Add a cuisine to the database
    """
        session = getRestaurantDBSession()

        cuisine = Cuisine(name=name)

        session.add(name)
        session.commit()
        session.close()

def addRestaurant(name, cuisine_id):
    """Add a restaurant to the database
    """
        session = getRestaurantDBSession()

        restaurant = Restaurant(name=name, cuisine_id=cuisine_id)

        session.add(restaurant)
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
    
    restaurants = session.query(Restaurant).order_by(Restaurant.id).all()
    
    session.close()
    return restaurants

def getRestaurant(rest_id):
    """Return the restaurant with the given ID

    Args:
      rest_id: the id of the restaurant to get
    """
    session = getRestaurantDBSession()

    restaurant = session.query(Restaurant).\
                 filter(Restaurant.id==rest_id).one()

    return restaurant

def getRestaurantMenuItems():
    """Return a list of all menu items ordered by restaurant ID
    """
    session = getRestaurantDBSession()

    menuItems = session.query(MenuItem).order_by(MenuItem.restaurant_id).all()

    session.close()
    return menuItems

def getRestaurantMenuItems(rest_id):
    """Return a list of all menu items for a specific restaurant

    Args:
        rest_id: the id of the restaurant whose menu items to get
    """
    session = getRestaurantDBSession()

    menuItems = session.query(RestaurantMenuItem).\
                filter_by(restaurant_id=rest_id).all()

    session.close()
    return menuItems

def getPopularCuisines():
    """Return a list of all cuisines offered by at least three restaurants
    """
    session = getRestaurantDBSession()

    numPerCuisine = session.query(Restaurant.foodType,
                                  func.count(Restaurant.foodType).label('No')).\
                                  group_by(Restaurant.foodType).all()
    popCuisines = []

    for cuisine in numPerCuisine:
        if cuisine.No >= 3:
            popCuisines.append(cuisine)

    session.close()
    return popCuisines

def getCuisines():
    """Return a list of all cuisines offered by at least one restaurant
    ordered by cuisine id
    """
    session = getRestaurantDBSession()

    cuisines  = session.query(Cuisine).order_by(Cuisine.id).all()

    session.close()
    return cuisines

