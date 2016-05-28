from flask import (Blueprint, render_template, request, redirect, 
    url_for, flash, session as login_session)

import os, requests
from decimal import Decimal

from restaurantmanager import DataManager, app
from restaurantmanager.utils import (getClientLoginSession, isLoggedIn, 
    isCSRFAttack, validateUserInput, validateUserPicture)
from restaurantmanager.home.home import login_required

restaurant_bp = Blueprint('restaurant', __name__, 
    template_folder='templates', static_folder='static')

@app.route('/restaurants/')
def restaurants():
    '''Serve info about all of the restaurants
    '''
    client_login_session = getClientLoginSession()

    cuisines = DataManager.getCuisines()

    numRestaurants = 0
    # get restaurants labeled with user or non-user
    # sectioned by cuisine
    cuisineToRestaurantsDict = {}
    for cuisine in cuisines:

        cuisineToRestaurantsDict[cuisine.id] = {}
        cuisineToRestaurantsDict[cuisine.id]['cuisine'] = cuisine
        restaurants = DataManager.\
                      getRestaurants(cuisine_id=cuisine.id)
        restaurantDicts = {}

        for restaurant in restaurants:

            numRestaurants += 1
            restaurantDict = {}
            restaurantDict['restaurant'] = restaurant
                      
            if (isLoggedIn() and
                restaurant.user_id == login_session['user_id']):

                restaurantDict['ownership'] = 'user'
            else:

                restaurantDict['ownership'] = 'non-user'

            restaurantDicts[restaurant.id] = restaurantDict

        cuisineToRestaurantsDict[cuisine.id]['restaurants'] = \
            restaurantDicts
    
    return render_template("Restaurants.html",
                    cuisineToRestaurantsDict=cuisineToRestaurantsDict,
                    numRestaurants=numRestaurants,
                    client_login_session=client_login_session)

