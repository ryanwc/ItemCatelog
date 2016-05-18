function placeholdWithBaseMenuItem() {

    // get the selected item
    var baseMenuItemID = document.getElementById("baseMenuItemID").value;

    // get the info
    var placeholderName = document.getElementById(baseMenuItemID + "name").innerHTML;
    var placeholderDescription = document.getElementById(baseMenuItemID + "description").innerHTML;
    var placeholderPrice = document.getElementById(baseMenuItemID + "price").innerHTML;
    console.log(placeholderPrice)
    var placeholderMenuSection = document.getElementById(baseMenuItemID + "menuSection").innerHTML;

    console.log(placeholderMenuSection)
    // set the placeholders
    document.getElementById("name").setAttribute("placeholder", placeholderName);
    document.getElementById("description").setAttribute("placeholder", placeholderDescription);
    document.getElementById("price").setAttribute("placeholder", placeholderPrice);
    document.getElementById("menuSection").value = placeholderMenuSection;  
};