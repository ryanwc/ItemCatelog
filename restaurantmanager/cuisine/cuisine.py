from flask import (Blueprint, render_template, request, redirect, 
    url_for, flash, session as login_session)

import os, requests
from decimal import Decimal

from restaurantmanager import DataManager
from restaurantmanager.utils import (getClientLoginSession, isLoggedIn, 
    isCSRFAttack, validateUserInput, validateUserPicture)
from restaurantmanager import app


cuisine_bp = Blueprint('cuisine', __name__, 
    template_folder='templates', static_folder='static')

@app.route('/cuisines/')
def cuisines():
    ''' Display all cuisines
    '''
    cuisines = DataManager.getCuisines()

    client_login_session = getClientLoginSession()

    return render_template("Cuisines.html", cuisines=cuisines,
                           client_login_session=client_login_session)

@app.route('/cuisines/add/', methods=['GET', 'POST'])
def addCuisine():
    '''Serve form for adding a cuisine to the database
    '''
    if not isLoggedIn():

        flash("You must log in to add a cuisine")
        return redirect(url_for('restaurantManagerIndex'))

    client_login_session = getClientLoginSession()

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        name = validateUserInput(request.form['name'],
            'name', 'create', 'cuisine', maxlength=80, 
            required=True, unique=True)

        if name is None:
            return redirect(url_for('cuisines'))

        DataManager.addCuisine(name)

        flash("Added cuisine '" + name + "' to the database!")

        return redirect(url_for('cuisines'))
    else:

        return render_template('AddCuisine.html',
                               hiddenToken=login_session['state'],
                               client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/')
def cuisine(cuisine_id):
    '''Serve cuisine info page
    '''
    cuisine = DataManager.getCuisine(cuisine_id=cuisine_id)
    restaurants = DataManager.\
                  getRestaurants(cuisine_id=cuisine_id)
    baseMenuItems = DataManager.\
                    getBaseMenuItems(cuisine_id=cuisine_id)
    restaurantMenuItems = DataManager.\
        getRestaurantMenuItems(cuisine_id=cuisine_id)
    sectionedBaseMenuItems = DataManager.\
                             getBaseMenuItems(cuisine_id=cuisine_id,
                                              byMenuSection=True)

    client_login_session = getClientLoginSession()

    # get restaurants labeled with user or non-user
    restaurantDicts = {}
    for restaurant in restaurants:
        restaurantDict = {}
        restaurantDict = {'restaurant': restaurant}

        if (isLoggedIn() and 
            restaurant.user_id == login_session['user_id']):
            restaurantDict['ownership'] = 'user'
        else:
            restaurantDict['ownership'] = 'non-user'

        restaurantDicts[restaurant.id] = restaurantDict

    # get the base items with their children 
    # in format that plays nice with jinja
    # and labels things user or non-user
    # and also calculate some data about the items
    mostExpensiveBaseMenuItem = DataManager.\
    getBaseMenuItem(baseMenuItem_id=-1)

    mostExpensiveRestaurantMenuItem = DataManager.\
        getBaseMenuItem(baseMenuItem_id=-1)

    sectionedBaseItemsWithChildren = {}

    for section, baseItemList in sectionedBaseMenuItems.iteritems():

        sectionedBaseItemsWithChildren[section] = {}

        for baseItem in baseItemList:

            baseItemID = baseItem.id

            if baseItem.price > mostExpensiveBaseMenuItem.price:
                mostExpensiveBaseMenuItem = baseItem

            childrenItems = DataManager.\
                getRestaurantMenuItems(baseMenuItem_id=baseItem.id)
            children = {}

            for item in childrenItems:

                if item.price > mostExpensiveRestaurantMenuItem.price:
                    mostExpensiveRestaurantMenuItem = item

                itemRestaurant = DataManager.\
                                 getRestaurant(item.restaurant_id)
                itemUserID = itemRestaurant.user_id
                child = {}
                child['item'] = item

                if (isLoggedIn() and
                    itemUserID == login_session['user_id']):
                    child['ownership'] = 'user'
                else:
                    child['ownership'] = 'non-user'

                children[item.id] = child

            itemWithChildren = {'item':baseItem, 'children':children}
            sectionedBaseItemsWithChildren[section][baseItem.id] = \
                itemWithChildren

    # this means there were no items, so display N/A
    if mostExpensiveRestaurantMenuItem.id == -1:
        mostExpensiveRestaurantMenuItem.name = "N/A"
        mostExpensiveRestaurantMenuItem.price = "N/A"
        mostExpensiveRestaurantMenuItem.restaurant_id = "N/A"
    else:
        # display nicely
        mostExpensiveRestaurantMenuItem.price = \
            Decimal(mostExpensiveRestaurantMenuItem.price).\
            quantize(Decimal('0.01'))

    if mostExpensiveBaseMenuItem.id == -1:
        mostExpensiveBaseMenuItem.name = "N/A"
        mostExpensiveBaseMenuItem.price = "N/A"
    else:
        mostExpensiveBaseMenuItem.price = \
            Decimal(mostExpensiveBaseMenuItem.price).\
            quantize(Decimal('0.01'))

    return render_template("Cuisine.html",
        cuisine=cuisine,
        mostExpensiveBaseMenuItem=mostExpensiveBaseMenuItem,
        mostExpensiveRestaurantMenuItem=mostExpensiveRestaurantMenuItem,
        restaurantDicts=restaurantDicts,
        sectionedBaseItemsWithChildren=sectionedBaseItemsWithChildren,
        client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/edit/', methods=['GET', 'POST'])
def editCuisine(cuisine_id):
    '''Serve form to edit a cuisine
    '''
    if not isLoggedIn():

        flash("You must log in to edit a cuisine")
        return redirect(url_for('restaurantManagerIndex'))
    
    client_login_session = getClientLoginSession()

    cuisine = DataManager.getCuisine(cuisine_id=cuisine_id)

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        oldName = cuisine.name

        newName = validateUserInput(request.form['name'],
            'name', 'edit', 'cuisine', maxlength=80, unique=True, 
            oldInput=oldName, tableName='Cuisine')

        DataManager.editCuisine(cuisine_id, newName=newName)
        
        if newName is not None:
            
            flash("Changed cuisine's name from '" + oldName +\
                "' to '" + newName + "'")

        return redirect(url_for('cuisine',
                                cuisine_id=cuisine_id))
    else:
        return render_template("EditCuisine.html",
                               cuisine=cuisine,
                               hiddenToken=login_session['state'],
                               client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/delete/', methods=['GET', 'POST'])
def deleteCuisine(cuisine_id):
    '''Serve form to delete a cuisine
    '''
    if not isLoggedIn():

        flash("You must log in to delete a cuisine")
        return redirect(url_for('restaurantManagerIndex'))
    
    client_login_session = getClientLoginSession()

    cuisine = DataManager.getCuisine(cuisine_id=cuisine_id)

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        # all of this is for flash messaging
        cuisineName = cuisine.name
        cuisineID = cuisine.id
        restaurantMenuItems = DataManager.\
                              getRestaurantMenuItems(cuisine_id=cuisine_id)
        numItemsReassigned = len(restaurantMenuItems)
        restaurants = DataManager.\
                      getRestaurants(cuisine_id=cuisine_id)
        numRestaurantsReassigned = len(restaurants)
        baseMenuItems = DataManager.\
                        getBaseMenuItems(cuisine_id=cuisine_id)
        numItemsDeleted = len(baseMenuItems)
        itemBaseForNoCuisine = DataManager.\
            getBaseMenuItem(baseMenuItem_id=-1)

        # here is the logic
        restaurantBaseForNoCuisine = DataManager.\
                                     getCuisine(cuisine_id=-1)

        DataManager.deleteCuisine(cuisine_id)

        flash("reassigned " + str(numItemsReassigned) + \
            " restaurant menu items' base item to '" + \
            itemBaseForNoCuisine.name + "'")

        flash("reassigned " + str(numRestaurantsReassigned) + \
            " restaurants' cuisine to '" + \
            restaurantBaseForNoCuisine.name + "'")

        flash("deleted " + str(numItemsDeleted) + \
            " base menu items from the database")

        flash("deleted cuisine " + str(cuisineID) + " (" + \
            cuisineName + ") from the database")

        return redirect(url_for('cuisines'))
    else:
        return render_template("DeleteCuisine.html",
                               cuisine=cuisine,
                               hiddenToken=login_session['state'],
                               client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/add/', methods=['GET','POST'])
def addBaseMenuItem(cuisine_id):
    '''Serve form to add a base menu item
    '''
    if not isLoggedIn():

        flash("You must log in to add a base menu item")
        return redirect(url_for('restaurantManagerIndex'))
    
    client_login_session = getClientLoginSession()

    cuisine = DataManager.getCuisine(cuisine_id=cuisine_id)
    menuSections = DataManager.getMenuSections()

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        name = validateUserInput(request.form['name'],
            'name', 'create', 'base menu item', maxlength=80, 
            required=True, unique=True, tableName='BaseMenuItem')

        if name is None:
            return redirect(url_for('cuisine', cuisine_id=cuisine.id))

        description = \
            validateUserInput(request.form['description'],
                'description', 'create', 'base menu item',
                maxlength=250, required=True)

        if description is None:
            return redirect(url_for('cuisine', cuisine_id=cuisine.id))

        price = validateUserInput(request.form['price'],
            'price', 'create', 'base menu item', maxlength=20,
            required=True, priceFormat=True)

        if price is None:
            return redirect(url_for('cuisine', cuisine_id=cuisine.id))

        validMenuSectionIDs = {}
        for menuSection in menuSections:
            validMenuSectionIDs[str(menuSection.id)] = True

        menuSection_id = validateUserInput(request.form['menuSection'],
                'menuSection_id', 'create', 'base menu item',
                columnNameForMsg='menu section', required=True, 
                validInputs=validMenuSectionIDs)

        if menuSection_id is None:
            return redirect(url_for('cuisine', cuisine_id=cuisine.id))

        providedPic = validateUserPicture('create', 'base menu item',
            file=request.files['pictureFile'],
            link=request.form['pictureLink'],
            maxlength=300, required=True)

        if providedPic is None:
            return redirect(url_for('cuisine', cuisine_id=cuisine.id))
        
        picture_id = DataManager.addPicture(text=providedPic['text'], 
            serve_type=providedPic['serve_type'])

        baseMenuItem_id = DataManager.\
            addBaseMenuItem(name, cuisine_id, description=description, 
            price=price, menuSection_id=menuSection_id, 
            picture_id=picture_id)

        # if pic was uploaded, now that we know item id, 
        # save actual file for serving and set the name in the database
        if providedPic['serve_type'] == 'upload':
            picfilename = 'baseMenuItem' + str(baseMenuItem_id)
            request.files['pictureFile'].save(os.path.\
                join(app.config['UPLOAD_FOLDER'], picfilename))
            DataManager.editPicture(picture_id=picture_id,
                                          newText=picfilename)

        flash("added '" + name + "' to " + cuisine.name + \
            "'s base menu")

        return redirect(url_for('cuisine', cuisine_id=cuisine.id))
    else:
        return render_template('AddBaseMenuItem.html',
                            cuisine=cuisine,
                            menuSections=menuSections,
                            hiddenToken=login_session['state'],
                            client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/')
def baseMenuItem(cuisine_id, baseMenuItem_id):
    '''Serve a base menu item
    '''
    client_login_session = getClientLoginSession()

    baseMenuItem = DataManager.\
        getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)
    baseMenuItem.price = Decimal(baseMenuItem.price).\
        quantize(Decimal('0.01'))
    cuisine = DataManager.\
        getCuisine(cuisine_id=baseMenuItem.cuisine_id)
    restaurantMenuItems = DataManager.\
        getRestaurantMenuItems(baseMenuItem_id=baseMenuItem.id)
    picture = DataManager.getPicture(baseMenuItem.picture_id)
    menuSection = DataManager.\
        getMenuSection(menuSection_id=baseMenuItem.menuSection_id)
    timesOrdered = 0

    return render_template("BaseMenuItem.html",
                            baseMenuItem=baseMenuItem,
                            restaurantMenuItems=restaurantMenuItems,
                            cuisine=cuisine,
                            timesOrdered=timesOrdered,
                            picture=picture,
                            menuSection=menuSection,
                            client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/edit/',
           methods=['POST','GET'])
def editBaseMenuItem(cuisine_id, baseMenuItem_id):
    '''Serve form to edit a base menu item
    '''
    if not isLoggedIn():

        flash("You must log in to edit a base menu item")
        return redirect(url_for('restaurantManagerIndex'))
    
    client_login_session = getClientLoginSession()

    baseMenuItem = DataManager.\
                   getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)
    cuisine = DataManager.getCuisine(cuisine_id=cuisine_id)

    baseMenuItem.price = Decimal(baseMenuItem.price).quantize(Decimal('0.01'))

    picture = DataManager.getPicture(baseMenuItem.picture_id)

    menuSections = DataManager.getMenuSections()

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        oldName = baseMenuItem.name
        oldDescription = baseMenuItem.description
        oldPrice = baseMenuItem.price
        oldPicture = picture
        oldMenuSection_id = baseMenuItem.menuSection_id
        
        newName = validateUserInput(request.form['name'], 'name', 
            'edit', 'base menu item', maxlength=80, 
            unique=True, oldInput=oldName)
            
        newDescription = validateUserInput(request.form['description'],
            'description', 'edit', 'base menu item', maxlength=250,
            oldInput=oldDescription)

        newPrice = validateUserInput(request.form['price'], 'price',
            'edit', 'base menu item', maxlength=20,
            priceFormat=True, oldInput=str(oldPrice))

        validMenuSectionIDs = {}
        for menuSection in menuSections:
            validMenuSectionIDs[str(menuSection.id)] = True

        # for 'do not change'
        validMenuSectionIDs['-1'] = True

        newMenuSection_id = validateUserInput(request.form['menuSection'],
                'menuSection_id', 'edit', 'base menu item',
                columnNameForMsg='menu section',
                oldInput=str(oldMenuSection_id),
                validInputs=validMenuSectionIDs)

        if newMenuSection_id == '-1':
            newMenuSection_id = None

        providedPic = validateUserPicture('edit', 'base menu item',
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

                picfilename = 'baseMenuItem' + str(baseMenuItem_id)
                request.files['pictureFile'].save(os.path.\
                    join(app.config['UPLOAD_FOLDER'], picfilename))
                providedPic['text'] = picfilename

            # edit the pic
            DataManager.editPicture(baseMenuItem.picture_id,
                newText=providedPic['text'], 
                newServe_Type=providedPic['serve_type'])

            flash("updated base menu item picture")

        # we edited the pic directly, no need to include here
        DataManager.editBaseMenuItem(baseMenuItem.id,
            newName=newName, newDescription=newDescription, 
            newPrice=newPrice, newMenuSection_id=newMenuSection_id)

        if newName is not None:
            flash("changed name from '"+oldName+"' to '"+newName+"'")

        if newDescription is not None:
            flash("changed description from '"+ oldDescription + "' to '" + \
                newDescription + "'")

        if newPrice is not None:
            flash("changed price from '" + str(oldPrice) + "' to '" + \
                str(newPrice) + "'")

        if newMenuSection_id is not None:
            flash("changed menu section")

        return redirect(url_for('baseMenuItem',
                                cuisine_id=cuisine_id,
                                baseMenuItem_id=baseMenuItem_id))
    else:
        return render_template("EditBaseMenuItem.html",
                               baseMenuItem=baseMenuItem,
                               cuisine=cuisine,
                               hiddenToken=login_session['state'],
                               picture=picture,
                               menuSections=menuSections,
                               client_login_session=client_login_session)

@app.route('/cuisines/<int:cuisine_id>/<int:baseMenuItem_id>/delete/',
           methods=['GET','POST'])
def deleteBaseMenuItem(cuisine_id, baseMenuItem_id):
    '''Serve form to delete a base menu item
    '''
    if not isLoggedIn():

        flash("You must log in to delete a base menu item")
        return redirect(url_for('restaurantManagerIndex'))
    
    client_login_session = getClientLoginSession()

    baseMenuItem = DataManager.\
                   getBaseMenuItem(baseMenuItem_id=baseMenuItem_id)

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        cuisine = DataManager.getCuisine(cuisine_id=cuisine_id)
        restaurantMenuItems = DataManager.\
            getRestaurantMenuItems(baseMenuItem_id=baseMenuItem_id)
        baseForNoCuisine = DataManager.\
            getBaseMenuItem(baseMenuItem_id=-1)

        DataManager.deleteBaseMenuItem(baseMenuItem_id=baseMenuItem_id)

        flash("reassigned " + str(len(restaurantMenuItems)) + \
            " restaurant menu items' base to '" +\
            baseForNoCuisine.name + "'")
        flash("deleted " + baseMenuItem.name + " from " +\
            cuisine.name + "'s base menu and from the database")

        return redirect(url_for('cuisine',cuisine_id=cuisine_id))
    else:

        return render_template("DeleteBaseMenuItem.html",
                            baseMenuItem=baseMenuItem,
                            cuisine_id=cuisine_id,
                            hiddenToken=login_session['state'],
                            client_login_session=client_login_session)
