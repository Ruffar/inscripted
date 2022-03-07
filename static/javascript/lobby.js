
// Global Data //
var socket = io()
var matches = {}

// Events //
$(document).ready(function() {
    JoinMatchLobby()
});

socket.on('UpdateMatchList', function(message) {
    matches = message;
    RenderMatchList();
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
    for (var matchId in matches) {
        matchList.append("<li class='matchEntry'>"+matches[matchId]+"</li>");
    }
}

function CreateMatch() {
    $.ajax({
        url: "/createMatch",
        type: "POST",

        success: function(response) {
            console.log(response)
        },
        error: PrintResponse
    })
}