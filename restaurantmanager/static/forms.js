// placehold form fields with the selected base menu item's attributes
// this could be made more flexible (e.g., pass elements
    // to placehold as a class named 'elementsToPlacehold')
function placeholdWithBaseMenuItem(baseMenuItemID, photoElementId) {

    // would be best to figure out a relative path from javascript to
    // the flask template instead of hardcoding
    var baseMenuItemJSONpath = '/base_menu_items/' + baseMenuItemID + '/JSON/';
    // [ajax call to get the info];
    var setPlaceholders = function(itemJSONformat) {

        itemDict = itemJSONformat['BaseMenuItem'];

        // set the non-picture placeholders
        document.getElementById("name").setAttribute("placeholder", itemDict['name']);
        document.getElementById("description").setAttribute("placeholder", itemDict['description']);
        document.getElementById("price").setAttribute("placeholder", itemDict['price']);
        document.getElementById("menuSection").value = itemDict['menuSection_id'];  

        var picJSONpath = '/pics/' + itemDict['picture_id'] + "/JSON/";
        getAndSetPhoto(picJSONpath, photoElementId);
    }
    
    getRowJSON(baseMenuItemJSONpath, setPlaceholders);
};

// get data with ajax call, check uniqueness, and set HTML form as appropriate
// input node must be jQuery object b/c eventually uses addClass()/removeClass() method
// is there an easy way to do addClass() / removeClass() in plain JS?
function realTimeUniqueCheck(columnValue, tableName, columnName, inputNode) {

    // define callback to execute upon successful ajax table retrieval
    var sendTableToCheckUniqueAndSetHTML = function(JSONTable) {

        checkUniqueAndSetHTML(columnValue, JSONTable, columnName, inputNode);
    };

    // do the ajax table retrieval 
    getTableJSON(tableName, sendTableToCheckUniqueAndSetHTML);
}

// check uniqueness of a value in a table and set HTML form as appropriate
// input node must be jQuery object
// or could refactor to not use .addClass/.removeClass
function checkUniqueAndSetHTML(columnValue, JSONTable, column, inputNode) {

    var uniqueAlertID = inputNode.attr('id') + "UniqueAlert";
    var uniqueAlertNode = document.getElementById(uniqueAlertID);

    if (checkUnique(columnValue, JSONTable, column)) {

        uniqueAlertNode.innerHTML = "OK: Not in use yet";
        inputNode.addClass("unique").removeClass("notUnique");
    }
    else {

        uniqueAlertNode.innerHTML = "NOT OK: Already in use";
        inputNode.addClass("notUnique").removeClass("unique");
    }
}

// return true if columnValue is unique in the table
function checkUnique(columnValue, JSONTableObj, column) {

    for (var tableName in JSONTableObj) {

        var table = JSONTableObj[tableName];

        for (i = 0; i < table.length; i++) {

            var row = table[i];

            if (row.hasOwnProperty(column)) {

                var thisColumn = row[column];

                if (columnValue == thisColumn) {

                    return false;
                }
            }
        }
    }

    return true;
};

