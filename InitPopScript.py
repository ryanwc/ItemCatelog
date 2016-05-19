### WARNING: Running this script clears and repopulates
### the database 'sqlite:///restaurants.db'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from RestaurantManager import *
from database_setup import Base, Cuisine, Restaurant, BaseMenuItem, RestaurantMenuItem, User, MenuSection, Picture

import random
from decimal import *


### delete everything
dropAllRecords()

### add some users
addUser(name="Robo Barista", email="tinnyTim@udacity.com", 
  picture_id=addPicture('https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png', 'link')
  )
print str(user.id)
addUser(name="Der Koch", email="ichbinkoch@example.com", 
  picture_id=addPicture('https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Mendel_I_142_r.jpg/173px-Mendel_I_142_r.jpg', 'link')
  )
addUser(name="Masayoshi Kazato", email="sushichef@example.com", 
  picture_id=addPicture('https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Sushi_chef_Masayoshi_Kazato_02.JPG/320px-Sushi_chef_Masayoshi_Kazato_02.JPG', 'link')
  )
addUser(name="Master Chef", email="master@example.com", 
  picture_id=addPicture('https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Chef_pr%C3%A9parant_une_truffe.jpg/320px-Chef_pr%C3%A9parant_une_truffe.jpg', 'link')
  )
addUser(name="Tandor", email="tandor@example.com", 
  picture_id=addPicture('https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Tandoor_chef_2.jpg/251px-Tandoor_chef_2.jpg', 'link')
  )
addUser(name="Peking Chef", email="peking@example.com", 
  picture_id=addPicture('https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Preparing_Peking_duck.JPG/180px-Preparing_Peking_duck.JPG', 'link')
  )
addUser(name="Romantic Chef", email="romantic@example.com", 
  picture_id=addPicture('https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Ribot_Theodule_The_Cook_And_The_Cat-1.jpg/183px-Ribot_Theodule_The_Cook_And_The_Cat-1.jpg', 'link')
  )
addUser(name="Kramer", email="kramer@example.com", picture_id=addPicture('https://upload.wikimedia.org/wikipedia/en/b/b7/Cosmo_Kramer.jpg', 'link'))
addUser(name="George", email="george@example.com", picture_id=addPicture('https://upload.wikimedia.org/wikipedia/en/7/70/George_Costanza.jpg', 'link'))

### create menu sections
addMenuSection("Appetizer")
appetizerID = getMenuSection(name="Appetizer").id
addMenuSection("Main Course")
mainCourseID = getMenuSection(name="Main Course").id
addMenuSection("Dessert")
dessertID = getMenuSection(name="Dessert").id
addMenuSection("Drink")
drinkID = getMenuSection(name="Drink").id
addMenuSection("Side Dish")
sideDishID = getMenuSection(name="Side Dish").id
addMenuSection("Other")
otherID = getMenuSection(name="Other").id

### add a dummy cuisine for foods and restaurants with no specific type
session = getRestaurantDBSession()
dummyCuisine = Cuisine(id=-1,name="No Specific Cuisine")
session.add(dummyCuisine)
session.commit()
session.close()

### add a dummy base menu item for foods with no specific type
session = getRestaurantDBSession()
dummyBaseMenuItem = BaseMenuItem(id=-1, 
  name="Base Item with no Specific Cuisine", 
  description="This item has no specific cuisine", cuisine_id=-1,
  menuSection_id=otherID, price='0.00', picture_id=addPicture("", "link"))
session.add(dummyBaseMenuItem)
session.commit()
session.close()

### add eight popular cuisines and four of their signature dishes

# prepare dishes
tomYum = {'name':'Tom Yum Koong',
          'description':'Spicy soup with prawns',
          'price':'7.00',
          'menuSection':mainCourseID,
          'picture':'https://upload.wikimedia.org/wikipedia/commons/e/e8/Tom_yam_kung_maenam.jpg'}
padThai = {'name':'Pad Thai',
           'description':'Fried noodles with chicken, tofu, peanuts, and beansprouts',
           'price':'6.00',
           'menuSection':mainCourseID,
           'picture':'https://upload.wikimedia.org/wikipedia/commons/3/39/Phat_Thai_kung_Chang_Khien_street_stall.jpg'}
