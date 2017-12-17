// Sorry this is a total mess! I just hacked it up on a Sunday and have no idea how to write web pages.

//Statics
var nextPlacementTime = -1;
var recurringTimerUpdate = null;
var showingPlacingText = false

function initialize() {
    nextPlacementTime = new Date().getTime();
    updateNextPlacement(5);
    evaluateNextMode();
}

function requestToggle(coord) {
    var now = new Date().getTime();
    var distance = nextPlacementTime - now;
    if (distance < 1.01) {
        showSubmittingMode();
        updateNextPlacement(30);
    }
}

function updateNextPlacement(intervalUntilNextPlacement) {
    var now = new Date().getTime();
    // Add an extra second because we enable "eligible to place" when distance < 1
    nextPlacementTime = now + (intervalUntilNextPlacement * 1000) + 1000;

    evaluateNextMode();
}

function evaluateNextMode() {
    if (nextPlacementTime == -1) {
        showLoadingMode();
        return;
    }

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
    document.getElementById("statusmessage").innerHTML = toHHMMSS(distance / 1000) + " until your next chance to place a pixel. [simulated]";
    evaluateNextMode();
}

function showCountdownMode() {
    if (recurringTimerUpdate == null) {
        recurringTimerUpdate = setInterval(updateCountdown, 1000);
    }
}

function showEligibleMode() {
    document.getElementById("statusmessage").innerHTML = "Select an LED to toggle. [simulated]";
    if (recurringTimerUpdate != null) {
        clearInterval(recurringTimerUpdate);
        recurringTimerUpdate = null;
    }
}

function showSubmittingMode() {
    showingPlacingText = true;
    document.getElementById("statusmessage").innerHTML = "Placing pixel… [simulated]";
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
    document.getElementById("statusmessage").innerHTML = "Loading… [simulated]";
    if (recurringTimerUpdate != null) {
        clearInterval(recurringTimerUpdate);
        recurringTimerUpdate = null;
    }
}
