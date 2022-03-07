from __future__ import annotations
import os
import flask as fl
import flask_socketio as fs
import uuid
import game

## Setup flask and socketio ##
app = fl.Flask(__name__,static_folder='static',template_folder='templates')
app.config['SECRET_KEY'] = '73nf0n39'
socketio = fs.SocketIO(app)

## Matchmaking ##
matches = {}
class MatchData:
    _matches = {} #Static dictionary of classes where the key is matchId

    def __init__(self, matchName: str):
        self._id = str(uuid.uuid4())
        self._playerIds = []
        self._name = matchName
        MatchData._matches[self._id] = self

    def GetName(self) -> str:
        return self._name

    def GetNoOfPlayers(self) -> int:
        return len(self._playerIds)

    def AddPlayer(self, plrId: str) -> None:
        if len(self._playerIds) >= 2:
            raise OverflowError("Match can only have 2 players")
        self._playerIds.append(plrId)

    @staticmethod
    def GetMatch(matchId: str) -> MatchData:
        return MatchData._matches[matchId]

    @staticmethod
    def GetMatchList() -> dict[str,str]:
        matchList = {}
        for matchId in MatchData._matches:
            currentMatch = MatchData._matches[matchId]
            matchList[matchId] = {"name": currentMatch.GetName(), "players": currentMatch.GetNoOfPlayers()}
        return matchList

MatchData("toilet")

## Requests ##
@app.route('/images/<path:path>')
def send_js(path):
    return fl.send_from_directory('static/images/', path)


@app.route('/')
def lobbyPage():
    return fl.render_template("lobby.html")

@app.route('/match')
def matchPage():
    return fl.render_template("match.html")


@socketio.on("JoinMatchLobby")
def onJoinMatchLobby():
    for room in fs.rooms(sid=fl.request.sid):
        if room != fl.request.sid:
            fs.leave_room(room)
    fs.join_room("lobby")

    fs.emit('UpdateMatchList', MatchData.GetMatchList(), room=fl.request.sid)
