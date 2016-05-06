### WARNING: Running this script clears and repopulates
### the database 'sqlite:///restaurants.db'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from RestaurantManager import getRestaurants, populateMenuWithBaseItems
from database_setup import Base, Cuisine, Restaurant, BaseMenuItem, RestaurantMenuItem

import random


engine = create_engine('sqlite:///restaurants.db')
Base.metadata.bind = engine
# clear existing data
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
# get session
DBSession = sessionmaker(bind=engine)
session = DBSession()


### add a dummy cuisine for foods and restaurants with no specific type
dummyCuisine = Cuisine(id=-1,name="No specific cuisine")
session.add(dummyCuisine)
session.commit()

### add eight popular cuisines and four of their signature dishes

# prepare dishes
tomYum = {'name':'Tom Yum Koong',
          'description':'Spicy soup with prawns',
          'price':'$7.00'}
padThai = {'name':'Pad Thai',
           'description':'Fried noodles with chicken, tofu, peanuts, and beansprouts',
           'price':'$6.00'}
somTam = {'name':'Som Tam',
          'description':'Spicy papaya salad',
          'price':'$4.00'}
khaoSoi = {'name':'Khao Soi',
           'description':'Yellow curry soup with coconut milk, chicken, and boiled and fried egg noodles',
           'price':'$5.50'}
hamburger = {'name':'Hamburger',
             'description':'A quarter-pound beef patty on a bun',
             'price':'$5.25'}
cheeseBurger = {'name':'Cheeseburger',
                'description':'A quarter-pound beef patty on a bun with your choice of cheese',
                'price':'$6.00'}
frenchFries = {'name':'French fries',
               'description':'Potatoes sliced very thin, deep fried, and sprinkled with salt',
               'price':'$1.50'}
milkshake = {'name':'Milkshake',
             'description':'Strawberry, chocolate, or vanilla milkshake',
             'price':'$2.00'}
pumpBagel = {'name':'Pumpernickel Bagel',
             'description':'Fresh pumpernickel bagel; cream cheese optional',
             'price':'$3.00'}
cornBeef = {'name':'Corned Beef',
            'description':'Rye bread piled high with corned beef and topped with spicy mustard',
            'price':'$6.25'}
italianSub = {'name':'Italian',
              'description':'Salami, ham, banana peppers, lettuce, and more topped with a vinaigrette',
              'price':'$5.50'}
pickle = {'name':'Pickle',
          'description':'One whole kosher dill pickle',
          'price':'$1.00'}
chicParm = {'name':'Chicken Parmesean',
            'description':'Chicken breast baked with tomato sauce and lots of mozarella',
            'price':'$10.50'}
persPizza = {'name':'Personal Pizza',
             'description':'10 inch personal pizza with your choice of up to two toppings',
             'price':'$9.00'}
canoli = {'name':'Canoli',
          'description':'Homeade, cream filled pastry',
          'price':'$3.50'}
pene = {'name':'Pene',
        'description':'Pene with fish and cream sauce',
        'price':'$13.50'}
belgianWaff = {'name':'Belgian Waffle',
               'description':'Large, fluffy Belgian waffle',
               'price':'$6.30'}
breakSaus = {'name':'Breakfast Sausage',
             'description':'Five all-beef sausage links',
             'price':'$2.50'}
hashBrown = {'name':'Hash Browns',
             'description':'Shredded potatoes fried in butter with garlic and onions',
             'price':'$1.90'}
coffee = {'name':'Coffee',
          'description':'100% Arabica coffee',
          'price':'$1.50'}
oneScoop = {'name':'One Scoop',
            'description':'One scoop of your flavor choice',
            'price':'$2.00'}
twoScoops = {'name':'Two Scoops',
             'description':'Two scoops of your flavor choices',
             'price':'$3.75'}
waffleCone = {'name':'Waffle Cone',
              'description':'A waffle cone... scoops sold separately!',
              'price':'$1.50'}