somTam = {'name':'Som Tam',
          'description':'Spicy papaya salad',
          'price':'4.00',
          'menuSection':appetizerID,
          'picture':'https://upload.wikimedia.org/wikipedia/commons/3/34/2013_Tam_Lao.jpg'}
khaoSoi = {'name':'Khao Soi',
           'description':'Yellow curry soup with coconut milk, chicken, and boiled and fried egg noodles',
           'price':'5.50',
           'menuSection':mainCourseID,
           'picture':'https://upload.wikimedia.org/wikipedia/commons/6/6c/Khao_soi_Chiang_Mai.jpg'}
fruitSmooth = {'name':'Fruit Smoothie',
               'description':'Banana, mango, dragonfruit, or coconut smoothie',
               'price':'3.25',
               'menuSection':drinkID,
               'picture':'https://s-media-cache-ak0.pinimg.com/236x/13/84/01/138401deb6f59a743a44c26d991f8d18.jpg'}
mangoSticky = {'name':'Mango with Sticky Rice',
               'description':'The classic Thai dessert',
               'price':'3.75',
               'menuSection':dessertID,
               'picture':'https://s-media-cache-ak0.pinimg.com/originals/1b/81/9a/1b819a524a52e5c44c373e5bfb22ab30.jpg'}
stickyRice = {'name':'Sticky Rice',
              'description':'Glutinous rice',
              'price':'1.10',
              'menuSection':sideDishID,
              'picture':'https://s-media-cache-ak0.pinimg.com/736x/ec/a6/39/eca6393c6dbf13d9a53cdd8e7317261a.jpg'}

hamburger = {'name':'Hamburger',
             'description':'A quarter-pound beef patty on a bun',
             'price':'5.25',
             'menuSection':mainCourseID,
             'picture':'https://upload.wikimedia.org/wikipedia/commons/3/3f/Flickr_-_cyclonebill_-_Burger.jpg'}
cheeseBurger = {'name':'Cheeseburger',
                'description':'A quarter-pound beef patty on a bun with your choice of cheese',
                'price':'6.00',
                'menuSection':mainCourseID,
                'picture':'https://upload.wikimedia.org/wikipedia/commons/4/4d/Cheeseburger.jpg'}
frenchFries = {'name':'French fries',
               'description':'Potatoes sliced very thin, deep fried, and sprinkled with salt',
               'price':'1.50',
               'menuSection':sideDishID,
               'picture':'https://upload.wikimedia.org/wikipedia/commons/3/3b/Pommes-1.jpg'}
milkshake = {'name':'Milkshake',
             'description':'Strawberry, chocolate, or vanilla milkshake',
             'price':'2.00',
             'menuSection':dessertID,
             'picture':'https://upload.wikimedia.org/wikipedia/commons/7/72/Strawberry_milkshake.jpg'}
friedMozz = {'name':'Fried Mozzarella',
              'description':'Six fried mozzarella stick served with marinara sauce',
              'price':'4.10',
              'menuSection':appetizerID,
              'picture':'https://s-media-cache-ak0.pinimg.com/736x/dd/31/1b/dd311be162318fd574706e9b1184d71a.jpg'}
soda = {'name':'Soda',
        'description':'A sugary, carbonated beverage',
        'price':'1.50',
        'menuSection':drinkID,
        'picture':'https://s-media-cache-ak0.pinimg.com/originals/f5/82/43/f58243d7b9f44cb5e961ab5ec1619377.jpg'}

pumpBagel = {'name':'Pumpernickel Bagel',
             'description':'Fresh pumpernickel bagel; cream cheese optional',
             'price':'3.00',
             'menuSection':appetizerID,
             'picture':'https://s-media-cache-ak0.pinimg.com/236x/f9/39/9a/f9399a404f215724519bb8022abd4953.jpg'}
cornBeef = {'name':'Corned Beef',
            'description':'Rye bread piled high with corned beef and topped with spicy mustard',
            'price':'6.25',
            'menuSection':mainCourseID,
            'picture':'https://upload.wikimedia.org/wikipedia/commons/9/94/Mmm..._corned_beef_on_rye_with_a_side_of_kraut_%287711551990%29.jpg'}
