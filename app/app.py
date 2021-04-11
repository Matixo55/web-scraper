import importlib
import os
import re
from typing import List

import requests as req
from bs4 import BeautifulSoup
from celery import Celery
from flask import Flask, jsonify, render_template
from flask import request as flask_request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, exc

DATABASE_URI = importlib.import_module(".", "settings").DATABASE_URI
flask_debug = importlib.import_module(".", "settings").enable_flask_debug
MAX_PAGE_SIZE = importlib.import_module(".", "settings").MAX_PAGE_SIZE
Request = importlib.import_module(".", "models").Request
RESPONSE = importlib.import_module(".", "models").list_model
Status = importlib.import_module(".", "models").Status

app = Flask(__name__)
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['DEBUG'] = flask_debug
celery = Celery(app.name, broker='redis://localhost:6379/0')

engine = create_engine(DATABASE_URI)


class DataAccessor:
    def __init__(self, session: Session):
        self._session = session

    def cancel_request(self, request_id: int) -> None:
        try:
            self._session.query(Request) \
                .filter(Request.id == request_id) \
                .update({Request.status: Status.invalid})
            self._session.commit()
        except BaseException as ex:
            self._session.rollback()
            raise ex
        finally:
            self._session.close()

    def create_request(self, request: Request) -> int:
        try:
            self._session.add(request)
            self._session.flush()
            request_id = request.id
            self._session.commit()
        except BaseException as ex:
            self._session.rollback()
            request_id = -1
            raise ex
        finally:
            self._session.close()
            return request_id

    def finish_images_request(self, urls: List[str], request_id: int) -> None:
        try:
            self._session.query(Request) \
                .filter(Request.id == request_id) \
                .update({Request.images: urls, Request.status: Status.done})
            self._session.commit()
        except BaseException as ex:
            self._session.rollback()
            raise ex
        finally:
            self._session.close()

    def finish_text_request(self, text: str, request_id: int) -> None:
        try:
            self._session.query(Request) \
                .filter(Request.id == request_id) \
                .update({Request.website_text: text, Request.status: Status.done})
            self._session.commit()
        except BaseException as ex:
            self._session.rollback()
            raise ex
        finally:
            self._session.close()

    def find_by_id(self, request_id: int) -> Request or None:
        try:
            result = self._session.query(Request) \
                .filter(Request.id == request_id).one()
            return result
        except exc.NoResultFound:
            return None

    def get_entries(self, limit: int, page: int) -> List[Request] or None:
        try:
            query = self._session.query(Request).limit(limit).offset((page - 1) * limit).all()
            query.sort(key=lambda entry: entry.id)
        except BaseException as ex:
            query = None
            raise ex
        finally:
            self._session.close()
            return query


accessor = DataAccessor(Session(engine))


def create_response(query: List[Request]) -> str:

    response = RESPONSE
    style = '"text-align: center; vertical-align: middle;"'
    status_converter = {
        Status.done: "Done",
        Status.preparing: "In progress",
        Status.invalid: "Error while processing"
                        }
    for result in query:
        response += '<tr>' \
                    f'<td style={style}>{result.id}</td>' \
                    f'<td style={style}>{result.url}</td>' \
                    f'<td style={style}>{status_converter[result.status]}</td>' \
                    '</tr>'
    response += "</table>"

    return response


def create_request_object() -> (str, int, bool):
    body = flask_request.get_json(force=True)
    url = body["url"]

    if is_url_valid(url):
        request = Request(url=url, status=Status.preparing, website_text="", images=[])
        if (request_id := accessor.create_request(request)) != -1:
            return url, request_id, True
        else:
            return url, 0, False

    else:
        return url, 0, False


def download_images(request_id: int, url_list: List[str]) -> List[str]:
    urls = []
    number = 0

    for url in url_list:
        try:
            response = req.get(url)
            extension = url.split(".")[-1]
            extensions = ["png", "jpg", "jpeg", "raw", "gif"]
            if extension.lower() not in extensions:
                extension = "png"
            path = f"./Images/{request_id}-{number}.{extension}"
            with open(path, "wb") as file:
                file.write(response.content)
            number += 1
            urls.append(path)

        except req.exceptions.ConnectionError:
            urls.append(f"Unable to download {url}")

    return urls


