import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from icecream import ic
from articles_operator import ArticlesOperator


class SlackBotFacade:
    def __init__(self):
        ic(os.environ.get("SLACK_SIGNING_SECRET"))

        self.app = App(
            token=os.environ.get("SLACK_BOT_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
        )
        self.operator = ArticlesOperator()

    def start(self):
        @self.app.event("message")
        def message_hello(message, say):
            message_text = self.extract_text_from_blocks(message)
            ic(message_text)
            ic(say("Searching for the answer... 🔎"))

            answer = self.operator.ask_question(message_text, verbore=True)
            say(answer)

        SocketModeHandler(self.app, os.environ["SLACK_APP_TOKEN"]).start()

    def extract_text_from_blocks(self, data):
        """
        Extracts plain text from the given data structure.
        """
        blocks = data.get('blocks', [])

        texts = []

        for block in blocks:
            block_elements = block.get('elements', [])

            for element in block_elements:
                if element['type'] == 'rich_text_section':
                    nested_elements = element.get('elements', [])

                    for nested_element in nested_elements:
                        if nested_element['type'] == 'text':
                            texts.append(nested_element['text'])

        # Join all the extracted texts
        plain_text = ' '.join(texts)
        return plain_text
