// Sorry this is a total mess! I just hacked it up on a Sunday and have no idea how to write web pages.

//Statics
var id_token;
var nextPlacementTime = -1;
var recurringTimerUpdate = null;
var showingPlacingText = false

function initialize() {
    evaluateNextMode();
    var auth2 = gapi.auth2.getAuthInstance();
    // Listen for changes to current user.
    // (called shortly before expiration)
    auth2.currentUser.listen(function(googleUser){
        id_token = googleUser.getAuthResponse().id_token;
    });
}

function requestToggle(coord) {
    var auth2 = gapi.auth2.getAuthInstance();
    var loggedIn = auth2.isSignedIn.get();
    if (!loggedIn) {
        auth2.signIn();
        return;
    } else if (loggedIn && nextPlacementTime == -1) {
        return;
    }
    var now = new Date().getTime();
    var distance = nextPlacementTime - now;
    if (distance < 1.01) {
        showSubmittingMode();
    }
    var xhr = new XMLHttpRequest();
    var url = "/toggle";
    var params = "coord="+coord+"&id_token="+id_token;
    xhr.open("POST", url, true);

    //Send the proper header information along with the request
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    xhr.onreadystatechange = function() {//Call a function when the state changes.
        if (xhr.readyState == 4) {
            if (xhr.status == 200) {
                // success! after a few seconds transition to countdown
                //console.log('Response: ' + xhr.responseText);
                var dict = JSON.parse(xhr.responseText);
                if (dict["secondsUntilNextPlacement"]) {
                    updateNextPlacement(dict["secondsUntilNextPlacement"]);
                    }
            } else {
                // report error message
            }
        }
    }
    xhr.send(params);
}

function onSignIn(googleUser) {
    id_token = googleUser.getAuthResponse().id_token;
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/login');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
        if (xhr.readyState == 4) {
            if (xhr.status == 200) {
                //console.log('Signed in: ' + xhr.responseText);
                var dict = JSON.parse(xhr.responseText);
                if (dict["secondsUntilNextPlacement"]) {
                    updateNextPlacement(dict["secondsUntilNextPlacement"]);
                }
            } else {
                // handle error
            }
        }
    };
    xhr.send('id_token=' + id_token);
}

function signOut() {
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(function () {
      id_token = "";
      showNeedsLoginMode();
    });
}

function updateNextPlacement(intervalUntilNextPlacement) {
    var now = new Date().getTime();
    // Add an extra second because we enable "eligible to place" when distance < 1
    nextPlacementTime = now + (intervalUntilNextPlacement * 1000) + 1000;

    evaluateNextMode();
}

function evaluateNextMode() {
    var auth2 = gapi.auth2.getAuthInstance();
    var loggedIn = auth2.isSignedIn.get();
    if (loggedIn && nextPlacementTime == -1) {
        showLoadingMode();
        return;
    }
    if (!loggedIn) {
        showNeedsLoginMode();
        return;
    } else {
        if (!showingPlacingText) {
            var now = new Date().getTime();
            var distance = nextPlacementTime - now;

            if (distance < 1.01) {
                showEligibleMode();
            } else {
                showCountdownMode();
            }
        }
    }
}

function toHHMMSS(secs) {
    var sec_num = parseInt(secs, 10)
    var hours   = Math.floor(sec_num / 3600) % 24
    var minutes = Math.floor(sec_num / 60) % 60
    var seconds = sec_num % 60
    return [hours,minutes,seconds]
        .map(v => v < 10 ? "0" + v : v)
        .filter((v,i) => v !== "00" || i > 0)
        .join(":")
}

function updateCountdown() {
    var now = new Date().getTime();
    var distance = nextPlacementTime - now;
    document.getElementById("statusmessage").innerHTML = toHHMMSS(distance / 1000) + " until your next chance to place a pixel.";
    evaluateNextMode();
}

function showNeedsLoginMode() {
    document.getElementById("signinbutton").style.visibility = "visible";
    document.getElementById("signoutbutton").style.display = "none";
    document.getElementById("statusmessage").innerHTML = "Sign in with your Google account to place a pixel.";
    if (recurringTimerUpdate != null) {
        clearInterval(recurringTimerUpdate);
        recurringTimerUpdate = null;
    }
}

function showCountdownMode() {
    document.getElementById("signinbutton").style.visibility = "hidden";
    document.getElementById("signoutbutton").style.display = "inline-block";
    if (recurringTimerUpdate == null) {
        recurringTimerUpdate = setInterval(updateCountdown, 1000);
    }
}

function showEligibleMode() {
    document.getElementById("signinbutton").style.visibility = "hidden";
    document.getElementById("signoutbutton").style.display = "inline-block";
    document.getElementById("statusmessage").innerHTML = "Select an LED to toggle.";
    if (recurringTimerUpdate != null) {
        clearInterval(recurringTimerUpdate);
        recurringTimerUpdate = null;
    }
}

function showSubmittingMode() {
    showingPlacingText = true;
    document.getElementById("signinbutton").style.visibility = "hidden";
    document.getElementById("signoutbutton").style.display = "inline-block";
    document.getElementById("statusmessage").innerHTML = "Placing pixel…";
    if (recurringTimerUpdate != null) {
        clearInterval(recurringTimerUpdate);
        recurringTimerUpdate = null;
    }
    setTimeout(function() {
        showingPlacingText = false;
        evaluateNextMode();
    }, 4000);
}

function showLoadingMode() {
    // This should be a transient state while we're waiting for google Sign IN to either indicate login or logout status
    document.getElementById("signinbutton").style.visibility = "hidden";
    document.getElementById("signoutbutton").style.display = "none";
    document.getElementById("statusmessage").innerHTML = "Loading…";
    if (recurringTimerUpdate != null) {
        clearInterval(recurringTimerUpdate);
        recurringTimerUpdate = null;
    }
}
