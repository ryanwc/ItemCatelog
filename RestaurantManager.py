from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Restaurant, BaseMenuItem, RestaurantMenuItem, Cuisine


def populateMenuWithBaseItems(restaurant_id):
    """Add all of a restaurant's base items base on its cuisine
    """
    session = getRestaurantDBSession()

    restaurant = getRestaurant(restaurant_id)

    # do not add any menu items if the restaurant has no specific cuisine
    if restaurant.cuisine_id is -1:
        session.close()
        return

    baseMenuItems = session.query(BaseMenuItem).\
                    filter_by(cuisine_id=restaurant.cuisine_id).all()
        
    for baseMenuItem in baseMenuItems:
        restaurantMenuItem = RestaurantMenuItem(
                name=baseMenuItem.name,
                description=baseMenuItem.description,
                price=baseMenuItem.price,
                baseMenuItem_id=baseMenuItem.id,
                restaurant_id=restaurant.id
            )
        session.add(restaurantMenuItem)

    session.commit()
    session.close()

def addRestaurantMenuItem(name, restaurant_id, baseMenuItem_id,
                          description=None, price=None, course=None):
    """Add an item to a restaurant's menu
    """
    session = getRestaurantDBSession()

    restaurantMenuItem = RestaurantMenuItem(
            name=name,
            description=description,
            price=price,
            course=course,
            restaurant_id=restaurant_id,
            baseMenuItem_id=baseMenuItem_id
        )

    session.add(restaurantMenuItem)
    session.commit()
    session.close()

def addBaseMenuItem(name, cuisine_id,
                    description=None, price=None, course=None):
    """Add an item to a cuisine's base item list
    """
    session = getRestaurantDBSession()

    baseMenuItem = BaseMenuItem(
            name=name, 
            description=description,
            price=price,
            course=course,
            cuisine_id=cuisine_id
        )

    session.add(baseMenuItem)
    session.commit()
    session.close()

def addCuisine(name):
    """Add a cuisine to the database
    """
    session = getRestaurantDBSession()

    cuisine = Cuisine(name=name)

    session.add(cuisine)
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

    restaurant = session.query(Restaurant).filter_by(id=rest_id).one()

    return restaurant

def getRestaurantMenuItems():
    """Return a list of all menu items ordered by restaurant ID
    """
    session = getRestaurantDBSession()

    restaurantMenuItems = session.query(RestaurantMenuItem).\
                          order_by(RestaurantMenuItem.restaurant_id).all()

    session.close()
    return restaurantMenuItems

def getRestaurantMenuItems(rest_id):
    """Return a list of all menu items for a specific restaurant

    Args:
        rest_id: the id of the restaurant whose menu items to get
    """
    session = getRestaurantDBSession()

    restaurantMenuItems = session.query(RestaurantMenuItem).\
                          filter_by(restaurant_id=rest_id).all()

    session.close()
    return restaurantMenuItems

def getRestaurantMenuItem(restaurantMenuItem_id):
    """Return a restaurant menu item with the given it

    Args:
        restaurantMenuItem_id: the id of the restaurant menu item to get
    """
    session = getRestaurantDBSession()

    restaurantMenuItem = session.query(RestaurantMenuItem).\
                         filter_by(id=restaurantMenuItem_id).one()

    session.close()
    return restaurantMenuItem

def getRestaurantsWithCuisine(cuisine_id):
    """Return all restaurants with the given cuisine id

    Args:
        cuisine_id: the id of the cuisine to match
    """
    session = getRestaurantDBSession()

    restaurants = session.query(Restaurant).\
                  filter_by(cuisine_id=cuisine_id).all()

    session.close()
    return restaurants

def getBaseMenuItemsWithCuisine(cuisine_id):
    """Return all base menu items with the given cuisine id

    Args:
        cuisine_id: the id of the cuisine to match
    """
    session = getRestaurantDBSession()

    baseMenuItems = session.query(BaseMenuItem).\
                    filter_by(cuisine_id=cuisine_id).all()

    session.close()
    return baseMenuItems

def getRestaurantMenuItemsWithCuisine(cuisine_id):
    """Return all restaurant menu items with the given cuisine id

    Args:
        cuisine_id: the id of the cuisine to match
    """
    session = getRestaurantDBSession()

    restaurantMenuItems = session.query(RestaurantMenuItem).\
                          join(BaseMenuItem).\
                          filter(BaseMenuItem.cuisine_id==cuisine_id).all()

    session.close()
    return restaurantMenuItems

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

def getCuisine(cuisine_id=None, name=None):
    """Return the cuisine with the given id

    Args:
        cuisine_id: the id of the cuisine to get.
            Pass None to get by name instead.
        name: the name of the cuisine to get.  Pass None to get by id instead.
    """
    session = getRestaurantDBSession()

    if cuisine_id is not None:
        cuisine  = session.query(Cuisine).filter_by(id=cuisine_id).one()
    elif name is not None:
        cuisine = session.query(Cuisine).filter_by(name=name).one()

    session.close()
    return cuisine

