from __future__ import annotations
import os
import flask as fl
import flask_session as s
import flask_socketio as fs
import uuid
import game

## Setup flask and socketio ##
app = fl.Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = '73nf0n39'
app.config['SESSION_TYPE'] = 'filesystem'
s.Session(app)
socketio = fs.SocketIO(app, manage_session=False)

## Matchmaking ##
matches = {}
class MatchData:
    _matches = {} #Static dictionary of classes where the key is matchId

    def __init__(self):
        self._id = str(uuid.uuid4())
        self._playerIds = []
        #self._name = matchName
        MatchData._matches[self._id] = self
        self._match = None

    def GetMatchId(self) -> str:
        return self._id

    #def GetName(self) -> str:
        #return self._name

    def GetNoOfPlayers(self) -> int:
        return len(self._playerIds)

    def AddPlayer(self, plrId: str) -> None:
        if len(self._playerIds) >= 2:
            raise OverflowError("Match can only have 2 players")
        self._playerIds.append(plrId)

        if len(self._playerIds) >= 2:
            self.StartMatch()

    def HasStarted(self) -> bool:
        return self._match != None

    def StartMatch(self) -> None:
        if len(self._playerIds) < 2:
          raise RuntimeError()

        decks = [game.CardCollection(40), game.CardCollection(40)]
        for i in range(2):
          for j in range(40):
            decks[i].AddCard(game.CardFactory.CreateCard("wolf"))

        self._match = game.Match(decks[0], decks[1])
      

    def GetPlayerId(self, plrNo: int) -> str:
        return self._playerIds[plrNo]

    def GetTurnPlayer(self) -> str:
        return self._playerIds[self._match.GetTurn()]

    def GetPlayerNumber(self, plrId: str) -> int:
        pos = self._playerIds.index(plrId)
        if 0 <= pos <= 1:
            return pos
        raise RuntimeError

    def IsPlayerInMatch(self, plrId: str) -> bool:
        return plrId in self._playerIds

    def VerifyPlayerTurn(self, plrId: str) -> bool:
        return plrId == self._playerIds[self._match.GetTurn()]

    def Sacrifice(self, plrId: str, handPos: int, boardPos: list[int]) -> None:
        if self.VerifyPlayerTurn(plrId):  
          self._match.Sacrifice(handPos, boardPos)

    def PlaceCard(self, plrId: str, handPos: int, boardPos: int) -> None:
        if self.VerifyPlayerTurn(plrId):
          self._match.PlaceCard(handPos, boardPos)

    def InitiateCombat(self, plrId: str,) -> None:
        if self.VerifyPlayerTurn(plrId):
          self._match.InitiateCombat()

    def GetPlayerHand(self, plrNo: int) -> list[dict[str, any]]:

        plr = self._match.GetPlayer(plrNo)
        hand = plr.GetHand()
        noOfCards = hand.GetNoOfCards()
        cardsList = []
        for c in range(noOfCards):
            cardsList.append(vars(CardTransfer(hand.GetCard(c))))

        return cardsList

    def GetBoard(self) -> list[dict[int, dict[str, any]]]:
    #Returns a list with two board sides corresponding to each player (i.e. 1st side for 1st player)
    #Each side is a dict of cards with keys from 0 to 3, each card is a dict
        out = [{},{}]
        for i in range(2):
            plr = self._match.GetPlayer(i)
            board = plr.GetBoard()
            noOfCards = board.GetNoOfCards()
            for c in range(noOfCards):
                card = board.GetCard(c)
                if card != None:
                  out[i][c] = vars(CardTransfer(card))
        return out

    def GetScreenData(self):
      out = []
      
      hands = [self.GetPlayerHand(0), self.GetPlayerHand(1)]
      board = self.GetBoard()

      for i in range(2):
          plrDict = {}
        
          plrBoard = board
          if i == 1:
              plrBoard = [board[1], board[0]]
          plrDict["hand"] = hands[i]
          plrDict["board"] = plrBoard

          plrDict["bones"] = self._match.GetPlayer(i).GetBones()

          plrDict["isTurn"] = self._match.GetTurn() == i

          if plrDict["isTurn"]:
              plrDict["gameState"] = game.GameState.ToString(self._match.GetState())
              if self._match.GetState() == game.GameState.Sacrificed:
                  plrDict["chosenCard"] = self._match.GetChosenCard()
          else:
              plrDict["gameState"] = "NORMAL"

          if i == 1:
            plrDict["scale"] = 10-self._match.GetScale()
          else:
            plrDict["scale"] = self._match.GetScale()
        
          out.append(plrDict)

      return out

    @staticmethod
    def GetMatch(matchId: str) -> MatchData:
        return MatchData._matches[matchId]

    @staticmethod
    def GetMatchList() -> dict[str,str]:
        matchList = {}
        for matchId in MatchData._matches:
            currentMatch = MatchData._matches[matchId]
            matchList[matchId] = {"matchId": matchId, "players": currentMatch.GetNoOfPlayers()}
        return matchList


