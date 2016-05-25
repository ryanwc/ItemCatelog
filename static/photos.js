// tricky to get jinja and javascript to work
// together to serve uploaded pictures
function getAndSetPhoto(picJSONpath, photoElementId) {

    var setPlacehold = function(picJSONformat) {

        var picDict = picJSONformat['Picture'];
        var photoSRC = picDict['text'];
        var photoServeType = picDict['serve_type'];

        setPhotoSRC(photoSRC, photoElementId, photoServeType);

        document.getElementById('pictureLink').setAttribute("placeholder", photoSRC);
    }

    getRowJSON(picJSONpath, setPlacehold);
}

// set src of a photo element
function setPhotoSRC(photoSRC, photoElementID, serve_type) {

    if (serve_type == 'upload') {

        var uploadPath = document.getElementById('picUploadPath').innerHTML;
        var newSRC = uploadPath.substring(0,uploadPath.length-1);
        newSRC = newSRC.concat(photoSRC);
        document.getElementById(photoElementID).setAttribute("src", newSRC);
    }
    else if (serve_type == 'link') {

        document.getElementById(photoElementID).setAttribute("src", photoSRC);
    }
}