@app.route('/restaurants/add/', methods=['GET','POST'])
@login_required
def addRestaurant():
    '''Serve form to add a restaurant
    '''
    client_login_session = getClientLoginSession()

    cuisines = DataManager.getCuisines()

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        validCuisineIDs = {}
        for cuisine in cuisines:
            validCuisineIDs[str(cuisine.id)] = True

        cuisine_id = validateUserInput(request.form['cuisineID'],
                'cuisine_id', 'create', 'restaurant', 
                columnNameForMsg='cuisine', required=True,
                validInputs=validCuisineIDs)

        if cuisine_id is None:
            return redirect(url_for('restaurants'))               

        name = validateUserInput(request.form['name'], 'name', 'create',
            'restaurant', maxlength=100, required=True)

        if name is None:
            return redirect(url_for('restaurants'))    

        providedPic = validateUserPicture('create', 'restaurant',
            file=request.files['pictureFile'],
            link=request.form['pictureLink'],
            maxlength=300, required=True)

        if providedPic is None:
            return redirect(url_for('restaurants'))
        
        picture_id = DataManager.addPicture(text=providedPic['text'], 
            serve_type=providedPic['serve_type'])

        restaurant_id = DataManager.addRestaurant(
                            name=name,
                            cuisine_id=cuisine_id,
                            user_id=login_session['user_id'],
                            picture_id=picture_id
                        )

        # if pic was uploaded, now that we know item id, 
        # save actual file for serving and set the name in the database
        if providedPic['serve_type'] == 'upload':
            picfilename = 'restaurant' + str(restaurant_id)
            request.files['pictureFile'].save(os.path.\
                join(app.config['UPLOAD_FOLDER'], picfilename))
            DataManager.editPicture(picture_id=picture_id,
                                          newText=picfilename)

        DataManager.populateMenuWithBaseItems(restaurant_id)

        flash("restaurant '" + name + "' added to the database!")

        return redirect(url_for('restaurants'))
    else:

        return render_template('AddRestaurant.html', 
                                cuisines=cuisines,
                                hiddenToken=login_session['state'],
                                client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/')
def restaurant(restaurant_id):
    '''Serve info about a restaurant
    '''
    client_login_session = getClientLoginSession()

    restaurant = DataManager.getRestaurant(restaurant_id)
    owner = DataManager.getUser(restaurant.user_id)
    restaurantMenuItems = DataManager.\
                          getRestaurantMenuItems(restaurant_id=restaurant_id)
    cuisine = DataManager.getCuisine(cuisine_id=restaurant.cuisine_id)

    picture = DataManager.getPicture(restaurant.picture_id)

    numMenuItems = len(restaurantMenuItems)

    if numMenuItems > 0:
        mostExpensiveItem = restaurantMenuItems[0]
        for item in restaurantMenuItems:
            if item.price > mostExpensiveItem.price:
                mostExpensiveItem = item
                mostExpensiveItem.price =\
                    Decimal(mostExpensiveItem.price).\
                    quantize(Decimal('0.01'))
        mostExpensiveItem.price =\
            Decimal(mostExpensiveItem.price).\
            quantize(Decimal('0.01'))
    else:
        mostExpensiveItem = DataManager.\
                            getBaseMenuItem(baseMenuItem_id=-1)
        mostExpensiveItem.name = 'N/A'
        mostExpensiveItem.price = 'N/A'

    return render_template('Restaurant.html', restaurant=restaurant, 
                           numMenuItems=numMenuItems,
                           mostExpensiveItem=mostExpensiveItem,
                           cuisine=cuisine, picture=picture, owner=owner,
                           client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/edit/',
           methods=['GET','POST'])
@login_required
def editRestaurant(restaurant_id):
    '''Serve form to add a restaurant menu item to a restaurant's menu
    '''
    restaurant = DataManager.getRestaurant(restaurant_id)

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to edit this restaurant")
        return redirect(url_for('restaurant',
            restaurant_id=restaurant.id))

    client_login_session = getClientLoginSession()

    restaurant = DataManager.getRestaurant(restaurant_id)
    cuisines = DataManager.getCuisines()
    picture = DataManager.getPicture(restaurant.picture_id)
    
    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        oldName = restaurant.name
        oldCuisine = DataManager.\
                     getCuisine(cuisine_id=restaurant.cuisine_id)
        oldPicture = DataManager.getPicture(restaurant.picture_id)
        
        newName = validateUserInput(request.form['name'], 'name',
            'edit', 'restaurant', maxlength=100)

        validCuisineIDs = {}
        for cuisine in cuisines:
            validCuisineIDs[str(cuisine.id)] = True

        # for 'do not change'
        validCuisineIDs['-2'] = True

        newCuisine_id = validateUserInput(request.form['cuisineID'],
                'cuisine_id', 'edit', 'restaurant',
                columnNameForMsg='cuisine', oldInput=str(oldCuisine.id),
                validInputs=validCuisineIDs)  

        if newCuisine_id == '-2':
            newCuisine_id = None

        providedPic = validateUserPicture('edit', 'restaurant',
            file=request.files['pictureFile'],
            link=request.form['pictureLink'], maxlength=300)

        if providedPic is not None:
            # delete the old pic if it was an upload and new is a link
            # or save the new pic if it was an upload
            if (providedPic['serve_type'] == 'link' and
                oldPicture.serve_type == 'upload'):

                path = app.config['UPLOAD_FOLDER']+'/'+oldPicture.text
                os.remove(path)
                flash("deleted old uploaded pic")
            elif providedPic['serve_type'] == 'upload':
                picfilename = 'restaurant' + str(restaurant_id)
                request.files['pictureFile'].save(os.path.\
                    join(app.config['UPLOAD_FOLDER'], picfilename))
                providedPic['text'] = picfilename

            # edit the pic
            DataManager.editPicture(restaurant.picture_id,
                newText=providedPic['text'], 
                newServe_Type=providedPic['serve_type'])

            flash("updated base menu item picture")

        # we edited the pic directly, no need to include here
        DataManager.editRestaurant(restaurant.id,
            newName=newName, newCuisine_id=newCuisine_id)

        restaurant = DataManager.getRestaurant(restaurant_id)

        if newName is not None:
            flash("changed " + restaurant.name + "'s (ID " + \
                str(restaurant.id) + ") name from '" + oldName + \
                "' to '" + newName + "'")

        if newCuisine_id is not None:
            flash("changed " + restaurant.name + "'s (ID " + \
                str(restaurant.id) + ") cuisine")
        
        return redirect(url_for('restaurant',
                                restaurant_id=restaurant_id))
    else:

        return render_template('EditRestaurant.html',
                               restaurant=restaurant,
                               cuisines=cuisines,
                               hiddenToken=login_session['state'],
                               picture=picture,
                               client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteRestaurant(restaurant_id):
    '''Serve form to delete a restaurant
    '''
    restaurant = DataManager.getRestaurant(restaurant_id)

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to delete this restaurant")
        return redirect(url_for('restaurant',
            restaurant_id=restaurant.id))

    client_login_session = getClientLoginSession()

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        restaurantMenuItems = DataManager.\
                    getRestaurantMenuItems(restaurant_id=restaurant_id)

        DataManager.deleteRestaurant(restaurant_id)

        flash("deleted " + str(len(restaurantMenuItems)) + \
            " restaurant menu items from the database")

        flash("deleted restaurant " + str(restaurant.id) + " (" + \
            restaurant.name + ") from the database")
        
        return redirect(url_for('restaurants'))
    else:   
        
        return render_template('DeleteRestaurant.html',
                               restaurant=restaurant,
                               hiddenToken=login_session['state'],
                               client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/menu/')
def restaurantMenu(restaurant_id):
    '''Serve a restaurant's menu
    '''
    restaurant = DataManager.getRestaurant(restaurant_id)

    sectionedItems = DataManager.\
                     getRestaurantMenuItems(restaurant_id=restaurant_id,
                                            byMenuSection=True)

    for menuSection, items in sectionedItems.iteritems():
        for item in items:
            # ensure display nicely formatted
            item.price = Decimal(item.price).quantize(Decimal('0.01'))

    if (isLoggedIn() and
        restaurant.user_id == login_session['user_id']):

        return render_template('PrivateRestaurantMenu.html',
                               restaurant=restaurant,
                               sectionedItems=sectionedItems)
    else:

        return render_template('PublicRestaurantMenu.html',
                               restaurant=restaurant,
                               sectionedItems=sectionedItems)

@app.route('/restaurants/<int:restaurant_id>/menu/add/',
           methods=['GET','POST'])
@login_required
def addRestaurantMenuItem(restaurant_id):
    '''Serve form to add a restaurant menu item to a restaurant's menu
    '''
    restaurant = DataManager.getRestaurant(restaurant_id)

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to add an item to "+\
            " this restaurant's menu")
        return redirect(url_for('restaurantMenu',
            restaurant_id=restaurant.id))  
    
    client_login_session = getClientLoginSession()

    baseMenuItems = DataManager.getBaseMenuItems()

    for item in baseMenuItems:
        pic = DataManager.getPicture(item.picture_id)
        item.picText = pic.text
        item.picServeType = pic.serve_type

    menuSections = DataManager.getMenuSections()

    # display nicely
    for item in baseMenuItems:
        item.price = Decimal(item.price).quantize(Decimal('0.01'))

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        validBaseMenuItemIDs = {}
        for item in baseMenuItems:
            validBaseMenuItemIDs[str(item.id)] = True

        baseMenuItem_id = validateUserInput(request.form['baseMenuItemID'],
            'baseMenuItem_id', 'create', 'restaurant menu item',
            columnNameForMsg='base menu item',
            validInputs=validBaseMenuItemIDs, required=True)

        if baseMenuItem_id is None:
            return redirect(url_for('restaurantMenu', 
                restaurant_id=restaurant_id))

        baseMenuItem = DataManager.\
            getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)

        # if a field is provided, use it, else use the base menu item's attr
        if request.form['name']:

            name = validateUserInput(request.form['name'], 'name', 'create',
                'restaurant menu item', maxlength=80, required=True)
            
            if name is None:
                return redirect(url_for('restaurantMenu', 
                    restaurant_id=restaurant_id))   
        else:

            name = baseMenuItem.name

        if request.form['description']:
        
            description = validateUserInput(request.form['description'],
                'description', 'create', 'restaurant menu item',
                maxlength=250, required=True)

            if description is None:
                return redirect(url_for('restaurantMenu', 
                    restaurant_id=restaurant_id))   
        else:

            description = baseMenuItem.description

        if request.form['price']:

            price = validateUserInput(request.form['price'], 'price', 
                'create', 'restaurant menu item', maxlength=20, 
                required=True, priceFormat=True)

            if price is None:
                return redirect(url_for('restaurantMenu', 
                    restaurant_id=restaurant_id))  
        else:

            price = baseMenuItem.price 

        if request.files['pictureFile'] or request.form['pictureLink']:
        
            providedPic = validateUserPicture('create', 'restaurant menu item',
                file=request.files['pictureFile'],
                link=request.form['pictureLink'],
                maxlength=300, required=True)

            if providedPic is None:
                return redirect(url_for('restaurantMenu', 
                    restaurant_id=restaurant_id))  
            else:           

                picture_id = DataManager.\
                    addPicture(text=providedPic['text'], 
                        serve_type=providedPic['serve_type'])
        else:

            picture_id = baseMenuItem.picture_id

        validMenuSectionIDs = {}
        for menuSection in menuSections:
            validMenuSectionIDs[str(menuSection.id)] = True

        # if this is somehow None, 
        # the add function defaults to base item's attr
        menuSection_id = validateUserInput(request.form['menuSectionID'],
            'menuSection_id', 'create', 'restaurant menu item',
            columnNameForMsg='menu section',
            validInputs=validMenuSectionIDs, required=True)

        restaurantMenuItem_id = DataManager.\
            addRestaurantMenuItem(name=name, restaurant_id=restaurant_id,
            description=description, price=price,
            baseMenuItem_id=baseMenuItem_id, picture_id=picture_id,
            menuSection_id=menuSection_id)

        # if pic was uploaded, now that we know item id, 
        # save actual file for serving and set the name in the database
        if (request.files['pictureFile'] and
            providedPic['serve_type'] == 'upload'):

            picfilename = 'restaurantMenuItem' + str(restaurantMenuItem_id)
            request.files['pictureFile'].save(os.path.\
                join(app.config['UPLOAD_FOLDER'], picfilename))
            DataManager.editPicture(picture_id=picture_id,
                                          newText=picfilename)

        flash("menu item '" + name + "' added to the menu!")

        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:

        return render_template('AddRestaurantMenuItem.html',
                               restaurant=restaurant,
                               baseMenuItems=baseMenuItems,
                               menuSections=menuSections,
                               hiddenToken=login_session['state'],
                               client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/')
@login_required
def restaurantMenuItem(restaurant_id, restaurantMenuItem_id):
    '''Serve a restaurant menu item
    '''
    restaurant = DataManager.getRestaurant(restaurant_id)

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to view this item's details")
        return redirect(url_for('restaurantMenu',
            restaurant_id=restaurant.id))  
    
    client_login_session = getClientLoginSession()

    restaurantMenuItem = DataManager.\
                         getRestaurantMenuItem(restaurantMenuItem_id)
    restaurantMenuItem.price = Decimal(restaurantMenuItem.price).\
        quantize(Decimal('0.01'))

    restaurantCuisineObj = DataManager.\
                           getCuisine(cuisine_id=restaurant.cuisine_id)
    restaurantCuisine = restaurantCuisineObj.name
    restaurantMenuItemSection = DataManager.\
        getMenuSection(menuSection_id=restaurantMenuItem.menuSection_id)

    baseMenuItem = DataManager.\
        getBaseMenuItem(baseMenuItem_id=restaurantMenuItem.baseMenuItem_id)
    baseMenuItem.price = Decimal(baseMenuItem.price).quantize(Decimal('0.01'))
    baseMenuItemCuisineObj = DataManager.\
                             getCuisine(cuisine_id=baseMenuItem.cuisine_id)
    baseMenuItemCuisine = baseMenuItemCuisineObj.name

    baseMenuItemSection = DataManager.\
        getMenuSection(menuSection_id=baseMenuItem.menuSection_id)

    picture = DataManager.getPicture(restaurantMenuItem.picture_id)

    timesOrdered = 0

    return render_template("RestaurantMenuItem.html",
                    restaurantMenuItem=restaurantMenuItem,
                    restaurant=restaurant,
                    restaurantCuisine=restaurantCuisine,
                    baseMenuItem=baseMenuItem,
                    baseMenuItemCuisine=baseMenuItemCuisine,
                    timesOrdered=timesOrdered,
                    picture=picture,
                    restaurantMenuItemSection=restaurantMenuItemSection,
                    baseMenuItemSection=baseMenuItemSection,
                    client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/edit/',
           methods=['GET','POST'])
@login_required
def editRestaurantMenuItem(restaurant_id, restaurantMenuItem_id):
    '''Serve a form to edit a restaurant menu item
    '''
    restaurant = DataManager.getRestaurant(restaurant_id)

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to edit this item")
        return redirect(url_for('restaurantMenu',
            restaurant_id=restaurant.id))  
    
    client_login_session = getClientLoginSession()

    user_id = restaurant.user_id
    restaurantMenuItem = DataManager.\
        getRestaurantMenuItem(restaurantMenuItem_id)

    restaurantMenuItem.price = Decimal(restaurantMenuItem.price).\
        quantize(Decimal('0.01'))
    
    picture = DataManager.getPicture(restaurantMenuItem.picture_id)

    menuSections = DataManager.getMenuSections()

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        oldName = restaurantMenuItem.name
        oldDescription = restaurantMenuItem.description
        oldPrice = restaurantMenuItem.price
        oldMenuSection_id = restaurantMenuItem.menuSection_id
        oldPicture = picture

        newName = validateUserInput(request.form['name'], 'name',
            'edit', 'restaurant menu item', maxlength=80, oldInput=oldName)
        
        newDescription = validateUserInput(request.form['description'],
            'description', 'edit', 'restaurant menu item', maxlength=250,
            oldInput=oldDescription)
            
        newPrice = validateUserInput(request.form['price'], 'price',
            'edit', 'restaurant menu item', maxlength=20, 
            oldInput=oldPrice, priceFormat=True)
            
        validMenuSectionIDs = {}
        for menuSection in menuSections:
            validMenuSectionIDs[str(menuSection.id)] = True

        # for 'do not change'
        validMenuSectionIDs['-1'] = True

        newMenuSection_id = validateUserInput(request.form['menuSection'],
                'menuSection_id', 'edit', 'restaurant menu item',
                columnNameForMsg='menu section',
                oldInput=str(oldMenuSection_id),
                validInputs=validMenuSectionIDs)

        if newMenuSection_id == '-1':
            newMenuSection_id = None

        providedPic = validateUserPicture('edit', 'restaurant menu item',
            file=request.files['pictureFile'], 
            link=request.form['pictureLink'], maxlength=300)

        if providedPic is not None:
            # delete the old pic if it was an upload and new is a link
            # or save the new pic if it was an upload
            if (providedPic['serve_type'] == 'link' and
                oldPicture.serve_type == 'upload'):
            
                path = app.config['UPLOAD_FOLDER']+'/'+oldPicture.text
                os.remove(path)
                flash("deleted old uploaded pic")
            elif providedPic['serve_type'] == 'upload':

                picfilename = 'restaurantMenuItem' + \
                    str(restaurantMenuItem_id)
                request.files['pictureFile'].save(os.path.\
                    join(app.config['UPLOAD_FOLDER'], picfilename))
                providedPic['text'] = picfilename

            # edit the pic
            DataManager.editPicture(restaurantMenuItem.picture_id,
                newText=providedPic['text'], 
                newServe_Type=providedPic['serve_type'])

            flash("updated restaurant menu item picture")

        # we edited the pic directly, no need to include here
        DataManager.editRestaurantMenuItem(restaurantMenuItem.id,
            newName=newName, newDescription=newDescription, 
            newPrice=newPrice, newMenuSection_id=newMenuSection_id)

        if newName is not None:
            flash("changed restaurant menu item " + \
                str(restaurantMenuItem.id) + \
                "'s name from '" + oldName + "' to '" + newName + "'")

        if newDescription is not None:
            flash("changed restaurant menu item " + \
                str(restaurantMenuItem.id) + \
                "'s description from '"+ oldDescription + "' to '" + \
                newDescription + "'")

        if newPrice is not None:
            flash("changed restaurant menu item " + \
                str(restaurantMenuItem.id) + \
                "'s price from '" + str(oldPrice) + "' to '" + \
                str(newPrice) + "'")

        if newMenuSection_id is not None:
            flash("changed the restaurant menu item's menu section")

        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:

        return render_template('EditRestaurantMenuItem.html',
                               restaurant=restaurant,
                               restaurantMenuItem=restaurantMenuItem,
                               menuSections=menuSections,
                               hiddenToken=login_session['state'],
                               picture=picture,
                               client_login_session=client_login_session)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:restaurantMenuItem_id>/delete/',
           methods=['GET','POST'])
@login_required
def deleteRestaurantMenuItem(restaurant_id, restaurantMenuItem_id):
    '''Serve a form to delete a restaurant menu item
    '''
    restaurant = DataManager.getRestaurant(restaurant_id)

    if restaurant.user_id != login_session['user_id']:

        flash("You do not have permission to delete this item")
        return redirect(url_for('restaurantMenu',
            restaurant_id=restaurant.id))  
    
    client_login_session = getClientLoginSession()

    restaurantMenuItem = DataManager.\
                         getRestaurantMenuItem(restaurantMenuItem_id)

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        restaurantMenuItemName = restaurantMenuItem.name

        DataManager.\
            deleteRestaurantMenuItem(restaurantMenuItem_id=\
                restaurantMenuItem_id)

        flash("removed item " + str(restaurantMenuItem_id) + " (" + \
              restaurantMenuItemName + ") from the menu and database")

        return redirect(url_for('restaurantMenu',
                                restaurant_id=restaurant_id))
    else:
        return render_template('DeleteRestaurantMenuItem.html',
                               restaurant=restaurant,
                               restaurantMenuItem=restaurantMenuItem,
                               hiddenToken=login_session['state'],
                               client_login_session=client_login_session)