italianSub = {'name':'Italian',
              'description':'Salami, ham, banana peppers, lettuce, and more topped with a vinaigrette',
              'price':'5.50',
              'menuSection':mainCourseID,
              'picture':'https://upload.wikimedia.org/wikipedia/commons/e/e6/Hoagie_Hero_Sub_Sandwich.jpg'}
pickle = {'name':'Pickle',
          'description':'One whole kosher dill pickle',
          'price':'1.00',
          'menuSection':sideDishID,
          'picture':'https://upload.wikimedia.org/wikipedia/commons/b/bb/Pickle.jpg'}
meatSampler = {'name':'Meat Sampler',
               'description':'Corned beef, two types of salami, and two type of ham',
               'price':'5.90',
               'menuSection':appetizerID,
               'picture':'https://s-media-cache-ak0.pinimg.com/236x/1b/f2/be/1bf2beba3a843563e3430d4006d0c412.jpg'}
chips = {'name':'Potato Chips',
         'description':'Homemade, crispy potato chips seasoned with salt and pepper',
         'price':'1.50',
         'menuSection':sideDishID,
         'picture':'https://s-media-cache-ak0.pinimg.com/236x/63/ca/d0/63cad031bc987a148808a89bb9ce6ddb.jpg'}
beer = {'name':'Beer',
        'description':'A pint of delicious, slightly hoppy, local brew',
        'price':'4.00',
        'menuSection':drinkID,
        'picture':'https://s-media-cache-ak0.pinimg.com/originals/10/ed/8e/10ed8e9470cb85d4a5ed316973f67da1.jpg'}

chicParm = {'name':'Chicken Parmesean',
            'description':'Chicken breast baked with tomato sauce and lots of mozarella',
            'price':'10.50',
            'menuSection':mainCourseID,
            'picture':'https://upload.wikimedia.org/wikipedia/commons/d/dc/Chicken_parmiagana.jpg'}
persPizza = {'name':'Personal Pizza',
             'description':'10 inch personal pizza with your choice of up to two toppings',
             'price':'9.00',
             'menuSection':mainCourseID,
             'picture':'https://upload.wikimedia.org/wikipedia/commons/a/a3/Eq_it-na_pizza-margherita_sep2005_sml.jpg'}
canoli = {'name':'Canoli',
          'description':'Homeade, cream filled pastry',
          'price':'3.50',
          'menuSection':dessertID,
          'picture':'https://upload.wikimedia.org/wikipedia/commons/1/14/Cannolo_siciliano_with_chocolate_squares.jpg'}
pene = {'name':'Penne',
        'description':'Penne with beef tomato sauce',
        'price':'13.50',
        'menuSection':mainCourseID,
        'picture':'https://upload.wikimedia.org/wikipedia/commons/2/24/Penne_all%27arrabbiata.jpg'}
houseWhite = {'name':'House White',
        'description':'A glass of the house white wine',
        'price':'6.50',
        'menuSection':drinkID,
        'picture':'https://s-media-cache-ak0.pinimg.com/736x/0e/7d/72/0e7d72880a33d35b63537465265107c1.jpg'}
houseRed = {'name':'House Red',
        'description':'A glass of the house red wine',
        'price':'7.00',
        'menuSection':drinkID,
        'picture':'https://s-media-cache-ak0.pinimg.com/236x/3b/96/c9/3b96c9e1b2920230d625a37d3010826d.jpg'}
olivePlate = {'name':'Olive Plate',
        'description':'Black, green, and castelvetrano olives',
        'price':'3.80',
        'menuSection':sideDishID,
        'picture':'https://s-media-cache-ak0.pinimg.com/236x/21/ae/df/21aedff5057040ef8c371cf47d0555f8.jpg'}
minestrone = {'name':'Minestrone Soup',
        'description':'A hearty cup of minestrone featuring zucchini and summer squash',
        'price':'3.75',
        'menuSection':appetizerID,
        'picture':'https://s-media-cache-ak0.pinimg.com/236x/ed/6c/cc/ed6cccec72be5befbeb87f9f754c20dc.jpg'}
garlicBread = {'name':'Garlic Bread',
        'description':'Freshly baked, crusty garlic bread',
        'price':'2.00',
        'menuSection':sideDishID,
        'picture':'https://s-media-cache-ak0.pinimg.com/236x/2a/c9/56/2ac9566d5063f8e31d374ea8ac043bca.jpg'}
