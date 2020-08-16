import pytest


@pytest.mark.parametrize(
    ('page', 'result'),
    [
        ('/', 200),
        ('/about', 200),
        ('/output_model', 200),
        ('/api/', 200),
        ('/api/v1/model', 200),
        ('/api/v1/model?reach=4&hours=20', 200)
    ]
)
def test_pages(client, page, result):
    """Test that pages render without errors."""
    assert client.get(page).status_code == result
