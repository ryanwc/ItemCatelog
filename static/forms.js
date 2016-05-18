function placeholdWithBaseMenuItem() {

    // get the selected item
    var baseMenuItemID = document.getElementById("baseMenuItemID").value;

    // get the info
    placeholderName = document.getElementById(baseMenuItemID + "name").innerHTML;
    placeholderDescription = document.getElementById(baseMenuItemID + "description").innerHTML;
    placeholderPrice = document.getElementById(baseMenuItemID + "price").innerHTML;
    placeholderMenuSection = document.getElementById(baseMenuItemID + "menuSection").innerHTML;

    // set the placeholders
    document.getElementById("name").setAttribute("placeholder", placeholderName);
    document.getElementById("description").setAttribute("placeholder", placeholderDescription);
    document.getElementById("price").setAttribute("placeholder", placeholderPrice);
    document.getElementById("menuSection").setAttribute("placeholder", placeholderMenuSection);  
};