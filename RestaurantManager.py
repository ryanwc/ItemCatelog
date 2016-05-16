from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

import traceback
from decimal import *

import requests

import os

from database_setup import Base, Restaurant, BaseMenuItem, RestaurantMenuItem, Cuisine, User, MenuSection, Picture


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
        addRestaurantMenuItem(restaurant_id=restaurant.id,
            baseMenuItem_id=baseMenuItem.id)

    session.close()

def addPicture(text, serve_type):
    """Add a picture to the database

    serve_type is a binary that takes the value "upload" or "link"
    to indicate whether the picture was provided via upload or link

    Returns the user id
    """
    session = getRestaurantDBSession()

    picture = Picture(text=text, serve_type=serve_type)

    session.add(picture)
    session.flush()
    picture_id = picture.id
    session.commit()
    session.close()

    return picture_id

def addUser(name, email, picture_id):
    """Add a user to the database

    Returns the user id
    """
    session = getRestaurantDBSession()

    user = User(name=name, email=email, picture_id=picture_id)

    session.add(user)
    session.flush()
    user_id = user.id
    session.commit()
    session.close()

    return user_id

def addMenuSection(name):
    """Add a menu section to the database

    Returns the menu section id
    """
    session = getRestaurantDBSession()

    menuSection = MenuSection(name=name)

    session.add(menuSection)
    session.flush()
    menuSection_id = menuSection.id
    session.commit()
    session.close()

    return menuSection_id

def addRestaurantMenuItem(restaurant_id, baseMenuItem_id,
                          name=None, description=None, price=None, 
                          picture_id=None, menuSection_id=None):
    """Add an item to a restaurant's menu

    Returns the id of the restaurant menu item
    """
    session = getRestaurantDBSession()

    baseMenuItem = getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)

    if name is None:
        name = baseMenuItem.name

    if description is None:
        description = baseMenuItem.description

    if price is None:
        price = baseMenuItem.price

    if menuSection_id is None:
        menuSection_id = baseMenuItem.menuSection_id

    if picture_id is None:
        picture_id = baseMenuItem.picture_id

    restaurantMenuItem = RestaurantMenuItem(
            name=name,
            description=description,
            price=Decimal(price).quantize(Decimal('0.01')),
            picture_id=picture_id,
            menuSection_id=menuSection_id,
            restaurant_id=restaurant_id,
            baseMenuItem_id=baseMenuItem_id
        )

    session.add(restaurantMenuItem)
    session.flush()
    restaurantMenuItem_id = restaurantMenuItem.id
    session.commit()
    session.close()

    return restaurantMenuItem_id

def addBaseMenuItem(name, cuisine_id, description, 
                    price, menuSection_id, picture_id):
    """Add an item to a cuisine's base item list

    Returns the id of the base menu item
    """
    session = getRestaurantDBSession()

    baseMenuItem = BaseMenuItem(
            name=name, 
            description=description,
            price=Decimal(price).quantize(Decimal('0.01')),
            cuisine_id=cuisine_id,
            menuSection_id=menuSection_id,
            picture_id=picture_id
        )

    session.add(baseMenuItem)
    session.flush()
    baseMenuItem_id = baseMenuItem.id
    session.commit()
    session.close()

    return baseMenuItem_id

def addCuisine(name):
    """Add a cuisine to the database

    Returns the id of the cuisine
    """
    session = getRestaurantDBSession()

    cuisine = Cuisine(name=name)

    session.add(cuisine)
    session.flush()
    cuisine_id = cuisine.id
    session.commit()
    session.close()

    return cuisine_id

def addRestaurant(name, cuisine_id, user_id, picture_id):
    """Add a restaurant to the database

    Returns the id of the restaurant
    """
    session = getRestaurantDBSession()

    restaurant = Restaurant(name=name, cuisine_id=cuisine_id, 
                            user_id=user_id, picture_id=picture_id)
    session.add(restaurant)
    session.flush()
    restaurant_id = restaurant.id
    session.commit()
    session.close()

    return restaurant_id

def getRestaurantDBSession():
    """Return an interactive session with the restaurant menu database
    """
    engine = create_engine('sqlite:///restaurants.db')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session

