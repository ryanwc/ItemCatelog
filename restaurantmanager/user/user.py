from flask import (Blueprint, render_template, request, redirect, 
    url_for, flash, session as login_session)

import os, requests
from decimal import Decimal

from restaurantmanager import DataManager, app
from restaurantmanager.utils import (getClientLoginSession, isLoggedIn, 
    isCSRFAttack, validateUserInput, validateUserPicture)
from restaurantmanager.home.home import login_required


user_bp = Blueprint('user', __name__, 
    template_folder='templates', static_folder='static')

@app.route('/users/', methods=['GET'])
def users():
    '''Serve information about all users
    '''
    client_login_session = getClientLoginSession()

    users = DataManager.getUsers()

    return render_template('Users.html', users=users,
                           client_login_session=client_login_session)

@app.route('/users/<int:user_id>/', methods=['GET'])
def user(user_id):
    '''Serve a user's profile
    '''
    client_login_session = getClientLoginSession()

    user = DataManager.getUser(user_id=user_id)
    picture = DataManager.getPicture(user.picture_id)
    userThings = DataManager.getUserThings(user.id)

    # calculate some stats to show
    loggedInStats = {}

    numRestaurants = 0

    mostExpensiveRest = None
    mostExpensiveRestAvgPrice = None
    leastExpensiveRest = None
    leastExpensiveRestAvgPrice = None

    numMenuItems = 0

    mostExpensiveMenuItem = None
    leastExpensiveMenuItem = None

    for restaurantID in userThings:

        numRestaurants = numRestaurants + 1
        numItemsThisRestaurant = 0
        totalRestaurantPrices = 0
        thisRestaurantAvgItemPrice = None

        for menuSectionName in userThings[restaurantID]['items']:

            for item in userThings[restaurantID]['items'][menuSectionName]:

                item.price = Decimal(item.price).\
                    quantize(Decimal('0.01'))
                numMenuItems = numMenuItems + 1
                numItemsThisRestaurant = numItemsThisRestaurant + 1

                if mostExpensiveMenuItem is None:
                    mostExpensiveMenuItem = item
                elif item.price > mostExpensiveMenuItem.price:
                    mostExpensiveMenuItem = item
                elif (leastExpensiveMenuItem is None and
                    numMenuItems > 1):
                    leastExpensiveMenuItem = item
                elif (item.price < leastExpensiveMenuItem.price and
                      numMenuItems > 1):
                    leastExpensiveMenuItem = item

                totalRestaurantPrices = totalRestaurantPrices + item.price

        if numItemsThisRestaurant > 0:
            thisRestaurantAvgItemPrice = \
                totalRestaurantPrices/numItemsThisRestaurant
        else:
            thisRestaurantAvgItemPrice = None

        if (mostExpensiveRest is None and
            numItemsThisRestaurant > 0):

            mostExpensiveRest = \
                userThings[restaurantID]['restaurant']
            mostExpensiveRestAvgPrice = thisRestaurantAvgItemPrice

        elif thisRestaurantAvgItemPrice > mostExpensiveRestAvgPrice:

            mostExpensiveRest = \
                userThings[restaurantID]['restaurant']
            mostExpensiveRestAvgPrice = thisRestaurantAvgItemPrice
        elif (leastExpensiveRest is None and
              numRestaurants > 1 and
              numItemsThisRestaurant > 0):
            leastExpensiveRest = \
                userThings[restaurantID]['restaurant']
            leastExpensiveRestAvgPrice = thisRestaurantAvgItemPrice
        elif (thisRestaurantAvgItemPrice < \
                leastExpensiveRestAvgPrice and
              numRestaurants > 1):
            leastExpensiveRest = \
                userThings[restaurantID]['restaurant']
            leastExpensiveRestAvgPrice = thisRestaurantAvgItemPrice

    if mostExpensiveRestAvgPrice:
        mostExpensiveRestAvgPrice = \
            Decimal(mostExpensiveRestAvgPrice).\
            quantize(Decimal('0.01'))
    
    if leastExpensiveRestAvgPrice:
        leastExpensiveRestAvgPrice = \
            Decimal(leastExpensiveRestAvgPrice).\
            quantize(Decimal('0.01'))

    if (isLoggedIn() and
        login_session['user_id'] == user.id):
        # could put stats in a loginStats dictionary
        return render_template('PrivateUserProfile.html',
            user=user, picture=picture, userThings=userThings,
            numRestaurants=numRestaurants, numMenuItems=numMenuItems,
            mostExpensiveRest=mostExpensiveRest,
            mostExpensiveRestAvgPrice=mostExpensiveRestAvgPrice,
            leastExpensiveRest=leastExpensiveRest,
            leastExpensiveRestAvgPrice=leastExpensiveRestAvgPrice,
            mostExpensiveMenuItem=mostExpensiveMenuItem,
            leastExpensiveMenuItem=leastExpensiveMenuItem,
            client_login_session=client_login_session)
    else:

        return render_template('PublicUserProfile.html',
            user=user, picture=picture, userThings=userThings,
            numRestaurants=numRestaurants, numMenuItems=numMenuItems,
            client_login_session=client_login_session)

