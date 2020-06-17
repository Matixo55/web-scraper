import re
import importlib

import requests as req
from bs4 import BeautifulSoup
from celery import Celery
from flask import Flask, jsonify
from flask import request as flask_request
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, exc

Requests = importlib.import_module(".", "models").Requests
Status = importlib.import_module(".", "models").Status
DATABASE_URI = importlib.import_module(".", "settings").DATABASE_URI


app = Flask(__name__)
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['DEBUG'] = True
celery = Celery(app.name, broker='redis://localhost:6379/0')


engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)


def create_request_object():
    body = flask_request.get_json(force=True)
    url = body["url"]
    if is_url_valid(url):
        sess = Session()
        __request = Requests(url=url, status=Status.preparing, website_text="", images=[])
        sess.add(__request)
        sess.flush()
        print(__request.id)
        id = __request.id
        sess.commit()
        return url, id, True
    else:
        return url, None, False


def finish_images_request(urls, target_id):
    session = Session()
    session.query(Requests) \
        .filter(Requests.id == target_id) \
        .update({Requests.images: urls, Requests.status: Status.done})
    session.commit()


def finish_text_request(text, target_id):
    session = Session()
    session.query(Requests) \
        .filter(Requests.id == target_id) \
        .update({Requests.website_text: text, Requests.status: Status.done})
    session.commit()


def is_url_valid(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None


def validate_id(id):
    if not id.isnumeric():
        return None, False
    session = Session()
    try:
        object = session.query(Requests) \
            .filter(Requests.id == id).one()
        return object, True
    except exc.NoResultFound:
        return None, False


@app.route("/", methods=["GET"])
def menu():
    return "<h1>Server is online</h1>", 200


@app.route("/download/images/<id>", methods=["GET"])
def download_images(id):
    object, valid = validate_id(id)
    if not valid:
        return "Invalid ID", 404
    if object.status == Status.done:
        number = 0
        urls = []
        for url in object.images:
            try:
                response = req.get(url)
                extension = url.split(".")[-1]
                extensions = ["png", "jpg", "jpeg", "raw", "gif"]
                if extension.lower() not in extensions:
                    extension = "png"
                name = f"./Images/{object.id}-{number}.{extension}"
                with open(name, "wb") as file:
                    file.write(response.content)
                number += 1
                urls.append(name)
            except req.exceptions.ConnectionError:
                urls.append(f"Unable to download {url}")
        return jsonify({"files": urls}), 200
    else:
        return "Request in progress, try later", 403


@app.route("/download/text/<id>", methods=["GET"])
def download_text(id):
    object, valid = validate_id(id)
    if not valid:
        return "Invalid ID", 404
    if object.status == Status.done:
        name = f"./Text/{object.id}.txt"
        with open(name, "w") as file:
            file.write(object.website_text)
        return jsonify({"file": name}), 200
    else:
        return "Request in progress, try later", 403


@app.route("/get/images/", methods=["POST"])
def create_image_request():
    url, id, accepted = create_request_object()
    if accepted:
        try:
            page = req.get(url)
        except req.exceptions.ConnectionError:
            return "Invalid url or couldn't connect", 400
        get_images(page, url, id)
        return jsonify({"id": id}), 201
    else:
        return "Invalid url", 400


@app.route("/get/text/", methods=["POST"])
def create_text_request():
    url, id, accepted = create_request_object()
    if accepted:
        try:
            page = req.get(url)
        except req.exceptions.ConnectionError:
            return "Invalid url or couldn't connect", 400
        get_text(page, id)
        return jsonify({"id": id}), 201
    else:
        return "Invalid url", 400


@celery.task
def get_images(page, url, request_id):
    html = page.content
    soup = BeautifulSoup(html, 'html.parser')
    img_tags = soup.find_all('img')
    if url[-1] != "/":
        url += "/"
    urls = [url + img['src'] for img in img_tags]
    finish_images_request(urls, request_id)


@celery.task
def get_text(page, request_id):
    html = page.content
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    finish_text_request(text, request_id)


if __name__ == "__main__":
    app.run()
