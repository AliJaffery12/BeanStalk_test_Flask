from flask import Flask, jsonify,Response
import requests
from dotenv import load_dotenv
import os
from requests.auth import HTTPBasicAuth
import json

def GetSpacePages():
    CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
    CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
    
    base_url = "https://digitalcareerinstitute.atlassian.net/wiki"
    endpoint = "/api/v2/spaces/1474564/pages?body-format=atlas_doc_format&status=current&start=0&limit=250"
    auth = HTTPBasicAuth(CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)
    headers = {"Accept": "application/json"}

    pages = []

    while True:
        response = requests.get(base_url + endpoint, headers=headers, auth=auth)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch space content", "status_code": response.status_code})

        json_data = json.loads(response.text)

        # Extract and append text content from the current page
        text_content = extract_text_from_json(json_data)
        pages.append(json_data)

        if 'next' in json_data['_links']:
            endpoint = json_data['_links']['next']
        else:
            break

    # Merge batches of pages in a single array
    merged_pages = []
    for batch in pages:
        merged_pages.extend(batch['results'])

    total_pages = len(merged_pages)
    print(f"Fetched {total_pages} pages in total.")
    
    return jsonify(merged_pages)

def extract_text_from_json(json_data):
    extracted_text = []

    def recursive_extract(element):
        if isinstance(element, dict):
            if "type" in element and element["type"] == "text" and "text" in element:
                extracted_text.append(element["text"])
            for key, value in element.items():
                recursive_extract(value)
        elif isinstance(element, list):
            for item in element:
                recursive_extract(item)

    # Loop through the "results" array to extract text content
    if "results" in json_data:
        for result in json_data["results"]:
            if "body" in result and "atlas_doc_format" in result["body"]:
                doc_format = result["body"]["atlas_doc_format"]
                if "value" in doc_format:
                    doc_value = json.loads(doc_format["value"])
                    recursive_extract(doc_value)

    return " ".join(extracted_text)