def getPicture(picture_id):
    """Return the picture with the given ID

    Args:
      picture_id: the id of the picture to get
    """
    session = getRestaurantDBSession()

    picture = session.query(Picture).filter_by(id=picture_id).first()

    session.close()
    return picture

def getUser(user_id=None, email=None):
    """Return the user with the given ID or email

    Args:
      user_id: the id of the user to get
      email: the email of the user to get
    """
    session = getRestaurantDBSession()

    if user_id is not None:
        user = session.query(User).filter_by(id=user_id).first()
    elif email is not None:
        user = session.query(User).filter_by(email=email).first()

    session.close()
    return user

def getUsers():
    """Return a list of all users ordered by id
    """
    session = getRestaurantDBSession()

    users = session.query(User).order_by(User.id).all()

    session.close()
    return users

def getMenuSection(menuSection_id=None, name=None):
    """Return the menu section with the given ID or name

    Args:
      menuSection_id: the id of the menu section to get
      name: the name of the menu section to get
    """
    session = getRestaurantDBSession()

    if menuSection_id is not None:
        menuSection = session.query(MenuSection).\
                      filter_by(id=menuSection_id).first()
    elif name is not None:
        menuSection = session.query(MenuSection).\
                      filter_by(name=name).first()

    session.close()
    return menuSection

def getMenuSections():
    """Return a list of all menu sections ordered by id
    """
    session = getRestaurantDBSession()

    menuSections = session.query(MenuSection).\
                   order_by(MenuSection.id).all()

    session.close()
    return menuSections

def getRestaurants(cuisine_id=None):
    """If no arguments are given, return a list of all restaurants 
    ordered by ID.  Otherwise, return a list of all restaurants that match
    the given argument.

    Args:
        cuisine_id: the id of the cuisine to match
    """
    session = getRestaurantDBSession()
    
    if cuisine_id is not None:
        restaurants = session.query(Restaurant).\
                      filter_by(cuisine_id=cuisine_id).all()
    else:
        restaurants = session.query(Restaurant).\
                      order_by(Restaurant.id).all()
    
    session.close()
    return restaurants

def getRestaurant(rest_id):
    """Return the restaurant with the given ID

    Args:
      rest_id: the id of the restaurant to get
    """
    session = getRestaurantDBSession()

    restaurant = session.query(Restaurant).\
                 filter_by(id=rest_id).first()

    session.close()
    return restaurant

def getRestaurantMenuItems(restaurant_id=None, baseMenuItem_id=None,
                           cuisine_id=None):
    """If no arguments are given, return a list of all menu items ordered 
    by restaurant ID.  Otherwise, return a list of all menu items that match 
    the argument given.

    NOTE: Exactly zero or one argument should be given.

    Args:
        restaurant_id: the id of the restaurant whose menu items to get
            Pass None to match by another id.
        baseMenuItem_id: the id of the base menu item whose menu items to get
            Pass None to match by another id.
        cuisine_id: the id of the cuisine to whose menu items to get
            Pass None to match by another id.
    """
    session = getRestaurantDBSession()

    if restaurant_id is not None:
        restaurantMenuItems = session.query(RestaurantMenuItem).\
                              filter_by(restaurant_id=restaurant_id).all()
    elif baseMenuItem_id is not None:
        restaurantMenuItems = session.query(RestaurantMenuItem).\
                              filter_by(baseMenuItem_id=baseMenuItem_id).\
                              all()
    elif cuisine_id is not None:
        restaurantMenuItems = session.query(RestaurantMenuItem).\
                              join(BaseMenuItem).\
                              filter(BaseMenuItem.cuisine_id==cuisine_id).\
                              all()
    else:
        restaurantMenuItems = session.query(RestaurantMenuItem).\
                              order_by(RestaurantMenuItem.restaurant_id).\
                              all()

    session.close()
    return restaurantMenuItems

def getRestaurantMenuItem(restaurantMenuItem_id):
    """Return a restaurant menu item with the given id

    Args:
        restaurantMenuItem_id: the id of the restaurant menu item to get
    """
    session = getRestaurantDBSession()

    restaurantMenuItem = session.query(RestaurantMenuItem).\
                         filter_by(id=restaurantMenuItem_id).first()

    session.close()
    return restaurantMenuItem

