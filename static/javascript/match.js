
// Constants //
const GameStates = {
    NONE: 0,
    DRAWING: 1,
    NORMAL: 2,
    SACRIFICING: 3,
    PLACING: 4,
    COMBAT: 5
}

const AMBIENCE = new Audio("/static/audio/DeathcardCabin.mp3");
AMBIENCE.volume = 0.2;
AMBIENCE.loop = true;

const BELLRING = new Audio("/static/audio/bellRing.mp3");

const CARDSLIP = new Audio("/static/audio/cardSlip.mp3");
const CARDDRAW = new Audio("/static/audio/cardDraw.mp3");
const CARDHIT = new Audio("/static/audio/cardHit.mp3");


// Global Data //
var socket = io();
var board = [{},{}];
var hand = [];
var bones = 0;

var gameState = GameStates.NONE;
var chosenCard = -1;
var bloodTotal = 0; //Total blood in sacrifice so far
var cardsToSacrifice = []; //List of integers that coresspond to board position
var hasSacrificed = false; //true if sacrifice is successful and card is being placed


// Events //
$(document).ready(function() {
    socket.emit("JoinMatch", matchId);
});


socket.on('UpdateData', function(data) {
    console.log(data);
    hand = data["hand"];
    board = data["board"];
    bones = data["bones"];

    if (data["isTurn"]) {
        $(".speech").text("Your turn...");
        if (data["gameState"] == "SACRIFICED") {
            ChangeGameState(GameStates.PLACING);
            hasSacrificed = true;
        } else if (data["gameState"] == "DRAWING") {
            ChangeGameState(GameStates.DRAWING);
        } else if (data["gameState"] == "NORMAL") {
            ChangeGameState(GameStates.NORMAL);
        }
    } else {
        $(".speech").text("Wait...");
    }

    // if ("chosenCard" in data) {
    //     chosenCard = data["chosenCard"];
    // }
  
    UpdateScreen();

    if (gameState != GameStates.NONE) {
        $(".eyes").removeAttr('hidden');
        if (AMBIENCE.paused) {
          AMBIENCE.play();
        }
    }
});

socket.on('MatchStart', function() {
    ChangeGameState(GameStates.NORMAL);
    $(".speech").text(" ");
    $(".eyes").removeAttr('hidden');
    //UpdateScreen();
});



$(document).on("click", ".handCard", function() {
    var cardLi = $(this);
    var cardData = GetCardLiData(cardLi);
  
    if (gameState == GameStates.NORMAL) { //Placing a card
        if (cardData.costType == 1) {
            if (cardData.costAmount <= GetBoardBloodTotal()) {
                ChangeGameState(GameStates.SACRIFICING);
                chosenCard = cardLi.index();
                cardLi.addClass("chosenCard");
                MoveView("w");
            } else { //Not enough blood to sacrifice
                SpeakMessage("The creature demands more blood...", 2000);
                cardLi.addClass("shakingCard");
                setTimeout(function(x) {
                    x.removeClass("shakingCard");
                }, 300, cardLi);
            }
        } else {
            if (cardData.costType == 2 && cardData.costAmount > bones) {
                SpeakMessage("The creature demands more bones...", 2000);
                cardLi.addClass("shakingCard");
                setTimeout(function(x) {
                    x.removeClass("shakingCard");
                }, 300, cardLi);
            } else {
                gameState = GameStates.PLACING;
                chosenCard = cardLi.index();
                cardLi.addClass("chosenCard");
                MoveView("w");
            }
        }
    }
})

// $(document).on("mouseenter", ".handCard", function(event) {
//     CARDSLIP.currentTime = 0;
//     CARDSLIP.play();
// });



$(document).on("click",".boardCard", function() {
    var boardPos = $(this).parent().index();
    var boardCardLi = $(this);
    var boardCardData = GetCardLiData(boardCardLi);
    
    if (gameState == GameStates.SACRIFICING) {
        if (!cardsToSacrifice.includes(boardPos)) {
            cardsToSacrifice.push(boardPos)
            bloodTotal += boardCardData.blood;

            boardCardLi.children(".sacrificeHover").remove();
            boardCardLi.append($("<img src='/images/sacrificeSymbol.png' class='sacrificeSymbol'></img>"));

            var chosenCardData = GetCardLiData($(".chosenCard"));
            if (bloodTotal >= chosenCardData.costAmount) {
                SacrificeCards();
            }
        }
    }
});



