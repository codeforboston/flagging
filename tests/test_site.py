#tests/test_site.py

#1 test_can_load_page ->
    # test all pages load properly
    # pytest mark param decorator
    # testing: '/'
    # testing: '/output_model'
#write function that has app as one of arguments
#flask
#test_auth
#use client to load pages within
#pass the fixture created, pass as argument (see: test directory)
import pytest
from flask import g
from flask import session

def test_home_page(client, app):
    # test that viewing the page renders without template errors
    assert client.get("/").status_code == 200

def test_output_model(client, app):
    # test that viewing the page renders without template errors
    assert client.get("/output_model").status_code == 200
