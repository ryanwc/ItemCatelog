function displayBasedOnLogin(intBooleanLoggedIn) {

	if (intBooleanLoggedIn==1) { 

		hide = document.getElementsByClassName("hideLoggedIn");
	}
	else {

		hide = document.getElementsByClassName("hideLoggedOut");
	}

	for (i = 0; i < hide.length; i++) {
		
		hide[i].style.display = "none";
	}

	return intBooleanLoggedIn;
};

function displayBasedOnOwner(loggedInUserID, thingOwnerID) {

	if (loggedInUserID == thingOwnerID) {

		hide = document.getElementsByClassName("hideIfOwner");
	}
	else {

		hide = document.getElementsByClassName("hideIfNotOwner");
	}

	for (i = 0; i < hide.length; i++) {
		
		hide[i].style.display = "none";
	}
};