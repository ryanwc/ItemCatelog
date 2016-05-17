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
};