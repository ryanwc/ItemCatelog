function placeholdWithBaseMenuItem() {

    // get the selected item
    var baseMenuItemID = document.getElementById("baseMenuItemID").value;

    // get the info
    var placeholderName = document.getElementById(baseMenuItemID + "name").innerHTML;
    var placeholderDescription = document.getElementById(baseMenuItemID + "description").innerHTML;
    var placeholderPrice = document.getElementById(baseMenuItemID + "price").innerHTML;
    var placeholderMenuSection = document.getElementById(baseMenuItemID + "menuSection").innerHTML;

    // set the placeholders
    document.getElementById("name").setAttribute("placeholder", placeholderName);
    document.getElementById("description").setAttribute("placeholder", placeholderDescription);
    document.getElementById("price").setAttribute("placeholder", placeholderPrice);
    document.getElementById("menuSection").value = placeholderMenuSection;  
};

// get data with ajax call, check uniqueness, and set HTML form as appropriate
// input node must be jQuery object b/c eventually uses .addClass/.removeClass method
function realTimeUniqueCheck(columnValue, tableName, columnName, inputNode) {

    // define callback to execute upon successful ajax table retrieval
    var sendTableToCheckUniqueAndSetHTML = function(JSONTable) {

        checkUniqueAndSetHTML(columnValue, JSONTable, columnName, inputNode);
    };

    // do the ajax table retrieval and return 
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

// get a JSON object representing a table in the database
// and base the JSON to the callback
function getTableJSON(tableName, callBackFunction) {

    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function() {

        if (xhttp.readyState == 4 && xhttp.status == 200) {

            response = JSON.parse(xhttp.responseText)

            if (typeof callBackFunction === 'function') {

                callBackFunction(response);
            }
            else {

                console.log("Callback was not a function");
            }
        }
    }

    // add tables as needed
    if (tableName == 'Cuisine') {

        path = "/cuisines/JSON";
    }
    else if (tableName == "BaseMenuItem") {

        path = "/baseMenuItems/JSON"
    }

    xhttp.open("GET", path, true);
    xhttp.send();
}

function checkForm(form) {

    // would it be better to have a separate function for each form?
    // or do careful refactoring for re-used code?
    if (form.id == 'editUserForm') {

        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;
        var name = document.getElementById("name").value;

        if (name.length > 0) {

            if (name.length > 30) {

                window.alert("Name is too long");
                return false;
            }
        }
        
        if (picFile.length > 0) {

            if (picFile.length < 5) {

                window.alert("Uploaded pic was in invalid format");
                return false;    
            }
            else if (picFile.length == 5) {

                if (picFile.substring(1, 5).toLowerCase() != '.png') {

                    window.alert("Uploaded pic was in invalid format");
                    return false;          
                }
            }
            else if (picFile.substring(picFile.length-5, picFile.length).toLowerCase() != '.jpeg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.jpg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.png') {

                window.alert("Uploaded pic must be .png, .jpeg, or .jpg");
                return false;
            }
        }
        else if (picLink.length > 0) {
            
            if (picLink.length < 8) {

                window.alert("Pic link is not a valid url");
                return false;
            }

            if (picLink.substring(0,7) != 'http://' ||
                picLink.substring(0,8) != 'https://') {

                window.alert("Link must start with 'http://' or 'https://'");
                return false;
            }

            if (picLink.length > 300) {

                window.alert("Pic link is too long")
                return false;
            }
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

        if (name.length > 0) {

            if (name.length > 80) {

                window.alert("Name is too long");
                return false;
            }
        }
        
        if (description.length > 0) {

            if (description.length > 250) {

                window.alert("Description is too long");
                return false;
            }
        }
        
        if (price.length > 0) {

            var priceMatch = price.match(/[0-9]*(?:.[0-9][0-9])?/);

            if (priceMatch[0] != price) {

                window.alert("Price is in invalid format");
                return false;
            }

            if (price.length > 20) {

                window.alert("Price is too long");
                return false;
            }
        }

        if (picFile.length > 0) {

            if (picFile.length < 5) {

                window.alert("Uploaded pic was in invalid format");
                return false;    
            }
            else if (picFile.length == 5) {

                if (picFile.substring(1, 5).toLowerCase() != '.png') {

                    window.alert("Uploaded pic was in invalid format");
                    return false;          
                }
            }
            else if (picFile.substring(picFile.length-5, picFile.length).toLowerCase() != '.jpeg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.jpg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.png') {

                window.alert("Uploaded pic must be .png, .jpeg, or .jpg");
                return false;
            }
        }
        else if (picLink.length > 0) {
                 

            if (picLink.length < 8) {

                window.alert("Pic link is not a valid url");
                return false;
            }

            if (picLink.substring(0,7) != 'http://' ||
                picLink.substring(0,8) != 'https://') {

                window.alert("Link must start with 'http://' or 'https://'");
                return false;
            }

            if (picLink.length > 300) {

                window.alert("Pic link is too long")
                return false;
            }
        }

        return true;
    }
    else if (form.id == 'editRestaurantForm') {

        var name = document.getElementById("name").value;
        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;

        if (name.length > 0) {

            if (name.length > 100) {

                window.alert("Name is too long");
                return false;               
            }
        }
        
        if (picFile.length > 0) {

            if (picFile.length < 5) {

                window.alert("Uploaded pic was in invalid format");
                return false;    
            }
            else if (picFile.length == 5) {

                if (picFile.substring(1, 5).toLowerCase() != '.png') {

                    window.alert("Uploaded pic was in invalid format");
                    return false;          
                }
            }
            else if (picFile.substring(picFile.length-5, picFile.length).toLowerCase() != '.jpeg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.jpg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.png') {

                window.alert("Uploaded pic must be .png, .jpeg, or .jpg");
                return false;
            }
        }
        else if (picLink.length > 0) {
                 
            if (picLink.length < 8) {

                window.alert("Pic link is not a valid url");
                return false;
            }

            if (picLink.substring(0,7) != 'http://' ||
                picLink.substring(0,8) != 'https://') {

                window.alert("Link must start with 'http://' or 'https://'");
                return false;
            }

            if (picLink.length > 300) {

                window.alert("Pic link is too long")
                return false;
            }
        }
        
        return true;
    }
    else if (form.id == 'editCuisineForm') {

        var name = document.getElementById("name").value;
        var uniqueAlert = document.getElementById("nameUniqueAlert").innerHTML;
        var nameIsUnique = false;
        
        if (uniqueAlert == 'OK: Not in use yet') {

            nameIsUnique = true;
        }
        
        if (name.length > 0){

            if (name > 80) {

                window.alert("Name is too long");
                return false;
            }
            
            if (!nameIsUnique) {

                window.alert("Name is not unique");
                return false;
            }
        }

        return true;
    }
    else if (form.id == 'editBaseMenuItemForm') {

        var name = document.getElementById("name").value;
        var uniqueAlert = document.getElementById("nameUniqueAlert").innerHTML;

        var description = document.getElementById("description").value;

        var price = document.getElementById("price").value;

        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;

        if (name.length > 0) {

            if (name.length > 80) {

                window.alert("Name is too long");
                return false;
            }
            
            if (uniqueAlert != 'OK: Not in use yet') {

                window.alert("Name is not unique");
                return false;
            }
        }
        
        if (description.length > 0) {

            if (description.length > 250) {

                return false;
            }
        }
        
        if (price.length > 0) {
            
            var priceMatch = price.match(/[0-9]*(?:.[0-9][0-9])?/);
            
            if (priceMatch[0] != price) {

                window.alert("Price is in invalid format");
                return false;
            }

            if (price.length > 20) {

                window.alert("Price is too long");
                return false;
            }
        }
            
        if (picFile.length > 0) {

            if (picFile.length < 5) {

                window.alert("Uploaded pic was in invalid format");
                return false;    
            }
            else if (picFile.length == 5) {

                if (picFile.substring(1, 5).toLowerCase() != '.png') {

                    window.alert("Uploaded pic was in invalid format");
                    return false;          
                }
            }
            else if (picFile.substring(picFile.length-5, picFile.length).toLowerCase() != '.jpeg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.jpg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.png') {

                window.alert("Uploaded pic must be .png, .jpeg, or .jpg");
                return false;
            }
        }
        else if (picLink.length > 0) {
                 

            if (picLink.length < 8) {

                window.alert("Pic link is not a valid url");
                return false;
            }

            if (picLink.substring(0,7) != 'http://' ||
                picLink.substring(0,8) != 'https://') {

                window.alert("Link must start with 'http://' or 'https://'");
                return false;
            }

            if (picLink.length > 300) {

                window.alert("Pic link is too long")
                return false;
            }
        }
        
        return true;
    }
    else if (form.id == 'addCuisineForm') {

        var name = document.getElementById("name").value;
        
        if (name.length < 1) {

            window.alert("Please enter a name");
            return false;
        }

        var uniqueAlert = document.getElementById("nameUniqueAlert").innerHTML;
        var nameIsUnique = false;

        if (uniqueAlert == 'OK: Not in use yet') {

            nameIsUnique = true;
        }

        if (name > 80) {

            window.alert("Name is too long");
            return false;
        }
            
        if (!nameIsUnique) {

            window.alert("Name is not unique");
            return false;
        }
        return true;
    }
    else if (form.id == 'addRestaurantForm') {

        var name = document.getElementById("name").value;
        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;

        if (name.length < 1) {

            window.alert("Please provide a name");
            return false;
        }

        if (picFile.length < 1 && picLink.length < 1) {

            window.alert("Please provide a picutre");
            return false;
        }


        if (name.length > 100) {

            window.alert("Name is too long");
            return false;               
        }
        
        if (picFile.length > 0) {

            if (picFile.length < 5) {

                window.alert("Uploaded pic was in invalid format");
                return false;    
            }
            else if (picFile.length == 5) {

                if (picFile.substring(1, 5).toLowerCase() != '.png') {

                    window.alert("Uploaded pic was in invalid format");
                    return false;          
                }
            }
            else if (picFile.substring(picFile.length-5, picFile.length).toLowerCase() != '.jpeg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.jpg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.png') {

                window.alert("Uploaded pic must be .png, .jpeg, or .jpg");
                return false;
            }
        }
        else {
                 
            if (picLink.length < 8) {

                window.alert("Pic link is not a valid url");
                return false;
            }

            if (picLink.substring(0,7) != 'http://' ||
                picLink.substring(0,8) != 'https://') {

                window.alert("Link must start with 'http://' or 'https://'");
                return false;
            }

            if (picLink.length > 300) {

                window.alert("Pic link is too long")
                return false;
            }
        }
        
        return true;
    }
    else if (form.id == 'addBaseMenuItemForm') {

        var name = document.getElementById("name").value;
        var uniqueAlert = document.getElementById("nameUniqueAlert").innerHTML;

        var description = document.getElementById("description").value;

        var price = document.getElementById("price").value;

        var picFile = document.getElementById("pictureFile").value;
        var picLink = document.getElementById("pictureLink").value;

        if (name.length < 1) {

            window.alert("Please provide name");
            return false;           
        }

        if (description.length < 1) {

            window.alert("Please provide description");
            return false; 
        }

        if (price.length < 1) {

            window.alert("Please provide price");
            return false; 
        }

        if (picFile.length < 1 && picLink < 1) {

            window.alert("Please provide picture");
            return false; 
        }

        if (name.length > 80) {

            window.alert("Name is too long");
            return false;
        }
            
        if (uniqueAlert != 'OK: Not in use yet') {

            window.alert("Name is not unique");
            return false;
        }

        if (description.length > 250) {

            return false;
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
            
        if (picFile.length > 0) {

            if (picFile.length < 5) {

                window.alert("Uploaded pic was in invalid format");
                return false;    
            }
            else if (picFile.length == 5) {

                if (picFile.substring(1, 5).toLowerCase() != '.png') {

                    window.alert("Uploaded pic was in invalid format");
                    return false;          
                }
            }
            else if (picFile.substring(picFile.length-5, picFile.length).toLowerCase() != '.jpeg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.jpg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.png') {

                window.alert("Uploaded pic must be .png, .jpeg, or .jpg");
                return false;
            }
        }
        else {     

            if (picLink.length < 8) {

                window.alert("Pic link is not a valid url");
                return false;
            }

            if (picLink.substring(0,7) != 'http://' ||
                picLink.substring(0,8) != 'https://') {

                window.alert("Link must start with 'http://' or 'https://'");
                return false;
            }

            if (picLink.length > 300) {

                window.alert("Pic link is too long")
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

        // don't need to alert empty input
        // defaults to base item attribute

        if (name.length > 0) {

            if (name.length > 80) {

                window.alert("Name is too long");
                return false;
            }
        }
        
        if (description.length > 0) {

            if (description.length > 250) {

                window.alert("Description is too long");
                return false;
            }
        }
        
        if (price.length > 0) {

            var priceMatch = price.match(/[0-9]*(?:.[0-9][0-9])?/);

            if (priceMatch[0] != price) {

                window.alert("Price is in invalid format");
                return false;
            }

            if (price.length > 20) {

                window.alert("Price is too long");
                return false;
            }
        }

        if (picFile.length > 0) {

            if (picFile.length < 5) {

                window.alert("Uploaded pic was in invalid format");
                return false;    
            }
            else if (picFile.length == 5) {

                if (picFile.substring(1, 5).toLowerCase() != '.png') {

                    window.alert("Uploaded pic was in invalid format");
                    return false;          
                }
            }
            else if (picFile.substring(picFile.length-5, picFile.length).toLowerCase() != '.jpeg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.jpg' &&
                     picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.png') {

                window.alert("Uploaded pic must be .png, .jpeg, or .jpg");
                return false;
            }
        }
        else if (picLink.length > 0) {
                 

            if (picLink.length < 8) {

                window.alert("Pic link is not a valid url");
                return false;
            }

            if (picLink.substring(0,7) != 'http://' ||
                picLink.substring(0,8) != 'https://') {

                window.alert("Link must start with 'http://' or 'https://'");
                return false;
            }

            if (picLink.length > 300) {

                window.alert("Pic link is too long")
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
