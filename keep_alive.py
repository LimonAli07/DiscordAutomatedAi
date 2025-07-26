from flask import Flask
from threading import Thread
import logging

# Configure logging
logger = logging.getLogger(__name__)

app = Flask('')

@app.route('/')
def home():
    return "Discord bot is alive!"

def run():
    logger.info("Starting Flask server for keep-alive ping")
    try:
        app.run(host='0.0.0.0', port=8080)
    except Exception as e:
        logger.error(f"Error in Flask server: {e}")

def keep_alive():
    """Start a Flask server in a separate thread to keep the Replit project alive."""
    t = Thread(target=run)
    t.daemon = True  # Set as daemon so it terminates when the main program exits
    t.start()
    logger.info("Keep-alive server started in background thread")