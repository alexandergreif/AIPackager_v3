"""Run the Flask application."""

from src.app import create_app

if __name__ == "__main__":
    app, socketio = create_app()

    socketio.run(app, debug=True, port=5001)
