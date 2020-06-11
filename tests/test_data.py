#first changes from edwin

# tests/test_site.py

import pytest
from flask import g
from flask import session


def test_home_page(data):
    # test that viewing the data renders the data between the values of 0 and 1
    assert data >= 0 and data <= 1


def test_output_model(data):
    # test that viewing the data renders the data between the values of 0 and 1
    assert data >= 0 and data <= 1
