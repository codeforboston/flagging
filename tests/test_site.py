import pytest


@pytest.mark.parametrize(
    'page, result',
    [
        ('/', 200),
        ('/output_model', 200)
    ]
)
def test_page(client, page, result):
    """Test that pages render without errors."""
    assert client.get(page).status_code == result