$(document).on("click",".allySide>.boardSpace", function(event) {
    if (event.target != event.currentTarget) {
        return;
    }
    
    var boardPos = $(this).index();
    if (gameState == GameStates.PLACING) {
        PlaceCard(boardPos);
    }
});



$(document).on("click",".bell", function(event) {
    if (gameState == GameStates.NORMAL) {
        BELLRING.play();
    }
});



$(window).keypress(function(event) {
    if (event.which == 87 || event.which == 119) { //Move forward
        MoveView("w");
    } else if (event.which == 83 || event.which == 115) {
        MoveView("s");
    }
});

$(window).on('wheel', function(event){
    if(Math.abs(event.originalEvent.deltaY) > 20){
        if(event.originalEvent.deltaY < 0){
            MoveView("w");
        } else {
            MoveView("s");
        }
    }
});


// Functions //
function PrintResponse(response) {
    console.log(response);
}


function SpeakMessage(newText, time) { //time = 1000 = 1 second
    var oldText = $(".speech").text();
    $(".speech").text(newText);
    setTimeout(function(x) {
        $(".speech").text(x);
    }, time, oldText);
}


function GetBoardBloodTotal() {
    var boardBloodTotal = 0;
    var allySide = $(".allySide");
    for (let i = 0; i < 4; i++) {
        var currentSpace = allySide.eq(i);
        if (currentSpace.has(".card").length) {
            var cardData = GetCardLiData(currentSpace.find(".card"));
            boardBloodTotal += cardData.blood;
        }
    }
    return boardBloodTotal;
}


function CreateCardLi(cardDict) {
    return "<li class='handCard card'>"+
    "<p class='cardName'>"+ cardDict["name"] +"</p>"+
    "<img src='"+ cardDict["image"] +"' class='cardImage'>"+
    "<p class='cardPower'>"+ cardDict["power"] +"</p>"+
    "<p class='cardHealth'>"+ cardDict["health"] +"</p>"+
    "<p hidden class='costType'>"+ cardDict["costType"] +"</p>"+
    "<p hidden class='costAmount'>"+ cardDict["costAmount"] +"</p>"+
    "<p hidden class='cardBlood'>"+ cardDict["blood"] +"</p>"+
    "<p hidden class='cardId'>"+ cardDict["id"] +"</p>"+
    "</li>";
}


function ChangeGameState(newState) {
    switch (newState) {
        case GameStates.NORMAL:
            gameState = GameStates.NORMAL;
            ResetSacrificeData();
            $(".allySide .shiveringCard").removeClass("shiveringCard");
            $(".sacrificeHover").remove();
            $(".sacrificeSymbol").remove();
            break;
        case GameStates.SACRIFICING:
            gameState = GameStates.SACRIFICING;
            $(".allySide .card").addClass("shiveringCard").append($("<img src='/images/sacrificeHover.png' class='sacrificeHover'></img>"));
            break;
      case GameStates.PLACING:
            gameState = GameStates.PLACING;
            break;
      case GameStates.DRAWING:
            gameState = GameStates.DRAWING;
            break;
    }
}


function SacrificeCards() {
    socket.emit("SacrificeCards", {"matchId": matchId, "handPos": chosenCard, "boardPos": cardsToSacrifice});
    ChangeGameState(GameStates.PLACING);
    hasSacrificed = true;
}


function PlaceCard(boardPos) {
    socket.emit("PlaceCard", {"matchId": matchId, "handPos": chosenCard, "boardPos": boardPos});
    ChangeGameState(GameStates.NORMAL);
}


function ResetSacrificeData() {
    chosenCard = -1;
    hasSacrificed = false;
    cardsToSacrifice = [];
    bloodTotal = 0;
}


