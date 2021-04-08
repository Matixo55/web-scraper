import re
import importlib

import requests as req
from bs4 import BeautifulSoup
from celery import Celery
from flask import Flask, jsonify, render_template
from flask import request as flask_request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, exc


DATABASE_URI = importlib.import_module(".", "settings").DATABASE_URI
MAX_PAGE_SIZE = importlib.import_module(".", "settings").MAX_PAGE_SIZE
Request = importlib.import_module(".", "models").Request
RESPONSE = importlib.import_module(".", "models").list_model
Status = importlib.import_module(".", "models").Status

app = Flask(__name__)
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['DEBUG'] = True
celery = Celery(app.name, broker='redis://localhost:6379/0')

engine = create_engine(DATABASE_URI)

class DataAccessor:
    def __init__(self, session: Session):
        self._session = session

    def cancel_request(self, id: int) -> None:
        try:
            self._session.query(Request)\
                .filter(Request.id == id)\
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
            id = request.id
            self._session.commit()
        except BaseException as ex:
            self._session.rollback()
            raise ex
            return -1
        finally:
            self._session.close()
            return id

    def finish_images_request(self, urls: list[str], id: int) -> None:
        try:
            self._session.query(Request)\
                .filter(Request.id == id)\
                .update({Request.images: urls, Request.status: Status.done})
            self._session.commit()
        except BaseException as ex:
            self._session.rollback()
            raise ex
        finally:
            self._session.close()

    def finish_text_request(self, text: str, id: int) -> None:
        try:
            self._session.query(Request) \
                .filter(Request.id == id) \
                .update({Request.website_text: text, Request.status: Status.done})
            self._session.commit()
        except BaseException as ex:
            self._session.rollback()
            raise ex
        finally:
            self._session.close()

    def find_by_id(self, id: int) -> Request or None:
        try:
            result = self._session.query(Request)\
                         .filter(Request.id == id).one()
            return result
        except exc.NoResultFound:
            return None

    def get_entries(self, limit: int, page: int) -> list[Request] or None:
        try:
            query = self._session.query(Request).limit(limit).offset((page - 1) * limit).all()
            print(limit, page, query, flush=True)
            query.sort(key=lambda entry: entry.id)
        except BaseException as ex:
            raise ex
            return None
        finally:
            self._session.close()
            print(query, type(query), 1, flush = True)
            return query

accessor = DataAccessor(Session(engine))

def create_request_object() -> (str, int, bool):

    body = flask_request.get_json(force=True)
    url = body["url"]

    if is_url_valid(url):
        request = Request(url=url, status=Status.preparing, website_text="", images=[])
        if (id := accessor.create_request(request)) != -1:
            return url, id, True
        else:
            return url, 0, False

    else:
        return url, 0, False

def is_url_valid(url: str) -> bool:

    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def get_entry(id: int) -> object or None:

    if not id.isnumeric():
        return None

    return accessor.find_by_id(id)

@app.route("/", methods=["GET"])
def menu():
    return "<h1>Server is online</h1>", 200


@app.route("/download/images/<id>", methods=["GET"])
def download_images(id: int):

    if (request := get_entry(id)) is None:
        return "Invalid ID", 404

    elif request.status == Status.done:
        number = 0
        urls = []

        for url in request.images:
            try:
                response = req.get(url)
                extension = url.split(".")[-1]
                extensions = ["png", "jpg", "jpeg", "raw", "gif"]
                if extension.lower() not in extensions:
                    extension = "png"
                name = f"./Images/{request.id}-{number}.{extension}"
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
def download_text(id: int):

    if (request := get_entry(id)) is None:
        return "Invalid ID", 404

    elif request.status == Status.done:
        name = f"./Text/{request.id}.txt"
        with open(name, "w") as file:
            file.write(request.website_text)
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
            accessor.cancel_request(id)
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
            accessor.cancel_request(id)
            return "Invalid url or couldn't connect", 400
        get_text(page, id)
        return jsonify({"id": id}), 201

    else:
        return "Invalid url", 400


@app.route("/list/", methods=["GET", "POST"])
def show_entries():

    response = RESPONSE

    if flask_request.method == "GET":
        return render_template('menu.html')

    elif flask_request.method == "POST":
        page = flask_request.form["page"]
        limit = flask_request.form["limit"]
        style = '"text-align: center; vertical-align: middle;"'
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

        status_converter = {Status.done: "Done", Status.preparing: "In progress", Status.invalid: "Error while processing"}
        query = accessor.get_entries(limit, page)

        if query is not None:
            for result in query:

                response += '<tr>' \
                            f'<td style={style}>{result.id}</td>' \
                            f'<td style={style}>{result.url}</td>' \
                            f'<td style={style}>{status_converter[result.status]}</td>' \
                            '</tr>'
            response += "</table>"
        return response


@celery.task
def get_images(page: "requests.models.Response", url: str, id: int):
    html = page.content
    soup = BeautifulSoup(html, 'html.parser')
    img_tags = soup.find_all('img')
    if url[-1] != "/":
        url += "/"
    urls = [url + img['src'] for img in img_tags]
    accessor.finish_images_request(urls, id)


@celery.task
def get_text(page: "requests.models.Response", id: int):
    html = page.content
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    accessor.finish_text_request(text, id)


if __name__ == "__main__":
    app.run()
