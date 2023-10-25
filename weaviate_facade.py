import os
from typing import Tuple

from weaviate import AuthApiKey, Client
from weaviate.util import generate_uuid5
from schema import article_class
import requests

class WeaviateFacade:
    """Facade for the Weaviate client
    todo: make a singleton
    """
    def __init__(self, recreate_schema: bool = False):
        self._client = self._create_client()
        self.query = self._client.query

        if recreate_schema:
            self.purge_schema()
            self.create_class(article_class)

        self.base_url = os.getenv('AZURE_OPENAI_BASE')
        self.api_key = os.getenv('AZURE_OPENAI_KEY')
        self.headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

    @staticmethod
    def _create_client() -> Client:
        """Create the Weaviate client instance"""
        weaviate_url = os.environ['WEAVIATE_URL']
        weaviate_api_key = os.environ['WEAVIATE_API_KEY']
        openai_api_key = os.environ['AZURE_OPENAI_KEY']

        if (not (weaviate_url and weaviate_api_key and openai_api_key)):
            print("Please provide all the required ENV variables in .env file!")
            raise Exception("Missing ENV variables")

        return Client(
            url=weaviate_url,
            auth_client_secret=AuthApiKey(api_key=weaviate_api_key),
            additional_headers={
                "X-Azure-Api-Key": openai_api_key
            }
        )

    def purge_schema(self) -> None:
        """Wipe out the schema with all objects"""
        self._client.schema.delete_all()
        print("Deleted the current schema with all objects")

    def create_class(self, record_class) -> None:
        """Recreate the given class in the schema"""
        self._client.schema.create_class(record_class)
        print(f'Class {record_class} was successfully re-created')

    def upload_data(self, data, data_type) -> None:
        """
        Upload the data to the db
        For each record, reproducible uuid is generated so the same entries won't be added again
        """
        with self._client.batch(
                batch_size=200,
                num_workers=2
        ) as batch:
            for idx, record in enumerate(data):
                class_name, class_object = self.mapper(data_type, record)
                batch.add_data_object(
                    class_object,
                    class_name,
                    uuid=generate_uuid5(class_object)
                )
                print(f'imported {type} {idx + 1}')

        print(f'Total of {len(data)} records were uploaded')

    def search_articles(self, query: str, limit=5) -> dict:
        return self._client.query.get("Article", ["title", "text", "article_id"]) \
            .with_near_text({"concepts": query}) \
            .with_limit(limit) \
            .do()

    def search_messages(self, chat_identifier, query: str, limit=5, min_words: int = 50) -> dict:
        with_where = None
        if type(chat_identifier) == int:
            with_where = {
                "path": ["chat_id"],
                "operator": "Equal",
                "valueInt": chat_identifier
            }
        elif type(chat_identifier) == str:
            with_where = {
                "path": ["username"],
                "operator": "Equal",
                "valueString": chat_identifier
            }

        return self._client.query.get("Message", ["text", "chat_id", "message_id"]) \
            .with_near_text({"concepts": query}) \
            .with_where(with_where) \
            .with_limit(limit) \
            .do()

    @staticmethod
    def mapper(data_type, record) -> Tuple[str, dict]:
        """Mappings for uploading the data"""
        record_class = {
            'Article': article_class,
        }[data_type]

        class_name = record_class["class"]
        obj = {}

        for prop in record_class["properties"]:
            key = prop["name"]
            obj[key] = record[key]

        return class_name, obj
