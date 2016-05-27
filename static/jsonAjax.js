// get a JSON object representing a table in the database
// and base the JSON to the callback
// would first var 'tableJSONpath' be better insead of the if statements?
// see, for example, function getRowJSON
function getTableJSON(tableName, callBackFunction) {

    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function() {

        if (xhttp.readyState == 4 && xhttp.status == 200) {

            response = JSON.parse(xhttp.responseText)

            if (typeof callBackFunction === 'function') {

                callBackFunction(response);
            }
            else {

                console.log("Callback was not a function");
            }
        }
    }

    // add tables as needed
    if (tableName == 'Cuisine') {

        path = "/cuisines/JSON";
    }
    else if (tableName == "BaseMenuItem") {

        path = "/base_menu_items/JSON"
    }

    xhttp.open("GET", path, true);
    xhttp.send();
}

// get a JSON object representing a row in the database
function getRowJSON(rowJSONpath, callBackFunction) {

    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function() {

        if (xhttp.readyState == 4 && xhttp.status == 200) {

            response = JSON.parse(xhttp.responseText)

            if (typeof callBackFunction === 'function') {

                callBackFunction(response);
            }
            else {

                console.log("Callback was not a function");
            }
        }
    }

    xhttp.open("GET", rowJSONpath, true);
    xhttp.send();
}