// could refactor this more to be more concise like the server side code
// but not sure it is worth it
function checkForm(form) {

    if (form.id == 'editUserForm') {

        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;
        var name = document.getElementById("name").value;

        // does not check for illegal chars 
        // (but this is done on server side)
        if (!validateName(name, 30, false, false)) {

            return false;
        }

        if (!validatePictureFile(picFile, 300, false)) {

            return false;
        }
            
        if (!validatePictureLink(picLink, 300, false)) {

            return false;
        }

        if (name == 'Ryan Connor') {

            window.alert("Your name is awesome");
        }

        return true;
    }
    else if (form.id == 'editRestaurantMenuItemForm') {

        var name = document.getElementById("name").value;
        var description = document.getElementById("description").value;
        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;
        var price = document.getElementById("price").value;
        var menuSectionID = document.getElementById("menuSection").value;
        var menuSectionIDs = document.getElementsByClassName("validMenuSectionID");

        if (!validateName(name, 80, false, false)) {

            return false;
        }

        if (!validateSelection(menuSectionID, validMenuSectionIDs, true)) {

            return false;
        }
    
        if (!validateDescription(description, maxlength, false)) {

                return false;
        }

        if (!validatePrice(price, 20, false)) {

            return false;
        }

        if (!validatePictureFile(picFile, 300, false)) {

            return false;
        }
                 
        if (!validatePictureLink(picLink, 300, false)) {

            return false;
        }

        return true;
    }
    else if (form.id == 'editRestaurantForm') {

        var name = document.getElementById("name").value;
        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;
        var cuisineID = document.getElementById("cuisine").value;
        var cuisineIDs = document.getElementsByClassName("validCuisineID");

        if (!validateName(name, 100, false, false)) {

            return false;               
        }

        if (!validateSelection(cuisineID, cuisineIDs, true)) {

            return false;
        }

        if (!validatePictureFile(picFile, 300, false)) {

            return false;
        }
                 
        if (!validatePictureLink(picLink, 300, false)) {

            return false;
        }
        
        return true;
    }
    else if (form.id == 'editCuisineForm') {

        var name = document.getElementById("name").value;

        if (!validateName(name, 80, false, true)) {

            return false;
        }

        return true;
    }
    else if (form.id == 'editBaseMenuItemForm') {

        var name = document.getElementById("name").value;
        var description = document.getElementById("description").value;
        var price = document.getElementById("price").value;
        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;
        var menuSectionID = document.getElementById("menuSection").value;
        var menuSectionIDs = document.getElementsByClassName("validMenuSectionID");

        if (!validateName(name, 80, false, true)) {

            return false;
        }

        if (!validateSelection(menuSectionID, menuSectionIDs, true)) {

            return false;
        }
        
        if (!validateDescription(description, 250, false)) {

            return false;
        }
        
        if (!validatePrice(price, 20, false)) {

            return false;
        }

        if (!validatePictureFile(picFile, 300, false)) {

            return false;
        }
   
        if (!validatePictureLink(picLink, 300, false)) {

            return false;
        }
        
        return true;
    }
    else if (form.id == 'addCuisineForm') {

        var name = document.getElementById("name").value;
        
        if (!validateName(name, 80, true, true)) {

            return false;
        }

        return true;
    }
    else if (form.id == 'addRestaurantForm') {

        var name = document.getElementById("name").value;
        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;
        var cuisineID = document.getElementById("cuisine").value;
        var cuisineIDs = document.getElementsByClassName("validCuisineID");

        if (!validateName(name, 100, true, false)) {

            return false;
        }

        if (!validateSelection(cuisineID, cuisineIDs, true)) {

            return false;
        }

        // one of these is required
        // so pass inner one required=true
        if (!validatePictureFile(picFile, 300, false)) {

            if (!validatePictureLink(picLink, 300, true)) {

                return false;
            }
        }
        
        return true;
    }
    else if (form.id == 'addBaseMenuItemForm') {

        var name = document.getElementById("name").value;
        var description = document.getElementById("description").value;
        var price = document.getElementById("price").value;
        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;
        var menuSectionID = document.getElementById("menuSection").value;
        var menuSectionIDs = document.getElementsByClassName("validMenuSectionID");

        if (!validateName(name, 80, true, true)) {

            return false;
        }

        if (!validateDescription(description, 250, true)) {

            return false;
        }

        if (!validatePrice(price, 20, true)) {

            return false;
        }

        if (!validateSelection(menuSectionID, menuSectionIDs, true)) {

            return false;
        }

        if (!validatePictureFile(picFile, 300, false)) {

            if (!validatePictureLink(picLink, 300, true)) {

                return false;
            }
        }
        
        return true;
    }
    else if (form.id == 'addRestaurantMenuItemForm') {

        var name = document.getElementById("name").value;
        var description = document.getElementById("description").value;
        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;
        var price = document.getElementById("price").value;
        var menuSectionID = document.getElementById("menuSection").value;
        var menuSectionIDs = document.getElementsByClassName("validMenuSectionID");
        var baseMenuItemID = document.getElementById("baseMenuItemID").value;
        var baseMenuItemIDs = document.getElementsByClassName("validBaseMenuItemID");

        if (!validateSelection(baseMenuItemID, baseMenuItemIDs, true)) {

            return false;
        }

        // don't need to alert empty input
        // defaults to base item attribute

        if (!validateName(name, 80, false)) {

            return false;
        }

        if (!validateSelection(menuSectionID, menuSectionIDs, true)) {

            return false;
        }
        
        if (!validateDescription(description, 250, false)) {

            return false;
        }
        
        if (!validatePrice(price, 20, false)) {

            return false;
        }

        if (!validatePictureFile(picFile, 300, false)) {

            if (!validatePictureLink(picLink, 300, false)) {

                return false;
            }
        }

        return true;
    }
    else {

        window.alert("Sorry, this form is not supported yet.")
        return false;
    }
}