class CardTransfer:
    def __init__(self, card: game.CardFactory._Card):
        self.type = "terrain"
        if isinstance(card, game.CardFactory._UnitCard):
            self.type = "unit"
            self.power = card.GetPower()
        self.id = str(card.GetId())
          
        self.name = card.GetBase().GetName()
        self.image = "/images/"+card.GetBase().GetImage()
        self.health = card.GetHealth()

        self.costType = card.GetBase().GetCostType()
        self.costAmount = card.GetBase().GetCost()

        self.blood = card.GetBlood()
        
  
### Requests ###
@app.route('/images/<path:path>')
def sendJs(path):
    return fl.send_from_directory('static/images/', path)


@app.route('/')
def lobbyPage():
    return fl.render_template("lobby.html")

@app.route('/match')
def matchPage():
    return fl.render_template("match.html", matchId=fl.request.args.get("id"))


@socketio.on("JoinMatchLobby")
def onJoinMatchLobby():
    for room in fs.rooms(sid=fl.request.sid):
        fs.leave_room(room)
    fs.join_room(fl.request.sid)
    fs.join_room("lobby")

    fs.emit("UpdateMatchList", MatchData.GetMatchList(), room=fl.request.sid)


@socketio.on("CreateMatch")
def OnCreateMatch():

    for room in fs.rooms(sid=fl.request.sid):
        if room.find("match") == 0:
            raise RuntimeError
        elif room != fl.request.sid:
          fs.leave_room(room)

    newMatch = MatchData()

    fs.emit("UpdateMatchList", MatchData.GetMatchList(), room="lobby")

    fs.emit("NewMatchCreated", newMatch.GetMatchId(), room=fl.request.sid)


@socketio.on("JoinMatch")
def OnJoinMatch(matchId):
    match = MatchData.GetMatch(matchId)

    if not "clientId" in fl.session:
        fl.session["clientId"] = str(uuid.uuid4())
    clientId = fl.session.get("clientId") #Client ID is separate from sid as it allows reconnects after disconnecting
    print(clientId)

    for room in fs.rooms(sid=fl.request.sid):
        fs.leave_room(room)
    fs.join_room(clientId)
    fs.join_room("match"+match.GetMatchId())

    if not match.IsPlayerInMatch(clientId):
        #if "matchId" in fl.session:
            #raise RuntimeError

        match.AddPlayer(clientId)
        #fl.session["matchId"] = match.GetMatchId()

        if match.GetNoOfPlayers() >= 2:
            fs.emit("MatchStart", room="match"+match.GetMatchId())
            #Update player screens
            screenData = match.GetScreenData()
            for i in range(2):
                fs.emit("UpdateData", screenData[i], room=match.GetPlayerId(i))
            fs.emit("TurnStart", {"firstTurn": True}, room=match.GetTurnPlayer())
    else:

        if match.HasStarted():
            plrNo = match.GetPlayerNumber(clientId)
            fs.emit("UpdateData", match.GetScreenData()[plrNo], room=clientId)


@socketio.on("SacrificeCards")
def OnSacrificeCards(data):
    clientId = fl.session.get("clientId")

    matchId = data["matchId"]
    handPos = data["handPos"]
    boardPos = data["boardPos"] # list of integers corresponding to board positions

    match = MatchData.GetMatch(matchId)
    match.Sacrifice(clientId, handPos, boardPos)

    #Tell player that it is successful
    #fs.emit("SacrificeSuccessful", room=clientId)
  
    #Update player screens
    screenData = match.GetScreenData()
    for i in range(2):
        fs.emit("UpdateData", screenData[i], room=match.GetPlayerId(i))


@socketio.on("PlaceCard")
def OnPlaceCard(data):
    clientId = fl.session.get("clientId")

    matchId = data["matchId"]
    handPos = data["handPos"]
    boardPos = data["boardPos"] #integer position on the board

    match = MatchData.GetMatch(matchId)
    match.PlaceCard(clientId, handPos, boardPos)

    #Tell player that it is successful
    #fs.emit("PlacingSuccessful", room=clientId)

    #Update player screens
    screenData = match.GetScreenData()
    for i in range(2):
        fs.emit("UpdateData", screenData[i], room=match.GetPlayerId(i))


@socketio.on("InitiateCombat")
def OnInitiateCombat(data):
    clientId = fl.session.get("clientId")

    matchId = data["matchId"]

    match = MatchData.GetMatch(matchId)
    match.PlaceCard(clientId, handPos, boardPos)

    #Tell player that it is successful
    #fs.emit("PlacingSuccessful", room=clientId)

    #Update player screens
    screenData = match.GetScreenData()
    for i in range(2):
        fs.emit("UpdateData", screenData[i], room=match.GetPlayerId(i))
