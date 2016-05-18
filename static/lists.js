// if we had antother reason or two to load jQuery onto the page,
// we probably want to use jQuery.slideToggle() instead (prettier)
function toggleList(listName) {

    // get the correct list
    var listID = String(listName+'List');
    var list = document.getElementById(listID);
    var listToggleID = String(listName+"Toggle");
    var listToggle = document.getElementById(listToggleID);

    console.log(list);
    console.log(listToggle);
    // toggle its display
    if (list.style.display  == "none") {

        list.style.display = "block";
        listToggle.innerHTML = '(hide)'
    }
    else {

        list.style.display = 'none';
        listToggle.innerHTML = '(show)'
    }
};

// could also do recursive with a "toggleChildrenList" function
function toggleAllLists() {

	var masterToggle = document.getElementById("masterToggle");
	var nonTopLevelLists = document.getElementsByClassName("nonTopLevelList");
	console.log(nonTopLevelLists);
	var listToggles = document.getElementsByClassName("listToggle");

	if (masterToggle.innerHTML == '(show all)') {

		masterToggle.innerHTML = '(hide all)'

		for (i = 0; i < listToggles.length; i++) {

        	listToggles[i].innerHTML = '(hide)';
		}
		for (i = 0; i < nonTopLevelLists.length; i++) {

        	nonTopLevelLists[i].style.display = "block";
		}
	}
	else {

		masterToggle.innerHTML = '(show all)'

		for (i = 0; i < listToggles.length; i++) {

        	listToggles[i].innerHTML = '(show)';
		}
		for (i = 0; i < nonTopLevelLists.length; i++) {
			console.log('changing to none');
			console.log(nonTopLevelLists[i]);
        	nonTopLevelLists[i].style.display = "none";
		}
	}
};
