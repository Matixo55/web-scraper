import json
import os
import re

import pytest
import requests
from flask import Flask, current_app

global text_id, images_id

app = Flask(__name__)


def test_server():
    with app.app_context():
        # Is online
        response = requests.get('http://flask_app:5000/')
        assert response.status_code == 200


def test_get_text():
    global text_id
    with app.app_context():
        # Malformed URL
        response = requests.post('http://flask_app:5000/get/text',
                                 data='{"url":"www.noturl"}',
                                 headers={'content-type': 'text/plain'})
        assert response.status_code == 400 and "Invalid url" in response.text
        # Invalid URL
        response = requests.post('http://flask_app:5000/get/text',
                                 data='{"url":"https://www.google"}',
                                 headers={'content-type': 'text/plain'})
        assert response.status_code == 400 and "Invalid url" in response.text
        # Correct request
        response = requests.post('http://flask_app:5000/get/text',
                                 data='{"url":"https://www.google.com"}',
                                 headers={'content-type': 'text/plain'})
        assert response.status_code == 201 and re.match('{"id":[0-9]+}\n', response.text)
        data = json.loads(response.text)
        text_id = data["id"]


def test_get_images():
    global images_id
    with app.app_context():
        # Malformed URL
        response = requests.post('http://flask_app:5000/get/images',
                                 data='{"url":"www.noturl"}',
                                 headers={'content-type': 'text/plain'})
        assert response.status_code == 400 and "Invalid url" in response.text
        # Invalid URL
        response = requests.post('http://flask_app:5000/get/images',
                                 data='{"url":"https://www.google"}',
                                 headers={'content-type': 'text/plain'})
        assert response.status_code == 400 and "Invalid url" in response.text
        # Correct request
        response = requests.post('http://flask_app:5000/get/images',
                                 data='{"url":"https://www.google.com"}',
                                 headers={'content-type': 'text/plain'})
        assert response.status_code == 201 and re.match('{"id":[0-9]+}\n', response.text)
        data = json.loads(response.text)
        images_id = data["id"]


def test_download_text():
    with app.app_context():
        # Non string ID
        response = requests.get(f'http://flask_app:5000/download/text/string')
        assert response.status_code == 404 and response.text == "Invalid ID"
        # ID doesn't exist
        response = requests.get(f'http://flask_app:5000/download/text/-1')
        assert response.status_code == 404 and response.text == "Invalid ID"
        # Correct request
        response = requests.get(f'http://flask_app:5000/download/text/{text_id}')
        assert response.status_code == 200 and f'"file":"./Text/{text_id}.txt"' in response.text
        # Check if created file
        assert os.path.isfile(f"/usr/src/app/Text/{text_id}.txt")
        with open(f"/usr/src/app/Text/{text_id}.txt", "r") as file:
            content = file.readlines()
        # Check if text is saved
        assert "Gmail" in content[0]
        # Delete file
        os.remove(f"/usr/src/app/Text/{text_id}.txt")


def test_download_iamges():
    with app.app_context():
        # Non string ID
        response = requests.get(f'http://flask_app:5000/download/images/string')
        assert response.status_code == 404 and response.text == "Invalid ID"
        # ID doesn't exist
        response = requests.get(f'http://flask_app:5000/download/images/-1')
        assert response.status_code == 404 and response.text == "Invalid ID"
        # Correct request
        response = requests.get(f'http://flask_app:5000/download/images/{images_id}')
        assert response.status_code == 200
        # Check if images are saved
        data = json.loads(response.text)
        for file in data["files"]:
            file = file[1:]
            assert os.path.isfile(f"/usr/src/app{file}")
        # Delete files
        for file in data["files"]:
            file = file[1:]
            os.remove(f"/usr/src/app{file}")

