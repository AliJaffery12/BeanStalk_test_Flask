
from dotenv import load_dotenv
import os
from flask import Flask, jsonify, Response, request 
import requests

import sentry_sdk
from flask import Flask
from datetime import datetime

from flask import current_app

# Add this decorator to instrument your python function

application = Flask(__name__)


@application.route("/")
def testpipeline():
    return 'Hello Pipeline Success'


if __name__ == "__main__":
  

    application.run(debug=True)