function MoveView(direction) {
    if (direction == "w") {
        $(".vision").removeClass().addClass("vision").addClass("topView");
        $(".eyes").removeClass().addClass("eyes").addClass("topView");
        $(".bell").removeClass().addClass("bell").addClass("topView");
        $(".scale").removeClass().addClass("scale").addClass("topView");
        
    } else if (direction == "s" && !hasSacrificed) {
        $(".vision").removeClass().addClass("vision");
        $(".eyes").removeClass().addClass("eyes");
        $(".bell").removeClass().addClass("bell");
        $(".scale").removeClass().addClass("scale");
        //Stop sacrificing
        if (gameState == GameStates.SACRIFICING || gameState == GameStates.PLACING) {
            ChangeGameState(GameStates.NORMAL);
            $(".hand .chosenCard").removeClass("chosenCard");
        }
    }
}


function UpdateHand() {
    var handDiv = $(".hand");
    var handDivChildren = handDiv.children(".card");
    
    handDivCards = [];
    handDivCardChecked = []; //Condition to check whether each card in current hand belongs there
    for (let i = 0; i < handDivChildren.length; i++) {
        handDivCards.push(GetCardLiData(handDivChildren.eq(i)));
        handDivCardChecked.push(false);
    }

    //Add any cards not already in hand
    for (var i in hand) {
        var currentCard = hand[i];
        var isCardAlreadyInHand = false;
        for (let j = 0; j < handDivCards.length; j++) {
            if (handDivCards[j].id == currentCard.id) {
                isCardAlreadyInHand = true;
                handDivCardChecked[j] = true;
                break;
            }
        }

        if (!isCardAlreadyInHand) {
            var newCard = $(CreateCardLi(hand[i])).addClass("handCard").addClass("justDrawn");
            handDiv.append(newCard);
            setTimeout(function(x) {
                x.removeClass("justDrawn");
            }, 1, newCard);
        }
    }

    //Remove card if it doesn't exist
    handDivChildren = handDiv.children(".card");
    var cardsDeleted = 0;
    for (let i = 0; i < handDivCardChecked.length; i++) { //If card in hand isn't confirmed to exist, then remove them
        if (!handDivCardChecked[i]) {
            handDivChildren.eq(i-cardsDeleted).remove();
            cardsDeleted += 1;
        }
    }

    //Chosen card hand class
    if (chosenCard != -1) {
        handDiv.addClass("handChosen");
        handDiv.children().eq(chosenCard).addClass("chosenCard");
    } else {
        handDiv.removeClass("handChosen");
    }
}

function UpdateBoard() {
    var boardDiv = [$(".allySide"), $(".enemySide")];
    for (let i = 0; i < 2; i++) {
        for (let j = 0; j < 4; j++) {
            var boardSpaceDiv = boardDiv[i].children().eq(j)

            //Check if new card needs to be placed
            var placeNewCard = false;
            var boardCardDataExists = j in board[i];
            if (boardCardDataExists) {
                if (boardSpaceDiv.has(".card").length) {
                    var currentCardData = GetCardLiData(boardSpaceDiv.children(".card").eq(0));
                    console.log(currentCardData.id);
                    console.log(board[i][j]);
                    if (!(currentCardData.id === board[i][j].id)) {
                        placeNewCard = true;
                    }
                } else {
                    placeNewCard = true;
                }
            }
          
            if (placeNewCard) {
                CardDeath(boardSpaceDiv);
                boardSpaceDiv.append(CreateCardLi(board[i][j]));
                var card = boardSpaceDiv.children(":not(.deadCard)").eq(0).removeClass().addClass("card").addClass("boardCard").addClass("fromHand");
                setTimeout(function(x) {
                    x.removeClass("fromHand");
                }, 1, card);
                CARDDRAW.play();
            } else if (!(boardCardDataExists)) {
                CardDeath(boardSpaceDiv);
            }
        }
    }
}

function CardDeath(boardSpaceDiv) {
    var cardDiv = boardSpaceDiv.children().eq(0);
    cardDiv.addClass("deadCard");
    setTimeout(function(x) {
        x.remove();
    }, 500, cardDiv);
}


function UpdateScreen() {
  UpdateHand();
  UpdateBoard();
}



// HTML Utilities //
function GetCardLiData(cardLi) {
    var out = {}
    out.costType = parseInt(cardLi.children(".costType").text());
    out.costAmount = parseInt(cardLi.children(".costAmount").text());
    out.blood = parseInt(cardLi.children(".cardBlood").text());
    out.id = cardLi.children(".cardId").text();
    return out;
}