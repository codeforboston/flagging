import pytest
from flask import g
from flask import session

def test_home_page(client, app):
    # test that viewing the page renders without template errors
    assert client.get("/").status_code == 200

def test_output_model(client, app):
    # test that viewing the page renders without template errors
    assert client.get("/output_model").status_code == 200
