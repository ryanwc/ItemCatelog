### WARNING: Running this script clears and repopulates
### the database 'sqlite:///restaurants.db'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from RestaurantManager import dropAllRecords, addRowsFromJSON

from database_setup import (Cuisine, Restaurant, BaseMenuItem, 
  RestaurantMenuItem, User, MenuSection, Picture)

import json

### delete everything
dropAllRecords()

### populate db from stored data
tableConstructors = [Picture, User, Cuisine, MenuSection, 
                     BaseMenuItem, Restaurant, RestaurantMenuItem]

for tableConstructor in tableConstructors:
    dataObj = json.loads(open('initial_data/'+\
        tableConstructor.__name__+'.json', 'r').read())
    key = tableConstructor.__name__ + 's'
    data = dataObj[key]

    addRowsFromJSON(data, tableConstructor)

'''
### add more random restaurants to the database if desired
### would need to modify to accomdate the .json structure above
### and import correct modules and methods
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
