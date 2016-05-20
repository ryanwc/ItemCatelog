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

//
//var form = 

//form.addEventListener("submit", function(evt) {

  //  if (form.checkValidity() === false) {

    //    evt.preventDefault();
      //  alert("Form contains invalid input");
        //return false;
    //}
//});