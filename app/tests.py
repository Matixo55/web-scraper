# import importlib
from .app import is_url_valid
#from .app import is_url_valid, Session, req, finish_pictures_request, finish_text_request
#from .models.Request import Requests

import pytest

# Test while having app running


def test_url():
    assert is_url_valid("www.noturl") is False
    assert is_url_valid("https://www.google.com/") is True


# def test_app():
#     html = req.get("http://127.0.0.1:5000/").content
#     assert html == b"<h1>Server is online</h1>"


# def test_download():
#     session = Session()
#     session.add(Requests(id=-1, url="test_url", status="in-progress", website_text="test", pictures=["url", "url"]))
#     session.commit()
#
#     html = req.get("http://127.0.0.1:5000/download-text/-2").content
#     assert html == b'{"error":"Incorrect ID"}\n'
#     html = req.get("http://127.0.0.1:5000/download-text/-1").content
#     assert html == b'{"status":"in-progress"}\n'
#     html = req.get("http://127.0.0.1:5000/download-pictures/-1").content
#     assert html == b'{"status":"in-progress"}\n'
#
#     session = Session()
#     request = session.query(Requests).filter(Requests.id == -1).one()
#     assert type(request.id) == int
#     assert type(request.url) == str
#     assert type(request.status) == str
#     assert type(request.website_text) == str
#     assert type(request.pictures) == list


# def test_finish_requests():
#
#     finish_text_request("text", -1)
#     session = Session()
#     request = session.query(Requests).filter(Requests.id == -1).one()
#     assert request.website_text == "text"
#
#     finish_pictures_request(["1", "2"], -1)
#
#     session = Session()
#     request = session.query(Requests).filter(Requests.id == -1).one()
#     assert request.pictures == ["1", "2"]
#
#     html = req.get("http://127.0.0.1:5000/download-text/-1").content
#     assert html == b'text'
#
#     session = Session()
#     to_delete = session.query(Requests).filter_by(id=-1).one()
#     session.delete(to_delete)
#     session.commit()
