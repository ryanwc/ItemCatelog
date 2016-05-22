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