def exists_directory(directory: str) -> bool:
    if not os.path.isdir(directory):
        try:
            os.mkdir(directory)
        except OSError:
            return False
        finally:
            return True


def is_url_valid(url: str) -> bool:
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None


def get_entry(request_id: str) -> Request or None:
    if not request_id.isnumeric():
        return None

    return accessor.find_by_id(int(request_id))


@app.route("/", methods=["GET"])
def menu():
    return "<h1>Server is online</h1>", 200


@app.route("/download/images/<request_id>", methods=["GET"])
def start_image_download(request_id):
    if (request := get_entry(request_id)) is None:
        return "Invalid or not existing ID", 404

    elif request.status == Status.done:

        if not exists_directory("./Images"):
            return "Unable to create ./Images directory", 450

        urls = download_images(request.id, request.images)
        return jsonify({"files": urls}), 200

    else:
        return "Request in progress, try later", 403


@app.route("/download/text/<request_id>", methods=["GET"])
def download_text(request_id):
    if (request := get_entry(request_id)) is None:
        return "Invalid or not existing ID", 404

    elif request.status == Status.done:

        if not exists_directory("./Text"):
            return "Unable to create ./Text directory", 450

        name = f"./Text/{request.id}.txt"
        with open(name, "w") as file:
            file.write(request.website_text)
        return jsonify({"file": name}), 200

    else:
        return "Request in progress, try later", 403


@app.route("/get/images/", methods=["POST"])
def create_image_request():
    url, request_id, accepted = create_request_object()

    if accepted:
        try:
            page = req.get(url)
        except req.exceptions.ConnectionError:
            accessor.cancel_request(request_id)
            return "Invalid url or couldn't connect", 400
        get_images(page, url, request_id)
        return jsonify({"id": request_id}), 201

    else:
        return "Invalid url", 400


@app.route("/get/text/", methods=["POST"])
def create_text_request():
    url, request_id, accepted = create_request_object()

    if accepted:
        try:
            page = req.get(url)
        except req.exceptions.ConnectionError:
            accessor.cancel_request(request_id)
            return "Invalid url or couldn't connect", 400
        get_text(page, request_id)
        return jsonify({"id": request_id}), 201

    else:
        return "Invalid url", 400


@app.route("/list/", methods=["GET", "POST"])
def show_entries():

    if flask_request.method == "GET":
        return render_template('menu.html')

    elif flask_request.method == "POST":
        page = flask_request.form["page"]
        limit = flask_request.form["limit"]
        if page is None or limit is None:
            return render_template('menu.html')

        if not page.isnumeric():
            return f"Bad Request - invalid page: {page} is not a correct number", 404
        if not limit.isnumeric():
            return f"Bad Request - invalid limit: {limit} is not a correct number", 404

        page = int(page)
        limit = int(limit)
        if page <= 0:
            return "Bad Request - invalid page: <= 0", 400
        if limit <= 0:
            return "Bad Request - invalid limit: <= 0", 400
        if limit > MAX_PAGE_SIZE:
            return f"Bad Request - limit bigger than {MAX_PAGE_SIZE}", 400

        query = accessor.get_entries(limit, page)

        if query is not None:
            return create_response(query)
        else:
            return RESPONSE


@celery.task
def get_images(page: "requests.models.Response", url: str, request_id: int):
    html = page.content
    soup = BeautifulSoup(html, 'html.parser')
    img_tags = soup.find_all('img')
    if url[-1] != "/":
        url += "/"
    urls = [url + img['src'] for img in img_tags]
    accessor.finish_images_request(urls, request_id)


@celery.task
def get_text(page: "requests.models.Response", request_id: int):
    html = page.content
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    accessor.finish_text_request(text, request_id)


if __name__ == "__main__":
    app.run()