@app.route('/users/<int:user_id>/edit/', methods=['GET','POST'])
@login_required
def editUser(user_id):
    '''Serve a form to edit a user
    '''
    user = DataManager.getUser(user_id)

    if user.id != login_session['user_id']:

        flash("You do not have permission to edit this profile")
        return redirect(url_for('user', user_id=user.id))  
    
    client_login_session = getClientLoginSession()

    picture = DataManager.getPicture(user.picture_id)

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        oldName = user.name
        oldPicture = picture
        
        newName = validateUserInput(request.form['name'], 'name',
            'edit', 'user', maxlength=30, oldInput=oldName,
            usernameFormat=True)       

        providedPic = validateUserPicture('edit', 'user',
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

                picfilename = 'user' + str(user_id)
                request.files['pictureFile'].save(os.path.\
                    join(app.config['UPLOAD_FOLDER'], picfilename))
                providedPic['text'] = picfilename
            
            # edit the pic
            DataManager.editPicture(user.picture_id,
                newText=providedPic['text'], 
                newServe_Type=providedPic['serve_type'])

            picture = DataManager.getPicture(user.picture_id)

            login_session['picture'] = picture.text
            login_session['picture_serve_type'] = picture.serve_type
            flash("updated your picture!")

        # we edited the pic directly, no need to include here
        DataManager.editUser(user.id, newName=newName)

        if newName is not None:

            login_session['username'] = newName
            flash("changed your username from '" + oldName +\
                "' to '"+newName+"'")

        return redirect(url_for('user', user_id=user.id))
    else:

        return render_template('EditUser.html',
                           user=user,
                           picture=picture,
                           hiddenToken=login_session['state'],
                           client_login_session=client_login_session)

@app.route('/users/<int:user_id>/delete/', methods=['GET','POST'])
@login_required
def deleteUser(user_id):
    '''Serve a form to delete a user
    '''
    user = DataManager.getUser(user_id)

    if user.id != login_session['user_id']:

        flash("You do not have permission to delete this profile")
        return redirect(url_for('user', user_id=user.id))  
    
    client_login_session = getClientLoginSession()

    if request.method == 'POST':

        if isCSRFAttack(request.form['hiddenToken']):
            return redirect(url_for('restaurantManagerIndex'))

        DataManager.deleteUser(user.id)

        flash("deleted " + user.name + " from " +\
            "the database")

        # this is messy but needed because even though disconnect() -- which
        # deletes all of this information (confirmed with print statements) -- 
        # has already run on "onsubmit" with submission of this form,
        # the login_session mysteriously still has all of this information
        del login_session['credentials']
        del login_session['user_id']
        del login_session['username']
        del login_session['picture']
        del login_session['email']
        del login_session['picture_serve_type']
        if 'gplus_id' in login_session:
            del login_session['gplus_id']
        elif 'facebook_id' in login_session:
            del login_session['facebook_id']

        return redirect(url_for('users'))

    return render_template('DeleteUser.html',
                           user=user,
                           hiddenToken=login_session['state'],
                           client_login_session=client_login_session)