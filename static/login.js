function displayBasedOnLogin(message) {

	if (message == 'Not logged in') { 

		hide = document.getElementsByClassName("hideLoggedOut");
	}
	else {

		hide = document.getElementsByClassName("hideLoggedIn");
	}

	for (i = 0; i < hide.length; i++) {
		
		hide[i].style.display = "none";
	}

	return message;
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

function signOut() {

	var xhttp = new XMLHttpRequest();

	xhttp.onreadystatechange = function() {
    	if (xhttp.readyState == 4 && xhttp.status == 200) {
     		window.alert(xhttp.responseText);
     		location.reload();
    	}
    }

    xhttp.open("POST", "/disconnect", true);
	xhttp.send();
};

// called when facebook login button clicked
function sendTokenToServer() {

    FB.api('/me', function(response) {
    	// hide the login
		$('#signIn').addClass('hiddenClass');
		
		// get parameters for connect
		var urlWithState = '/fbconnect?state=' + $('#state').html();
		var data = FB.getAuthResponse()['accessToken'];
		var loginClass = 'fbSignIn';
    	// send the on-time-use code to the server, if the server responds, write
		// the output of the /fbconnect method to the web page then refresh
		connect(urlWithState, data, loginClass);
	});
}

// called when Google calls back after sending the user the access code
function signInCallback(authResult) {

	if (authResult['code']) {
		// hide the sign-in button
		$('#signIn').addClass('hiddenClass');

		// get data for connect
		var urlWithState = '/gconnect?state=' + $('#state').html();
		var loginClass = 'gSignIn';
		var data = authResult['code'];

		// send the on-time-use code to the server, if the server responds, write
		// the output of the /gconnect method to the web page then refresh
		connect(urlWithState, data, loginClass);
	}
}

// make ajax call to server and handle result
function connect(urlWithState, data, loginClass) {

	$.ajax({
		type: 'POST',
		url: urlWithState,
		processData: false,
		data: data,
		contentType: 'application/octet-stream; charset=utf-8',
		success: function(result) {

			handleSignInResult(loginClass, result);
		}
	});
}

// handle rest of sign in after a ajax call
function handleSignInResult(loginClass, result) {

	if (result) {

		resultObj = JSON.parse(result);
		$('#result').addClass(loginClass);
		$('#result').removeClass('hiddenClass');
		$('#resultMessage').html('Login Sucessful!');

		$('#welcome').html(resultObj['loginMessage']);

		if (resultObj['picture_serve_type'] == 'upload') {

			// tricky to get jinja and javascript to work
			// together to serve uploaded pictures
			var currSRC = $('#signInPhoto').attr("src");
			var path = currSRC.substring(0,currSRC.length-1);
			var newSRC = path.concat(resultObj['picture']);
    	    $('#signInPhoto').attr("src", newSRC);
		}
		else if (resultObj['picture_serve_type'] == 'link') {

    	    $('#signInPhoto').attr("src", resultObj['picture']);
		}

		$('#redirectMessage').html('Redirecting...');

		setTimeout(function() {
		
			location.reload();
		}, 4000);
	}
	else if (authResult['error']) {
					
		console.log('There was an error: ' + authResult['error']);
	}
	else {

		$('#result').html('Failed to make a server-side call.  Check your configuration and console.');
	}
}