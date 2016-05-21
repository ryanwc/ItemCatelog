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

function checkForm(form) {

    if (form.id == 'editUserForm') {

        var picFile = document.getElementById("pictureFile").value;

        if (document.getElementById("name").value > 30) {

            window.alert("Name is too long");
            return false;
        }
        else if (document.getElementById("pictureFile").value == "" &&
                 document.getElementById("pictureLink").value != "" &&
                 (document.getElementById("pictureLink").value.substring(0,7) != 'http://' ||
                  document.getElementById("pictureLink").value.substring(0,8) != 'https://')) {

            window.alert("Link must start with 'http://' or 'https://'");
            return false;
        }
        else if (picFile.substring(picFile.length-5, picFile.length).toLowerCase() != '.jpeg' &&
                 picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.jpg' &&
                 picFile.substring(picFile.length-4, picFile.length).toLowerCase() != '.png') {

            window.alert("Uploaded pic must be .png, .jpeg, or .jpg");
            return false;
        }
        else {

            if (document.getElementById("name").value == 'Ryan Connor') {

                window.alert("Your name is awesome");
            }

            return true;
        }
    }
    else {

        window.alert("Sorry, this form is not supported yet.")
        return false;
    }
}