sundae = {'name':'Sundae',
          'description':'Three scoops topped with banana slices, cherries, and your choice of sauce',
          'price':'$6.50'}
cobb = {'name':'Cobb Salad',
        'description':'Iceberg lettuce with hardboiled egg, bacon, bleu cheese, and ranch dressing',
        'price':'$6.50'}
ceasar = {'name':'Ceasar Salad',
          'description':'Romain lettuce, croutons, parmesan cheese, and our house dressing',
          'price':'$6.00'}
fruitSalad = {'name':'Fruit Salad',
              'description':'A mix of oranges, bananas, raspberries, and blueberries',
              'price':'$4.00'}
greenTea = {'name':'Green Tea',
            'description':'A simple blend of green tea leaves',
            'price':'$1.40'}
twoDrum = {'name':'Two Drumsticks',
           'description':'Two chicken drumsticks deep fried with our house breadcrumb blend',
           'price':'$4.00'}
oneBreast = {'name':'One Breast',
             'description':'One chicken breast deep fried with our house breadcrumb blend',
             'price':'$4.25'}
mashTate = {'name':'Mashed Potatoes',
            'description':'Gooey mashed potatoes flavored with garlic and paprica',
            'price':'$2.75'}
sweeTea = {'name':'Sweet Tea',
           'description':'A tall, cool glass of southern sweet tea',
           'price':'$3.10'}

# prepare menus
baseMenus = {'Thai':[tomYum,padThai,somTam,khaoSoi],
             'Burgers':[hamburger,cheeseBurger,frenchFries,milkshake],
             'Delicatessen':[pumpBagel,cornBeef,italianSub,pickle],
             'Italian':[chicParm,persPizza,canoli,pene],
             'Waffles':[belgianWaff,breakSaus,hashBrown,coffee],
             'Ice Cream':[oneScoop,twoScoops,waffleCone,sundae],
             'Salad':[cobb,ceasar,fruitSalad,greenTea],
             'Fried Chicken':[twoDrum,oneBreast,mashTate,sweeTea]}

# add cuisines and their associated dishes to the database
for cuisine in baseMenus:
    cuisineObj = Cuisine(name=cuisine)
    session.add(cuisineObj)
    session.commit()
    
    for baseMenuItem in baseMenus[cuisine]:
        cuisineObj = session.query(Cuisine).filter_by(name=cuisine).one()
        baseMenuItem = BaseMenuItem(name=baseMenuItem['name'],
                                    description=baseMenuItem['description'],
                                    price=baseMenuItem['price'],
                                    cuisine_id=cuisineObj.id)
        session.add(baseMenuItem)
        session.commit()


### generate names for restaurants; we've manually ensured the
### cuisine names match the names now in the Cuisine table
possPros = ['Jill\'s','Ryan\'s','Our','Your','Canada\'s','Franklin\'s',\
            'Morroco\'s','Hilde\'s']
adjectives = ['Great','Best','Blazin','Happy','Delicious','Elegant',\
              'Big','Yummy']
cuisines = ['Thai', 'Burgers','Delicatessen','Italian','Waffles','Ice Cream',\
            'Salad','Fried Chicken']


### add 40 restaurants to the database (names not unique)
for restaurant in range(0,40):
    poss = possPros[int(round(random.uniform(0,len(possPros)-1)))]
    adj = adjectives[int(round(random.uniform(0,len(adjectives)-1)))]
    thisCuisine = cuisines[int(round(random.uniform(0,len(cuisines)-1)))]

    thisCuisineObj = session.query(Cuisine).filter_by(name=thisCuisine).one()

    restaurantName = poss+" "+adj+" "+thisCuisine
    newRestaurant = Restaurant(name=restaurantName,cuisine_id=thisCuisineObj.id)
    session.add(newRestaurant)
    session.commit()

session.close()


### add base cuisine items to each restaurant's menu
rests = getRestaurants()

for restaurant in rests:
    populateMenuWithBaseItems(restaurant.id)