tiramisu = {'name':'Tiramisu',
        'description':'The popular coffee-flavored dessert',
        'price':'5.50',
        'menuSection':dessertID,
        'picture':'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Tiramisu_with_blueberries_and_raspberries%2C_July_2011.jpg/300px-Tiramisu_with_blueberries_and_raspberries%2C_July_2011.jpg'}
ravioli = {'name':'Ravioli',
        'description':'Goat cheese ravioli in cream sauce',
        'price':'7.25',
        'menuSection':appetizerID,
        'picture':'https://s-media-cache-ak0.pinimg.com/236x/20/a2/99/20a299f020c97c6ce5c4e95ffa95f528.jpg'}

belgianWaff = {'name':'Belgian Waffle',
               'description':'Large, fluffy Belgian waffle with strawberries',
               'price':'6.30',
               'menuSection':mainCourseID,
               'picture':'https://upload.wikimedia.org/wikipedia/commons/c/cf/Waffle_with_strawberries_and_confectioner%27s_sugar.jpg'}
breakSaus = {'name':'Breakfast Sausage',
             'description':'Seven small, all-beef sausage patties',
             'price':'2.50',
             'menuSection':sideDishID,
             'picture':'https://upload.wikimedia.org/wikipedia/commons/7/7d/Breakfast_Saussage.jpg'}
hashBrown = {'name':'Hash Browns',
             'description':'Shredded potatoes fried in butter with garlic and onions',
             'price':'1.90',
             'menuSection':sideDishID,
             'picture':'https://s-media-cache-ak0.pinimg.com/736x/19/43/9c/19439c09af13d300237ad913b5fda82d.jpg'}
coffee = {'name':'Coffee',
          'description':'100% Arabica coffee',
          'price':'1.50',
          'menuSection':drinkID,
          'picture':'https://upload.wikimedia.org/wikipedia/commons/4/45/A_small_cup_of_coffee.JPG'}
bacon = {'name':'Bacon',
        'description':'Four slices of crispy bacon',
        'price':'2.50',
        'menuSection':sideDishID,
        'picture':'https://s-media-cache-ak0.pinimg.com/236x/3e/78/69/3e7869532c249dc3575ea5850b408a23.jpg'}
egg = {'name':'One Egg',
        'description':'One egg, cooked any style',
        'price':'1.00',
        'menuSection':sideDishID,
        'picture':'http://24.media.tumblr.com/tumblr_m6uvaeLNlE1r3a3r6o1_500.png'}
omelette = {'name':'Omelette',
        'description':'Three eggs with ham, onions, peppers, tomatoes, and cheese',
        'price':'6.30',
        'menuSection':mainCourseID,
        'picture':'https://s-media-cache-ak0.pinimg.com/236x/2e/a6/02/2ea602351a3eb5b3ce904629c8b7266c.jpg'}
pancakes = {'name':'Pancakes',
        'description':'A stack of three golden-brown pancakes',
        'price':'5.00',
        'menuSection':mainCourseID,
        'picture':'https://s-media-cache-ak0.pinimg.com/originals/6f/7b/ab/6f7bab83009d87a621f375b22cc35838.jpg'}

oneScoop = {'name':'One Scoop',
            'description':'One scoop of your flavor choice',
            'price':'2.00',
            'menuSection':dessertID,
            'picture':'https://s-media-cache-ak0.pinimg.com/236x/37/08/b4/3708b47ffc250865e8e7e026841b42bc.jpg'}
twoScoops = {'name':'Two Scoops',
             'description':'Two scoops of your flavor choices',
             'price':'3.75',
             'menuSection':dessertID,
             'picture':'https://s-media-cache-ak0.pinimg.com/236x/36/80/dd/3680dd7b6acd48f5b44d298a8889cc1d.jpg'}
waffleCone = {'name':'Waffle Cone',
              'description':'A waffle cone... scoops sold separately!',
              'price':'1.50',
              'menuSection':otherID,
              'picture':'https://s-media-cache-ak0.pinimg.com/236x/78/fb/6a/78fb6afe746280c76a5691c448f9ffd1.jpg'}