def getBaseMenuItem(baseMenuItem_id):
    """Return the base menu item with the given id

    Args:
        baseMenuItem_id: the id of the base menu item to get
    """
    session = getRestaurantDBSession()

    baseMenuItem = session.query(BaseMenuItem).\
                   filter_by(id=baseMenuItem_id).first()

    session.close()
    return baseMenuItem

def getBaseMenuItems(cuisine_id=None, byMenuSection=False):
    """If cuisie_id is none and byMenuSection is false, 
        return all base menu items ordered by id.
    If cuisine_id is none and byMenuSection is true, 
        return a dictionary of 'menu section':[list of all items].
    If cuisine_id is given and byMenuSection is False, 
         return the base menu items for the given cuisine.
    If cuisine_id is given and byMenuSection is True,
        return a dictionary of 'menu section':[list of given cuisine's items].

    Args:
        cuisine_id: the id of the cuisine to match
    """
    session = getRestaurantDBSession()

    if cuisine_id is not None:

        if not byMenuSection:

            baseMenuItems = session.query(BaseMenuItem).\
                            filter_by(cuisine_id=cuisine_id).all()
        else:

            menuSections = getMenuSections()
            baseMenuItemList = session.query(BaseMenuItem).\
                               filter_by(cuisine_id=cuisine_id).all()

            baseMenuItems = {}

            for menuSection in menuSections:
                baseMenuItems[menuSection.name] = []
            for baseMenuItem in baseMenuItemList:
                menuSection = getMenuSection(menuSection_id=baseMenuItem.menuSection_id)
                baseMenuItems[menuSection.name].append(baseMenuItem)
    else:
        if not byMenuSection:

            baseMenuItems = session.query(BaseMenuItem).\
                            order_by(BaseMenuItem.id).all()
        else:

            baseMenuItems = {}

            menuSections = getMenuSections()
            baseMenuItemList = session.query(BaseMenuItem).all()

            for menuSection in menuSections:
                baseMenuItems[menuSection.name] = []
            for baseMenuItem in baseMenuItemList:
                menuSection = getMenuSection(menuSection_id=baseMenuItem.menuSection_id)
                baseMenuItems[menuSection.name].append(baseMenuItem)

    session.close()
    return baseMenuItems

def getCuisines(onlyPopular=False):
    """If onlyPopular is false, return a list of all cuisines offered by at 
    least one restaurant ordered by cuisine id.  Otherwise, return a list
    of all cuisines offered by more than three restaurants.

    Args:
        onlyPopular: boolean indicating whether to return all or a subset
        of restaurants.
    """
    session = getRestaurantDBSession()

    if onlyPopular:
        numPerCuisine = session.query(Restaurant.foodType,
                        func.count(Restaurant.foodType).label('No')).\
                        group_by(Restaurant.foodType).all()
        cuisines = []

        for cuisine in numPerCuisine:
            if cuisine.No > 3:
                cuisines.append(cuisine)
    else:
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
        cuisine  = session.query(Cuisine).filter_by(id=cuisine_id).first()
    elif name is not None:
        cuisine = session.query(Cuisine).filter_by(name=name).first()

    session.close()
    return cuisine

def editPicture(picture_id, newText=None, newServe_Type=None):
    """Edit a picture

    Pass none for any attribute to leave it unchanged.

    Args:
        picture_id: the id of the picture to edit
        newText: the new text that describes a link or a file name
        newServe_Type: the new serve style for the picture on this server.
            Must be 'link' or 'upload'.
    """
    session = getRestaurantDBSession()

    if newText is not None:
        session.query(Picture).filter_by(id=picture_id).\
            update({'text':newText})

    if newServe_Type is not None:
        session.query(Picture).filter_by(id=picture_id).\
            update({'serve_type':newServe_Type})  

    session.commit()
    session.close()

