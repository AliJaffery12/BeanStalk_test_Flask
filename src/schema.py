
article_class = {
    # Class definition
    "class": "Article",

    # Property definitions
    "properties": [
        {
            "name": "title",
            "description": "The title of an article",
            "dataType": ["text"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": False,
                    "vectorizePropertyName": False
                }
            }
        },
        {
            "name": "text",
            "description": "Markdown text content",
            "dataType": ["text"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": False,
                    "vectorizePropertyName": False
                }
            }
        },
        {
            "name": "language",
            "description": "Language of the text",
            "dataType": ["text"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": False,
                    "vectorizePropertyName": False
                }
            }
        },
        {
            "name": "article_id",
            "description": "Confluence article id",
            "dataType": ["text"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": True,
                    "vectorizePropertyName": False
                }
            }
        },
        {
            "name": "last_edited",
            "description": "Date when the article was last changed",
            "dataType": ["date"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": True,
                    "vectorizePropertyName": False
                }
            }
        },
    ],

    # Specify a vectorizer
    "vectorizer": "text2vec-openai",

    # Module settings
    "moduleConfig": {
        "text2vec-openai": {
            "vectorizeClassName": False,
            "model": "ada",
            "modelVersion": "002",
            "type": "text",
            "resourceName": "student-chatbot",
            "deploymentId": "embeddings",
        },
        "qna-openai": {
            "model": "text-davinci-003"
        },
        "generative-openai": {
            "model": "gpt-3.5-turbo"
        }
    },
}