sundae = {'name':'Sundae',
          'description':'Three scoops topped with your choice of fruit and sauce',
          'price':'6.50',
          'menuSection':dessertID,
          'picture':'https://upload.wikimedia.org/wikipedia/commons/a/ae/StrawberrySundae.jpg'}

cobb = {'name':'Cobb Salad',
        'description':'Iceberg lettuce with grilled chicken, hardboiled egg, bacon, bleu cheese, and ranch dressing',
        'price':'6.50',
        'menuSection':mainCourseID,
        'picture':'https://s-media-cache-ak0.pinimg.com/236x/ed/b6/25/edb6251389e8a8553fee37f2462086b1.jpg'}
ceasar = {'name':'Ceasar Salad',
          'description':'Romain lettuce, croutons, parmesan cheese, and our house dressing',
          'price':'6.00',
          'menuSection':mainCourseID,
          'picture':'https://upload.wikimedia.org/wikipedia/commons/2/23/Caesar_salad_%282%29.jpg'}
fruitSalad = {'name':'Fruit Salad',
              'description':'A mix of strawberries, pineapple, kiwi, cantaloupe, and blueberries',
              'price':'4.00',
              'menuSection':appetizerID,
              'picture':'https://s-media-cache-ak0.pinimg.com/originals/50/bd/8a/50bd8aafab922fb94bfd37939bdcab56.jpg'}
greenTea = {'name':'Green Tea',
            'description':'A simple blend of green tea leaves',
            'price':'1.40',
            'menuSection':drinkID,
            'picture':'https://upload.wikimedia.org/wikipedia/commons/c/cb/Tea_leaves_steeping_in_a_zhong_%C4%8Daj_05.jpg'}
veganCookies = {'name':'Vegan Cookies',
        'description':'100% vegan chocolate chip cookies',
        'price':'3.10',
        'menuSection':dessertID,
        'picture':'https://s-media-cache-ak0.pinimg.com/236x/9c/de/1c/9cde1ceef22e4e4f186c132278cb0dba.jpg'}

twoDrum = {'name':'Two Drumsticks',
           'description':'Two chicken drumsticks deep fried with our house breadcrumb blend',
           'price':'4.00',
           'menuSection':mainCourseID,
           'picture':'https://s-media-cache-ak0.pinimg.com/236x/c6/ea/1c/c6ea1ce05a43590df965a455dbd38f85.jpg'}
oneBreast = {'name':'One Breast',
             'description':'One chicken breast deep fried with our house breadcrumb blend',
             'price':'4.25',
             'menuSection':mainCourseID,
             'picture':'https://s-media-cache-ak0.pinimg.com/236x/ba/22/65/ba22653c43cf716bd26fbf5eb1dbe9af.jpg'}
mashTate = {'name':'Mashed Potatoes',
            'description':'Gooey mashed potatoes flavored with garlic and paprica',
            'price':'2.75',
            'menuSection':sideDishID,
            'picture':'https://upload.wikimedia.org/wikipedia/commons/3/39/MashedPotatoes.jpg'}
sweeTea = {'name':'Sweet Tea',
           'description':'A tall, cool glass of southern sweet tea',
           'price':'3.10',
           'menuSection':drinkID,
           'picture':'https://upload.wikimedia.org/wikipedia/commons/e/ef/Iced_Tea_from_flickr.jpg'}
corn = {'name':'Corn',
        'description':'Buttered sweetcorn served off-the-cobb',
        'price':'2.20',
        'menuSection':sideDishID,
        'picture':'https://s-media-cache-ak0.pinimg.com/736x/47/2e/ee/472eee0fb79ee21f8068738df7106e6d.jpg'}


# prepare menus
baseMenus = {'Thai':[tomYum,padThai,somTam,khaoSoi,fruitSmooth,mangoSticky,stickyRice],
             'Burgers':[hamburger,cheeseBurger,frenchFries,milkshake,friedMozz,soda],
             'Delicatessen':[pumpBagel,cornBeef,italianSub,pickle,meatSampler,chips,beer],
             'Italian':[chicParm,persPizza,canoli,pene,houseWhite,houseRed,olivePlate,minestrone,garlicBread,tiramisu],
             'Waffles':[belgianWaff,breakSaus,hashBrown,coffee,bacon,egg,omelette,pancakes],
             'Ice Cream':[oneScoop,twoScoops,waffleCone,sundae],
             'Salad':[cobb,ceasar,fruitSalad,greenTea,veganCookies],
             'Fried Chicken':[twoDrum,oneBreast,mashTate,sweeTea,corn]}