function validateName(name, maxlength, required, unique) {

    if (name.length < 1) {

        if (required) {

            window.alert("You must provide a name");
            return false;
        }
        else {

            return true;
        }
    }

    if (unique) {

        var uniqueAlert = document.getElementById('nameUniqueAlert').innerHTML;

        if (uniqueAlert != 'OK: Not in use yet') {

            window.alert("Name is not unique");
            return false;
        }
    }

    if (name.length > 30) {

        window.alert("Name is too long");
        return false;
    }

    return true;
}

function validateDescription(description, maxlength, required) {

    if (description.length < 1) {

        if (required) {

            window.alert("You must provide a description");
            return false;
        }
        else {

            return true;
        }
    }

    if (description.length > maxlength) {

        window.alert("Description is too long");
        return false;
    }

    return true;
}

function validatePrice(price, maxlength, required) {

    if (price.length < 1) {

        if (required) {

            window.alert("You must provide a price");
            return false;
        }
        else {

            return true;
        }
    }

    var priceMatch = price.match(/[0-9]*(?:.[0-9][0-9])?/);

    if (priceMatch[0] != price) {

        window.alert("Price is in invalid format");
        return false;
    }

    if (price.length > 20) {

        window.alert("Price is too long");
        return false;
    }

    return true;
}

// doesn't really capture the name.  Apprently, from the form,
// the name is something like "FakeC://name..."
// but maybe this could change from system to system?
function validatePictureFile(pictureFileName, maxlength, required) {

    if (pictureFileName.length < 1) {

        if (required) {

            window.alert("You must provide a picture file");
            return false;
        }
        else {

            return true;
        }
    }

    if (pictureFileName.length < 5) {

        window.alert("Uploaded pic was in invalid format");
        return false;    
    }

    if (pictureFile.length > maxlength) {

        window.alert("Picture file name is too long");
        return false;
    }
    
    if (pictureFileName.length == 5) {

        if (pictureFileName.substring(1, 5).toLowerCase() != '.png') {

            window.alert("Uploaded pic is in invalid format");
            return false;          
        }
    }
    
    // make sure it's an allowed extension
    if (pictureFileName.substring(pictureFileName.length-5, pictureFileName.length).toLowerCase() != '.jpeg' &&
        pictureFileName.substring(pictureFileName.length-4, pictureFileName.length).toLowerCase() != '.jpg' &&
        pictureFileName.substring(pictureFileName.length-4, pictureFileName.length).toLowerCase() != '.png') {

        window.alert("Uploaded pic must be .png, .jpeg, or .jpg");
        return false;
    }

    return true;
}

function validatePictureLink(pictureLink, maxlength, required) {

    if (pictureLink.length < 1) {

        if (required) {

            window.alert("You must provide a picture");
            return false;
        }
        else {

            return true;
        }
    }

    // maybe a regex would be better?
    if (pictureLink.length < 8) {

        window.alert("Pic link is not a valid url");
        return false;
    }

    if (pictureLink.substring(0,7) == 'http://') {

        if (pictureLink == 'http://') {

            window.alert("Pic link is not a valid url");
            return false;
        }
    }
    else if (pictureLink.substring(0,8) == 'https://') {

        if (pictureLink == 'https://') {

            window.alert("Pic link is not a valid url");
            return false;
        }
    }
    else {

        window.alert("Pic link must start with 'http://' or 'https://'");
        return false;
    }

    if (pictureLink.length > maxlength) {

        window.alert("Pic link is too long")
        return false;
    }

    return true;
}

function validateSelection(userSelectedValue, validSelectNodes, required) {

    if (userSelectedValue.length < 1) {

        if (required) {

            window.alert("You didn't select an option from a dropdown menu");
            return false;
        }
        else {

            return true;
        }
    }

    for (i = 0; i < validSelectNodes.length; i++) {

        if (userSelectedValue == validSelectNodes[i].value) {

            return true;
        }
    }

    window.alert("You selected an invalid dropdown menu selection");
    return false;
}