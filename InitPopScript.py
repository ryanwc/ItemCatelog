from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from RestaurantManager import getRestaurants
from database_setup import Base, Restaurant, MenuItem

import random


engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# clear data
for tbl in reversed(Base.metadata.sorted_tables):
    engine.execute(tbl.delete())
session.commit()

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
for restaurant in range(0,40):
    poss = possPros[int(round(random.uniform(0,len(possPros)-1)))]
    adj = adjectives[int(round(random.uniform(0,len(adjectives)-1)))]
    thisCuisine = cuisines[int(round(random.uniform(0,len(cuisines)-1)))]

    restaurantName = poss+" "+adj+" "+thisCuisine
    restaurants.append({'name':restaurantName,'possPro':poss,\
                        'adj':adj,'cuisine':thisCuisine})
    newRestaurant = Restaurant(name=restaurantName,foodType=thisCuisine)
    session.add(newRestaurant)
    session.commit()

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
              'description':'Salami, ham, banana peppers, lettue, and more topped with a vinaigrette',
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

baseMenus = {'Thai':[tomYum,padThai,somTam,khaoSoi],
             'Burgers':[hamburger,cheeseBurger,frenchFries,milkshake],
             'Delicatessen':[pumpBagel,cornBeef,italianSub,pickle],
             'Italian':[chicParm,persPizza,canoli,pene],
             'Waffles':[belgianWaff,breakSaus,hashBrown,coffee],
             'Ice Cream':[oneScoop,twoScoops,waffleCone,sundae],
             'Salad':[cobb,ceasar,fruitSalad,greenTea],
             'Fried Chicken':[twoDrum,oneBreast,mashTate,sweeTea]}

rests = getRestaurants()

# populate the menu table
for restaurant in rests:
    print restaurant.foodType
    for item in baseMenus[restaurant.foodType]:
        menuItem = MenuItem(name=item['name'],
                            description=item['description'],
                            price=item['price'],
                            restaurant_id=restaurant.id)
        session.add(menuItem)
        session.commit()
