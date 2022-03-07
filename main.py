import gameController

#gameController.app.run(port='8080')
gameController.socketio.run(gameController.app, host='0.0.0.0', port=8080)
