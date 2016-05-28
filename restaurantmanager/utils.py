from flask import flash, session as login_session
from werkzeug import secure_filename

from restaurantmanager.api.api import (usersJSON, picturesJSON, cuisinesJSON, 
    baseMenuItemsJSON,restaurantsJSON, allRestaurantMenuItemsJSON, 
    menuSectionsJSON)

from . import DataManager

import bleach, json


def writeTablesToJSON(path):
    '''Write all of the tables in the database to .json files
    in the specified directory.

    NOTE: This will only write Picture columns, not the uploaded file
        that column 'text' of a picture with serve_type='upload' points to.
    '''
    tableJSONendpoints = [{'func':usersJSON, 'name':'User'},
                          {'func':picturesJSON, 'name':'Picture'},
                          {'func':cuisinesJSON, 'name':'Cuisine'},
                          {'func':baseMenuItemsJSON, 'name':'BaseMenuItem'},
                          {'func':restaurantsJSON, 'name':'Restaurant'}, 
                          {'func':allRestaurantMenuItemsJSON, 'name':'RestaurantMenuItem'},
                          {'func':menuSectionsJSON, 'name':'MenuSection'}]

    for table in tableJSONendpoints:
        func = table['func']
        response = func()
        data = response.data
        name = func.__name__
        name = name[:-4]
        file = open(path+table['name']+'.json', 'w')
        file.write(data)
        file.close()

def allowed_pic(filename):
    '''Return true if the file name is a valid pic filename
    '''
    return ('.' in filename and 
            filename.rsplit('.', 1)[1] in ALLOWED_PIC_EXTENSIONS)

def isLoggedIn():
    '''Return true if the user is logged in
    '''
    return ('credentials' in login_session and
            'access_token' in login_session['credentials'] and
            'user_id' in login_session)

def setProfile():
    '''Populate the login session with the logged in user's settings
    '''
    user = DataManager.getUser(email=login_session['email'])

    # create the user if the user doesn't exist
    if user is None:
        picture_id = DataManager.\
            addPicture(text=login_session['picture'], serve_type='link')
        DataManager.addUser(name=login_session['username'],
                                  email=login_session['email'],
                                  picture_id=picture_id)
        user = DataManager.getUser(email=login_session['email'])

    # set this user's saved settings for our app
    picture = DataManager.getPicture(user.picture_id)

    login_session['user_id'] = user.id
    login_session['username'] = user.name
    login_session['picture'] = picture.text
    login_session['picture_serve_type'] = picture.serve_type

def getSignInAlert():
    ''' Return a JSON-format object representing a successful signin
    '''
    outputDict = {}

    outputDict['loginMessage'] = "Welcome, " + \
        login_session['username'] + "!"
    outputDict['picture'] = login_session['picture']
    outputDict['picture_serve_type'] = login_session['picture_serve_type']

    flash("you are now logged in as %s" % login_session['username'])

    return json.dumps(outputDict)

def getClientLoginSession():
    ''' Return a dict with entries for setting dynamic client-side content

    Also avoids passing all of current session.
    '''
    client_login_session = {}
    client_login_session['username'] = ""
    client_login_session['user_id'] = -99
    client_login_session['message'] = 'Not logged in'

    if isLoggedIn():

        client_login_session['username'] = login_session['username']
        client_login_session['user_id'] = login_session['user_id']
        client_login_session['message'] = "Logged in as " + \
            login_session['username']

    return client_login_session

###
### Form validation
###

def isCSRFAttack(currentState):
    '''Validate the request came from the same session that logged in
    at the homepage.
    '''
    if currentState != login_session['state']:
        flash("An unknown error occurred.  Sorry!  Try signing out, "+\
            "signing back in, and repeating the operation.")
        return True
    else:
        return False

