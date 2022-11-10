
// Global Data //
var socket = io()
var matches = {}

// Events //
$(document).ready(function() {
    JoinMatchLobby();
});

socket.on('UpdateMatchList', function(message) {
    matches = message;
    RenderMatchList();
});

//Create match button
$(document).on("click", ".matchEntry", function() {
    mId = $(this).text()
    JoinMatch(mId);
});

$(document).on("click", ".createMatchButton", function() {
    CreateMatch();
});

socket.on('NewMatchCreated', function(matchId) {
    JoinMatch(matchId)
});


// Functions //
function PrintResponse(response) {
    console.log(response)
}

function JoinMatchLobby() {
    socket.emit("JoinMatchLobby")
}

function RenderMatchList() {
    var matchList = $(".matchList")
    matchList.empty()
    for (var mid in matches) {
        matchList.append("<li class='matchEntry'>"+mid+"</li>");
    }
}

function CreateMatch() {
    socket.emit("CreateMatch")
}

function JoinMatch(matchId) {
    window.location.href = "/match?id="+matchId
}