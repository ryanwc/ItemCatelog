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
