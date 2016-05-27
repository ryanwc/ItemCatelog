### WARNING: Running this script clears and repopulates
### the database 'sqlite:///restaurants.db'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from RestaurantManager import (addMenuSection, addUser, addCuisine, 
  addBaseMenuItem, addPicture, populateMenuWithBaseItems, addRestaurant, 
  getCuisine, dropAllRecords, getMenuSection, getRestaurantDBSession, 
  getUsers, getRestaurants, getRestaurant)

from database_setup import (Base, Cuisine, Restaurant, BaseMenuItem, 
  RestaurantMenuItem, User, MenuSection, Picture)

import random
import json


### delete everything
dropAllRecords()


session = getRestaurantDBSession()

# from initial .json data...
tableFuncs = [Picture, User, Cuisine, MenuSection, 
              BaseMenuItem, Restaurant, RestaurantMenuItem]

for tableFunc in tableFuncs:
    tableData = json.loads(open('initial_data/'+\
      tableFunc.__name__+'.json', 'r').read())
    key = tableFunc.__name__ + 's'
    for jsonRow in tableData[key]:
        print jsonRow
        dbRow = tableFunc(**jsonRow)
        print dbRow
        session.add(dbRow)
        session.commit()

session.close()

'''
### add more random restaurants to the database if desired
### would need to modify to accomdate the .json structure above
for restaurant in range(0,10):
    poss = possivesAndAdverbs[int(round(random.uniform(0,len(possivesAndAdverbs)-1)))]
    adj = adjectives[int(round(random.uniform(0,len(adjectives)-1)))]
    thisCuisine = cuisines[int(round(random.uniform(0,len(cuisines)-1)))]

    user_id = int(round(random.uniform(1,len(getUsers()))))

    picture_id = restaurantPicIDs[int(round(random.uniform(0,len(restaurantPicIDs)-1)))]

    thisCuisineObj = getCuisine(name=thisCuisine)

    restaurantName = poss+" "+adj+" "+thisCuisine
    restaurant_id = addRestaurant(name=restaurantName, 
      cuisine_id=thisCuisineObj.id, user_id=user_id, picture_id=picture_id)
    restaurant = getRestaurant(restaurant_id)
    populateMenuWithBaseItems(restaurant.id)
'''