def editRestaurant(restaurantMenuItem_id, newName=None, newCuisine_id=None):
    """Edit a restaurant

    Args:
        restaurant_id: the id of the restaurant to edit
        newName: a new name of the restaurant to edit.  Pass none to leave
            the name unchanged.
        newCuisine_id: the id of the restaurant's new cuisine.
            Pass None to leave the cuisine unchanged.
    """
    session = getRestaurantDBSession()

    if newName is not None:
        session.query(Restaurant).filter_by(id=restaurant_id).\
            update({'name':newName})

    if newCuisine_id is not None:
        session.query(Restaurant).filter_by(id=restaurant_id).\
            update({'cuisine_id':newCuisine_id})

    session.commit()
    session.close()

def editRestaurantMenuItem(restaurantMenuItem_id, newName=None, 
                           newDescription=None, newPrice=None,
                           newCourse=None, newRestaurant_id=None,
                           newBaseMenuItem_id=None):
    """Edit a restaurant menu item

    Args:
        restaurantMenuItem_id: the id of the restaurant menu item to edit
        newName: a new name for the restaurant menu item.
            Pass none to leave the name unchanged.
        newDescription: a new description for the restaurant menu item.
            Pass None to leave the description unchanged.
        newPrice: a new price for the restaurant menu item.
            Pass None to leave the price unchanged.
        newCourse: the restaurant menu item's new course.
            Pass None to leave the course unchanged.
        newRestaurant_id: the id of the restaurant menu item's new restaurant.
            Pass None to leave the restaurant unchanged.
        newBaseMenuItem_id: the id of the restaurant menu item's new
            base menu item. Pass None to leave the base menu item unchanged.
    """
    session = getRestaurantDBSession()

    if newName is not None:
        session.query(RestaurantMenuItem).filter_by(id=restaurantMenuItem_id).\
            update({'name':newName})

    if newDescription is not None:
        session.query(RestaurantMenuItem).filter_by(id=restaurantMenuItem_id).\
            update({'description':newDescription})

    if newPrice is not None:
        session.query(RestaurantMenuItem).filter_by(id=restaurantMenuItem_id).\
            update({'price':newPrice})

    if newCourse is not None:
        session.query(RestaurantMenuItem).filter_by(id=restaurantMenuItem_id).\
            update({'course':newCourse})

    if newRestaurant_id is not None:
        session.query(RestaurantMenuItem).filter_by(id=restaurantMenuItem_id).\
            update({'restaurant_id':newRestaurant_id})

    if newBaseMenuItem_id is not None:
        session.query(RestaurantMenuItem).filter_by(id=restaurantMenuItem_id).\
            update({'baseMenuItem_id':newBaseMenuItem_id})

    session.commit()
    session.close()

def editCuisine(cuisine_id, newName=None):
    """Edit a cuisine

    Args:
        cuisine_id: the id of the cuisine to edit
        newName: the new name of the cuisine to edit.  Pass none to leave
            the name unchanged.
    """
    session = getRestaurantDBSession()

    if newName is not None:
        session.query(Cuisine).filter_by(id=cuisine_id).\
            update({'name':newName})

    session.commit()
    session.close()

def editBaseMenuItem(baseMenuItem_id, newName=None, 
                     newDescription=None, newPrice=None,
                     newCourse=None, newCuisine_id=None):
    """Edit a base menu item

    Args:
        baseMenuItem_id: the id of the base menu item to edit
        newName: a new name for the base menu item.
            Pass none to leave the name unchanged.
        newDescription: a new description for the base menu item.
            Pass None to leave the description unchanged.
        newPrice: a new price for the base menu item.
            Pass None to leave the price unchanged.
        newCourse: the base menu item's new course.
            Pass None to leave the course unchanged.
        newCuisine_id: the id of the base menu item's new cuisine.
            Pass None to leave the cuisine unchanged.
    """
    session = getRestaurantDBSession()

    if newName is not None:
        session.query(BaseMenuItem).filter_by(id=baseMenuItem_id).\
            update({'name':newName})

    if newDescription is not None:
        session.query(BaseMenuItem).\
            filter_by(id=baseMenuItem_id).\
            update({'description':newDescription})

    if newPrice is not None:
        session.query(BaseMenuItem).filter_by(id=baseMenuItem_id).\
            update({'price':newPrice})

    if newCourse is not None:
        session.query(BaseMenuItem).filter_by(id=baseMenuItem_id).\
            update({'course':newCourse})

    if newCuisine_id is not None:
        session.query(BaseMenuItem).filter_by(id=baseMenuItem_id).\
            update({'cuisine_id':newCuisine_id})

    session.commit()
    session.close()