def validateUserInput(userInput, columnName, CRUDtype, itemNameForMsg, 
                      columnNameForMsg=None, maxlength=None, 
                      required=False, unique=False, oldInput=None, 
                      tableName=None, priceFormat=False, 
                      validInputs=None, usernameFormat=False):
    '''Validate (and strip HTML) from user input

    Returns the validated name, 
    or none with a flahsed messageif the test fails.

    Args:
        userInput: the input to validate
        columnName: the name of the database column for this input
        columnNameForMsg: the name of the columm for user message.
            Pass None if same as columnName.
        CRUDtype: create, read, update, or delete
        itemNameForMsg: the name for this item in response text
            to the user
        maxlength: the max allowable length of this input
        required: true if form submission requires this input
        unique: whether this input needs to be unique in the table
        oldInput: for an edit -- the value to replace
        tableName only needed if unique is True.
        priceFormat: true if this input should be in standard price format
        validInputs: dictionary with keys that are the only valid inputs
        usernameFormat: true if the input should be a legal username
    '''
    if not columnNameForMsg:
        columnNameForMsg = columnName

    badResult = "Did not " + CRUDtype + " " + itemNameForMsg + ". "
    neutralResult = "Did not edit " + columnNameForMsg + ". "

    if not userInput or len(userInput) < 1:

        if required:

            flash(badResult + "Must provide a " + columnNameForMsg + ".")
        else:

            flash(neutralResult + "Nothing provided.")

        return None

    userInput = bleach.clean(userInput)

    if userInput and maxlength:
        if len(userInput) > maxlength:

            if required:

                flash(badResult + columnNameForMsg + "was too long.")
            else:
                flash(neutralResult + "It was too long.")

            return None

    if userInput and priceFormat:

        match = re.search(r'[0-9]*(.[0-9][0-9])?', userInput)

        if match.group(0) != userInput:

            if required:
                flash(badResult + "Price was in an invalid format.")
            else:

                flash(neutralResult + "It was in an invalid format.")

            return None

        userInput = Decimal(userInput).quantize(Decimal('0.01'))

    if userInput and unique:
        if not isUnique(userInput, columnName, tableName):
            
            if required:

                flash(badResult + columnNameForMsg + " was not unique.")
            else: 

                flash(neutralResult + "It was not unique.")
            return None

    if userInput and oldInput:
        if userInput == oldInput:

            if required:

                flash(badResult + columnNameForMsg +\
                    " provided was same as before")
            else:

                flash(neutralResult + \
                    "The one provided was the same as before.")

            return None

    if userInput and validInputs:
        if userInput not in validInputs:

            if required:

                flash(badResult + columnNameForMsg + \
                    " was not a valid selection")
            else:

                flash(neutralResult + \
                    "It was not a valid selection.")

            return None

    if userInput and usernameFormat:
        match = \
            re.search(r"[^~`!@#\$%\^&\*\(\)_=\+\{}\[\]\\\|\.<>\?/;:]\+",
                userInput)
        if match is not None:

            if required:

                flash(badResult + columnNameForMsg + \
                    " was contained an illegal character.")
            else:

                flash(neutralResult + \
                    "It contained an illegal character.")

            return None

    return userInput

def validateUserPicture(CRUDtype, itemNameForMsg, file=None, link=None,
                        maxlength=None, required=False):
    '''Validate (and strip HTML from) a picture file or link 
    provided by a user.

    Returns dictionary with 'text' and 'serve_type' keys,
    or None if a test fails.

    Does NOT fail if, for an edit, provided pic is same as the old pic
    Does not provide a "unique" argument.

    Args:
        CRUDtype: create, read, update, or delete
        itemNameForMsg: the name for this item in response text
            to the user
        file: the file provided by the user
        link: the link provided by the user
        maxlength: the maximum allowable length for the pic's text
        required: true if form submission requires this input
    '''
    badResult = "Did not " + CRUDtype + itemNameForMsg + ". "
    neutralResult = "Did not edit picture. "   

    pictureDict = {}

    if file:

        file.filename = bleach.clean(file.filename)

        if allowed_pic(file.filename):
            # this name will be overwritten eventually
            # but better safe than sorry
            file.filename = secure_filename(file.filename)
            
            pictureDict['text'] = file.filename
            pictureDict['serve_type'] = 'upload'
        else:
            
            if required:
                flash(badResult + "the uploaded pic was not "+\
                        ".png, .jpeg, or .jpg.")
            else:
                flash(neutralResult + "the uploaded pic was not "+\
                        ".png, .jpeg, or .jpg.")               

            return None
    elif link:

        link = bleach.clean(link)

        if maxlength:
            if len(link) > maxlength:

                if required:

                    flash(badResult + "The link was too long.")
                else:

                    flash(neutralResult + "The link was too long.")

                return None

        if not isURL(link):

            if required:
                
                flash(badResult + "The link was not a url.")
            else:

                flash(neutralResult + "The link was not a url.")

            return None

        pictureDict['text'] = link
        pictureDict['serve_type'] = 'link'

    # if there was input provided
    if 'text' in pictureDict:

        return pictureDict
    else:

        if required:
            
            flash(badResult + 'You must provide a picture.')
        else:

            flash(neutralResult + 'You did not provide one.')

        return None

def isUnique(value, columnName, tableName):
    '''Return true if value is unique for a column within a table

    Incomplete method, but does what I need it to do for now.
    '''
    sameValue = None

    # syntax for python switch statement? hashtag no internet connection
    if tableName == 'BaseMenuItem':
        if columnName == 'name':
            sameValue = DataManager.\
                        getBaseMenuItem(baseMenuItemName=value)
    elif tableName == 'Cuisine':
        if columnName == 'name':
            sameValue = DataManager.getCuisine(name=value)

    if not sameValue:
        return True
    else:
        return False 

def isURL(string):
    '''Return whether a string represents a valid url

    Just checks for beginning http:// or https:// followed by a char
    '''
    if (len(string) < 8 or 
        (len(string) == 7 and string[:6] != 'http://') or
        (len(string) == 8 and string[:7] != 'https://') or
        (string[:6] != 'http://' and string[:7] != 'https://')):

        return True;
    else:

        return False;