def editRestaurant(restaurant_id, newName=None, 
                   newCuisine_id=None, newPicture_id=None):
    """Edit a restaurant

    Pass none for any attribute to leave it unchanged.

    Args:
        restaurant_id: the id of the restaurant to edit
        newName: a new name of the restaurant to edit
        newCuisine_id: the id of the restaurant's new cuisine
        newPicture_id: the id of the new picture for the restaurant
    """
    session = getRestaurantDBSession()

    if newName is not None:
        session.query(Restaurant).filter_by(id=restaurant_id).\
            update({'name':newName})

    if newCuisine_id is not None:
        session.query(Restaurant).filter_by(id=restaurant_id).\
            update({'cuisine_id':newCuisine_id})

    if newPicture_id is not None:
        session.query(Restaurant).filter_by(id=restaurant_id).\
            update({'picture_id':newPicture_id})        

    session.commit()
    session.close()

def editRestaurantMenuItem(restaurantMenuItem_id, newName=None, 
                           newDescription=None, newPrice=None,
                           newMenuSection_id=None, newBaseMenuItem_id=None,
                           newPicture_id=None):
    """Edit a restaurant menu item.

    Pass none for any attribute to leave it unchanged.

    Args:
        restaurantMenuItem_id: the id of the restaurant menu item to edit
        newName: a new name for the restaurant menu item.
        newDescription: a new description for the restaurant menu item.
        newPrice: a new price for the restaurant menu item.
        newMenuSection_id: the id of the restaurant menu item's new menu section.
        newBaseMenuItem_id: the id of the restaurant menu item's new
        newPicture_id: the id of the restaurant menu item's new picture.
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
            update({'price':Decimal(newPrice).quantize(Decimal('0.01'))})

    if newMenuSection_id is not None:
        session.query(RestaurantMenuItem).filter_by(id=restaurantMenuItem_id).\
            update({'menuSection_id':newMenuSection_id})

    if newPicture_id is not None:
        session.query(RestaurantMenuItem).filter_by(id=restaurantMenuItem_id).\
            update({'picture_id':newPicture_id})

    if newBaseMenuItem_id is not None:
        session.query(RestaurantMenuItem).filter_by(id=restaurantMenuItem_id).\
            update({'baseMenuItem_id':newBaseMenuItem_id})

    session.commit()
    session.close()

def editCuisine(cuisine_id, newName=None):
    """Edit a cuisine

    Pass none for an attribute to leave it unchanged.
    Args:
        cuisine_id: the id of the cuisine to edit
        newName: the new name of the cuisine to edit.
    """
    session = getRestaurantDBSession()

    if newName is not None:
        session.query(Cuisine).filter_by(id=cuisine_id).\
            update({'name':newName})

    session.commit()
    session.close()

def editBaseMenuItem(baseMenuItem_id, newName=None, 
                     newDescription=None, newPrice=None,
                     newCuisine_id=None, newMenuSection_id=None,
                     newPictur_ide=None):
    """Edit a base menu item

    Pass none for an attribute to leave it unchanged.

    Args:
        baseMenuItem_id: the id of the base menu item to edit
        newName: a new name for the base menu item
        newDescription: a new description for the base menu item
        newPrice: a new price for the base menu item
        newCuisine_id: the id of the base menu item's new cuisine
        newMenuSection_id: the id of the base menu item's new menu section
        newPicture_id: the id of the base menu item's new picture
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
            update({'price':Decimal(newPrice).quantize(Decimal('0.01'))})

    if newMenuSection_id is not None:
        session.query(BaseMenuItem).filter_by(id=baseMenuItem_id).\
            update({'menuSection_id':newMenuSection_id})

    if newCuisine_id is not None:
        session.query(BaseMenuItem).filter_by(id=baseMenuItem_id).\
            update({'cuisine_id':newCuisine_id})

    if newPicture_id is not None:
        session.query(BaseMenuItem).filter_by(id=baseMenuItem_id).\
            update({'picture':newPicture_id})

    session.commit()
    session.close()

