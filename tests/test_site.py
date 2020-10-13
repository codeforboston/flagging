import pytest


@pytest.mark.parametrize(
    ('page', 'result'),
    [
        ('/', 200),
        ('/about', 200),
        ('/output_model', 200),
        ('/flags', 200),
        ('/api/', 200),
        ('/api/docs', 200),
        ('/api/v1/model', 200),
        ('/api/v1/model?reach=4&hours=20', 200),
        ('/api/v1/boathouses', 200),
        ('/api/v1/model_input_data', 200),
    ]
)
def test_pages(client, page, result):
    """Test that pages render without errors. This test is very broad; the
    purpose of this test is to capture any errors that would cause a routing
    function to fail, such as a 404 HTTP error or a 500 HTTP error.

    Although this test is not very specific with what it tests (e.g. a page can
    render without any status code errors but still render incorrectly), it is
    still a good stop-gap.
    """
    assert client.get(page).status_code == result
