A Chat Bot to answer general questions from DCI Students

# How to run the project
1. clone the repo and then open it in your favourite IDE.
2. Go to the src folder
3. install the require dependencies from the requiremnts.txt file via this command and make sure you are using python 3.10.8 or lower version 
4. pip install -r requirements.txt
5. run the flask app via
6. python app.py
# Requirements

## Functionality
Students can write the Bot a question and the Bot should answer it if possible.

- If the Bot can not find a good answer, it should let the student know this and present them with alternative ways to seek assistance.
- The bot's purpose is to answer questions that are covered in the [Studentsportal](https://digitalcareerinstitute.atlassian.net/wiki/spaces/STP/overview?homepageId=1474703)
- If the Bot is asked a question outside of it's predefined scope, it should let the student know this and present them with alternative ways to seek assistance. 

## UI
Students will use the ChatBot through a Chat interface in moodle.

During initial development, Slack is used as the UI to interact with the Bot.

## Data source and storage
- The data source for answering student questions is this Confluence space: https://digitalcareerinstitute.atlassian.net/wiki/spaces/STP
- All pages of the space need to be vectorized and stored in a vector database
- The data on the confluence space is subject to change. The vector database needs to reflect the current state of the confluence space:
  - pages that are deleted, need to be removed from the vector index
  - when pages change, the corresponding vector needs to be re-created
  - when a new page is added, it's vector needs to be added to the vector DB

## AI
- The App should use the OpenAI API to generate answers
- The models gpt-3.5-turbo and gpt-4 should be evaluated for use in the app. The model providing satisfactory answers at reasonable speed should be selected.

## Deployment and Hosting
- The App should be hosted on AWS as an EC2 instance
- There should be a pipeline from the GitHub repo of the App to AWS on the `main` branch
