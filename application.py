from icecream import ic
from articles_operator import ArticlesOperator
from dotenv import load_dotenv
import os
from flask import Flask, jsonify, Response, request 
import requests
from Confluence_data import GetSpacePages, extract_text_from_json
import sentry_sdk
from flask import Flask
from datetime import datetime
from sentry_sdk.crons import monitor
from flask import current_app
import schedule
import time
# Add this decorator to instrument your python function

sentry_sdk.init(
    dsn="https://bd9804963261404b14353239ecf78bda@o1264169.ingest.sentry.io/4506064744349696",
    traces_sample_rate=1.0,
)


application = Flask(__name__)


MOODLE_API_TOKEN = os.getenv("MOODLE_TOKEN")



@application.route("/")
def hello_world():
    try:
        get_space_pages()
        loader = ArticlesOperator()
        loader.load_pages()
        loader.upload()
   
        # Raises an error
        return "<p>Passed !</p>"
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return "<p>Error occurred. The error has been reported to Sentry.</p>"
    
@application.route("/confluence/space/AllSpacePages")
def get_space_pages():
    return GetSpacePages()

if __name__ == "__main__":
    loader = ArticlesOperator()
    loader.load_pages()
    loader.upload()
   

    ic(loader.ask_question('how to fix my zoom?', verbose=True))
    application.run(debug=True)
