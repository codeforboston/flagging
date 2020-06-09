import pytest
from flask import g
from flask import session

'''

Test that viewing the page renders without template errors
'''
@pytest.mark.parametrize('page, result',
                         [
                             ("/", 200),
                             ("/output_model", 200)
                         ]
                         )
def test_page(client, app, page, result):
    '''
    test that viewing the page renders without template errors
    '''
    assert client.get(page).status_code == result