def deleteRestaurantMenuItem(restaurantMenuItem_id=None):
    """Remove a restaurant menu item from the database.

    Also deletes the restaurant menu item's picture, but only if 
    that picture is different from its base menu item's picture.

    Args:
        restaurantMenuItem_id: the id of the restaurant menu item to remove
    """
    session = getRestaurantDBSession()

    if restaurantMenuItem_id is not None:

        restaurantMenuItem = getRestaurantMenuItem(restaurantMenuItem_id)
        baseMenuItem = getBaseMenuItem(restaurantMenuItem.baseMenuItem_id)

        if restaurantMenuItem.picture_id != baseMenuItem.picture_id:
            deletePicture(restaurantMenuItem.picture_id)

        session.query(RestaurantMenuItem).\
            filter_by(id=restaurantMenuItem_id).\
            delete(synchronize_session=False)

        session.commit()

    session.close()

def deletePicture(picture_id=None):
    """Remove a picture from the database.

    Also deletes the picture from the file system, if it was 
    uploaded by a user.

    Args:
        picture_id: the id of the picture to remove
    """
    session = getRestaurantDBSession()

    picture = getPicture(picture_id=picture_id)

    if picture.serve_type == 'upload':
        relPath = 'pics/'+picture.text
        os.remove(relPath)

    if picture_id is not None:
        session.query(Picture).\
            filter_by(id=picture_id).\
            delete(synchronize_session=False)

        session.commit()

    session.close()

def deleteRestaurant(restaurant_id=None):
    """Remove a restaurant from the database.

    NOTE: This also deletes all the restaurant's restaurant menu items
    and the restaurant's picture.

    Args:
        restaurant_id: the id of the restaurant to remove
    """
    session = getRestaurantDBSession()

    if restaurant_id is not None:
        restaurantMenuItems = getRestaurantMenuItems(restaurant_id=restaurant_id)

        for restaurantMenuItem in restaurantMenuItems:
            session.query(RestaurantMenuItem).\
                filter_by(id=restaurantMenuItem.id).\
                delete(synchronize_session=False)

            session.commit()

        restaurant = getRestaurant(restaurant_id)
        deletePicture(restaurant.picture_id)

        session.query(Restaurant).filter_by(id=restaurant_id).\
                delete(synchronize_session=False)
        
        session.commit()

    session.close()

def deleteBaseMenuItem(baseMenuItem_id=None):
    """Remove a base menu item from the database.

    NOTE: This also reassigns all restaurant menu items with the given 
    item as its base to the default base item for restaurant menu
    items with no base item.

    Args:
        baseMenuItem_id: the id of the base menu item to remove
    """
    session = getRestaurantDBSession()

    if baseMenuItem_id is not None:
        restaurantMenuItems = getRestaurantMenuItems(baseMenuItem_id=baseMenuItem_id)

        for restaurantMenuItem in restaurantMenuItems:
            editRestaurantMenuItem(restaurantMenuItem.id,
                                   newBaseMenuItem_id=-1)

        session.query(BaseMenuItem).\
            filter_by(id=baseMenuItem_id).\
            delete(synchronize_session=False)

        session.commit()

    session.close()

def deleteCuisine(cuisine_id=None):
    """Remove a cuisine from the database.

    NOTE: This also reassigns all restaurants with this cuisine to "No
        specific cuisine" and reassigns all restaurant menu items with a base
        menu item with this cuisine to "Base Menu Item for Restaurant Menu Items
        with No Specific Cuisine".

    Args:
        cuisine_id: the id of the cuisine to remove
    """
    session = getRestaurantDBSession()

    if cuisine_id is not None:
        baseMenuItems = getBaseMenuItems(cuisine_id=cuisine_id)
        restaurants = getRestaurants(cuisine_id=cuisine_id)

        for baseMenuItem in baseMenuItems:
            deleteBaseMenuItem(baseMenuItem_id=baseMenuItem.id)

        for restaurant in restaurants:
            editRestaurant(restaurant.id,
                           newCuisine_id=-1)
            session.commit()        

        session.query(Cuisine).filter_by(id=cuisine_id).\
                delete(synchronize_session=False)
        
        session.commit()

    session.close()

def dropAllRecords():
    """Drop all records from the database
    """
    engine = create_engine('sqlite:///restaurants.db')
    Base.metadata.bind = engine

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