# add cuisines and their associated dishes to the database
for cuisine in baseMenus:
    addCuisine(cuisine)
    cuisineObj = getCuisine(name=cuisine)

    for baseMenuItem in baseMenus[cuisine]:

        addBaseMenuItem(name=baseMenuItem['name'],
                        description=baseMenuItem['description'],
                        price=Decimal(baseMenuItem['price']).quantize(Decimal('0.01')),
                        cuisine_id=cuisineObj.id,
                        menuSection_id=baseMenuItem['menuSection'],
                        picture_id=addPicture(baseMenuItem['picture'], 'link'))


### generate names and pics restaurants; we've manually ensured the
### cuisine names match the names now in the Cuisine table
possivesAndAdverbs = ['Jill\'s','Ryan\'s','Our','Your','Canada\'s','Franklin\'s',\
                      'Morroco\'s','Hilde\'s','Branson\'s','Jim\'s','My',
                      'Definitively','Positively','Effortlessly',
                      'Heroically','Predictably']
adjectives = ['Great','Lip-Smacking','Blazin\'','Happy','Delicious','Elegant',\
              'Big','Yummy','Authentic','Homestyle']
cuisines = ['Thai', 'Burgers','Delicatessen','Italian','Waffles','Ice Cream',\
            'Salad','Fried Chicken']
restaurantPicIDs = [addPicture('https://upload.wikimedia.org/wikipedia/commons/a/a6/6x8_80dpi_-_Piment_rouge_-_view_of_cellar_fm_mezz_stairs_to_Peel.JPG', 'link'),
                    addPicture('https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Petrus_%28London%29_Kitchen.jpg/1024px-Petrus_%28London%29_Kitchen.jpg', 'link'),
                    addPicture('https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Chef%27s_table_at_Marcus.jpg/800px-Chef%27s_table_at_Marcus.jpg', 'link'),
                    addPicture('https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Inside_Le_Procope.jpg/1024px-Inside_Le_Procope.jpg', 'link'),
                    addPicture('https://upload.wikimedia.org/wikipedia/commons/5/52/PerSe.jpg', 'link'),
                    addPicture('https://upload.wikimedia.org/wikipedia/commons/1/1e/Tom%27s_Restaurant%2C_NYC.jpg', 'link'),
                    addPicture('https://s-media-cache-ak0.pinimg.com/736x/05/0e/03/050e033f834f3e50bc251be37f828839.jpg', 'link'),
                    addPicture('https://s-media-cache-ak0.pinimg.com/736x/03/15/c4/0315c45e007e7d8e417ed8bc904df7c9.jpg', 'link'),
                    addPicture('https://s-media-cache-ak0.pinimg.com/736x/84/32/86/843286f54381695e73deeb4d264c9f67.jpg', 'link'),
                    addPicture('https://s-media-cache-ak0.pinimg.com/736x/77/72/a6/7772a69c4e416b3ccbb2f7852eab9ccd.jpg', 'link')]

### add 50 restaurants to the database (names not unique)
numUsers = len(getUsers())
numRestaurantPics = len(restaurantPicIDs)
for restaurant in range(0,50):
    poss = possivesAndAdverbs[int(round(random.uniform(0,len(possivesAndAdverbs)-1)))]
    adj = adjectives[int(round(random.uniform(0,len(adjectives)-1)))]
    thisCuisine = cuisines[int(round(random.uniform(0,len(cuisines)-1)))]

    user_id = int(round(random.uniform(0,numUsers-1)))
    picture_id = restaurantPicIDs[int(round(random.uniform(0,numRestaurantPics-1)))]

    thisCuisineObj = getCuisine(name=thisCuisine)

    restaurantName = poss+" "+adj+" "+thisCuisine
    addRestaurant(name=restaurantName, 
                  cuisine_id=thisCuisineObj.id, 
                  user_id=user_id,
                  picture_id=picture_id)


### add base cuisine items to each restaurant's menu
rests = getRestaurants()

for restaurant in rests:
    populateMenuWithBaseItems(restaurant.id)
