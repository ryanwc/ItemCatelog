from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from RestaurantManager import getRestaurants
from database_setup import Base, Restaurant, MenuItem

import random


engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# list of possesive pronouns
possPros = ['Jill\'s','Ryan\'s','Our','Your','Canada\'s','Franklin\'s',\
            'Morroco\'s','Hilde\'s']
# list of adjectives
adjectives = ['Great','Best','Blazin','Happy','Delicious','Elegant',\
              'Big','Yummy']
# list of food types
cuisines = ['Thai', 'Burgers','Delicatessen','Italian','Waffles','Ice Cream',\
            'Salad','Fried Chicken']

restaurants = []
# populate the database with 40 restaurants
# (note that it's OK if names repeat, this could just be another branch)
for restaurant in range(0,39):
    poss = possPros[int(round(random.uniform(0,len(possPros)-1)))]
    adj = adjectives[int(round(random.uniform(0,len(adjectives)-1)))]
    cuisine = cuisines[int(round(random.uniform(0,len(cuisines)-1)))]

    restaurantName = poss+" "+adj+" "+cuisine
    restaurants.append({'name':restaurantName,'possPro':poss,\
                        'adj':adj,'cuisine':cuisine})
    newRestaurant = Restaurant(name=restaurantName,foodType=cuisine)
    session.add(newRestaurant)
    session.commit()

baseMenus = {'Thai':{'Tom Yum Koong','Pad Thai','Som Tam','Khao Soi'},
             'Burgers':{'Hamburger','Cheeseburger','French Fries','Milkshake'},
             'Delicatessen':{'Pumpernickel Bagel','Corned Beef','Italian','Pickle'},
             'Italian':{'Chicken Parmesean','Personal Pizza','Canoli','Pene'},
             'Waffles':{'Belgian Waffle','Breakfast Sausage','Hash browns','Coffee'},
             'Ice Cream':{'One Scoop','Two Scoops','Waffle Cone','Sundae'},
             'Salad':{'Cobb Salad','Ceasar Salad','Fruit Salad','Green Tea'},
             'Fried Chicken':{'Two Drumsticks','One Breast','Mashed Potatoes','Sweet Tea'}}

rests = getRestaurants()

# populate the menu table
for restaurant in rests:
    for item in baseMenus[restaurant.foodType]:
        menuItem = MenuItem(name=item,restaurant_id=restaurant.id)
        session.add(menuItem)
        session.commit()
