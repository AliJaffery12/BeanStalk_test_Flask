import requests
from langdetect import detect
import openai
from dotenv import load_dotenv
import time
import os
import json
from icecream import ic
from weaviate.util import generate_uuid5
from requests.auth import HTTPBasicAuth

from weaviate_facade import WeaviateFacade
import matplotlib.pyplot as plt


class ArticlesOperator:
    save_location = 'data/pages.json'
    BASE_URL = "https://digitalcareerinstitute.atlassian.net/wiki"

    PROMPT = """
Your task is to answer user's question only based on the provided documentation.
1. Your answer should be as detailed as possible and must include all the necessary information. Provide links to the documents that were used during the answer. Try not to ask additional questions
2. Links should lead to https://digitalcareerinstitute.atlassian.net/servicedesk/customer/portal/1/article/ + ARTICLE_ID
3. Only if user needs to pass any document or request regarding theses topics:
    Absence reporting
    You missed a class and have problems with the reporting.

    Federal Employment Agency support
    You need help communicating with Jobcenter or Agentur für Arbeit.

    Giving feedback
    Let us know how we can improve.

    Internship registration
    Let us know if you found an internship position.

    Language classes
    Do you have a request about the language class?

    Any other issue
    Anything else that is on your mind.

    Official documents
    You need some paperwork from us.

    Job registration
    You got a job? Great – tell us all about it!

    Tutorship
    You are a tutor in your class and have a request.

    Technical Issues
    A device or program doesn't work.

    Leave requests
    You want to request a special leave (needs to be confirmed by job agent first).
Then:
    Give them this link: https://digitalcareerinstitute.atlassian.net/servicedesk/customer/portal/1

Documentation: {documentation}
"""


    def __init__(self, use_cache=True, pages: list = None, recreate_schema=False):
        load_dotenv()
        self.pages = pages
        self.CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
        self.CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
        self.DEPLOYMENT_ID = os.getenv("GPT4_DEPLOYMENT_ID")
        self._client = WeaviateFacade(recreate_schema)

    def load_pages(self, use_cache=False, verbose=False) -> None:

        if use_cache:
            try:
                os.makedirs(os.path.dirname(self.save_location), exist_ok=True)
                with open(self.save_location, 'r') as file:
                    self.pages = json.load(file)
                ic('Loaded pages from cache')
                return
            except FileNotFoundError:
                ic('Cache file not found, downloading pages')

        ic('Downloading pages')
        self._download_pages()

        for page in self.pages:
            try:
                page['language'] = detect(page['text'])
            except:
                ic('Language detection failed for a page')
                ic(page)
                page['language'] = 'unknown'

        if verbose:
            en_count = sum(1 for page in self.pages if page['language'] == 'en')
            de_count = sum(1 for page in self.pages if page['language'] == 'de')

            ic(f"Number of English pages: {en_count}")
            ic(f"Number of German pages: {de_count}")

        ic('Language detection completed for all pages')
        self._save_pages_to_cache()

    def _save_pages_to_cache(self):
        os.makedirs(os.path.dirname(self.save_location), exist_ok=True)
        with open(self.save_location, 'w') as file:
            json.dump(self.pages, file)
        ic('Saved pages to cache')

    def query(self, query: str, limit=5) -> dict:
        return self._client.query.get("Article", ["title", "text", "article_id"]) \
            .with_near_text({"concepts": query}) \
            .with_limit(limit) \
            .do()

    def _get_all_articles(self):
        data = self._client.query.get("Article", ["last_edited"]).do()
        data = data['data']['Get']['Article']
        ic(f'Total of {len(data)} articles')
        return data

    def ask_question(self, query: str, limit=5, verbose=False) -> str:
        """
        Use search query to answer questions about articles. 
        """
        # Get the documentation from search_articles
        documentation = self.query(query, limit)
        pages = documentation['data']['Get']['Article']

        # Get all the pages text and article id
        pages_text = ""
        for i, page in enumerate(reversed(pages)):
            page_text = page.get("text", "").replace("`", "")
            article_id = page.get("article_id", "")
            pages_text += f"Document {i+1}: (link: https://digitalcareerinstitute.atlassian.net/servicedesk/customer/portal/1/article/{article_id})\n```Text: {page_text}```\n\n"

        if verbose:
            ic(pages_text)

        # Prepare the request
        data = {
            "messages": [
                {"role": "system",
                 "content": f"{self.PROMPT.format(documentation=documentation)}"},
                {"role": "user", "content": query}
            ]
        }


        url = f"{os.getenv('AZURE_OPENAI_BASE')}/openai/deployments/{self.DEPLOYMENT_ID}/chat/completions?api-version=2023-05-15"
        headers = {
            "Content-Type": "application/json",
            "api-key": os.getenv('AZURE_OPENAI_KEY')
        }
        # Send the request to OpenAI

        retries = 0
        while retries < 3:
            response = requests.post(url, headers=headers, json=data)
            if response.json().get('error', {}).get('code') == 'InternalServerError':
                ic(response.json())
                time.sleep(3)
                retries += 1
                ic("Failed to get an answer. Retrying...")
            else:
                if retries > 0:
                    ic("Retry successful!")
                break

        try:
            answer = response.json()['choices'][0]['message']['content']
        except KeyError:
            ic(response.json())
            raise Exception("Failed to get answer from OpenAI")

        return answer

    def upload(self, limit=None):
        pages_to_upload = [page for page in self.pages.copy() if page.get("text") != ""]

        # 1. Get all data from Weaviate
        weaviate_data = self._get_all_articles()

        # 2. Iterate through data, if last_edited is the same, then remove it from pages to load
        for article in weaviate_data:
            last_edited = article.get("last_edited")
            if last_edited:
                # should it compare their time?
                pages_to_upload = [page for page in pages_to_upload if page.get("last_edited") != last_edited]

        if limit is not None:
            pages_to_upload = pages_to_upload[:limit]

        ic(f'Total of {len(pages_to_upload)} pages are uploading')

        self._client.upload_data(pages_to_upload, 'Article')

        ic(f'Total of {len(pages_to_upload)} articles were uploaded')

        # Advanced logging to show skipped files
        skipped_files = [page for page in self.pages if
                         page.get("last_edited") in [article.get("last_edited") for article in weaviate_data]]
        ic(f'Total of {len(skipped_files)} files were skipped because they are already in Weaviate')

    @classmethod
    def _adf_to_plain_text(cls, node, is_root=True):
        """Convert an ADF node to its plain text representation, ensuring better spacing between block elements."""
        node_type = node.get("type", "")

        # Base case: if the node is a text node
        if node_type == "text":
            text = node.get("text", "")
            marks = node.get("marks", [])

            for mark in marks:
                mark_type = mark.get("type", "")
                # Handle some of the marks. Others can be added as needed.
                if mark_type == "link":
                    url = mark.get("attrs", {}).get("url", "")
                    text = f"{text} <{url}>"
                # Other mark types can be added here as required

            return text

        # If the node is a list item, add a newline at the end
        elif node_type == "listItem":
            return "".join(
                cls._adf_to_plain_text(child_node, is_root=False) for child_node in node.get("content", [])) + "\n"

        # If the node is a code block, wrap the content in backticks
        elif node_type == "codeBlock":
            return f"```\n{''.join(cls._adf_to_plain_text(child_node, is_root=False) for child_node in node.get('content', []))}\n```\n"

        # If the node is a bullet list, add bullet points before each item
        elif node_type == "bulletList":
            return "\n".join(
                f"- {cls._adf_to_plain_text(child_node, is_root=False)}" for child_node in node.get("content", []))

        # Recursive case: if the node has content
        content = node.get("content", [])

        # Add a newline between block elements but not within inline content
        separator = "\n" if is_root else ""
        return separator.join(cls._adf_to_plain_text(child_node, is_root=False) for child_node in content).strip()

    def _download_pages(self, debug=False, cache=True):
        endpoint = "/api/v2/spaces/1474564/pages?body-format=atlas_doc_format&status=current&start=0&limit=250"
        auth = HTTPBasicAuth(self.CONFLUENCE_USERNAME, self.CONFLUENCE_API_TOKEN)
        headers = {"Accept": "application/json"}

        pages = []
        while True:
            response = requests.get(self.BASE_URL + endpoint, headers=headers, auth=auth)
            if response.status_code != 200:
                raise Exception("Failed to fetch space content. Status code:", response.status_code)

            json_data = response.json()
            pages.append(json_data)

            if 'next' in json_data['_links']:
                endpoint = json_data['_links']['next']
            else:
                break

        # Merge batches of pages into a single array
        merged_pages = []
        for batch in pages:
            merged_pages.extend(batch['results'])

        # Process the merged pages
        page_values = []
        for page in merged_pages:
            text = self._adf_to_plain_text(json.loads(page['body']['atlas_doc_format']['value']))
            page_value = {
                'article_id': page['id'],
                'title': page['title'],
                'last_edited': page['version']['createdAt'],
                'text': text,
                'words': len(text.split())
            }
            page_values.append(page_value)

        if debug:
            # Calculate min, max, and average word count
            word_counts = [page['words'] for page in page_values]
            min_word_count = min(word_counts)
            max_word_count = max(word_counts)
            average_word_count = sum(word_counts) / len(word_counts)
            # Print the results
            print(f"Minimum word count: {min_word_count}")
            print(f"Maximum word count: {max_word_count}")
            print(f"Average word count: {average_word_count}")
            # Plotting logic can be added here if required

        if cache:
            self.save_pages(page_values)

        self.pages = page_values

    @classmethod
    def save_pages(cls, page_values):
        with open(cls.save_location, 'w') as f:
            json.dump(page_values, f)
