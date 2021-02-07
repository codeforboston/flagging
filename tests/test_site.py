import pytest

from flagging_site.data import Boathouse


@pytest.mark.parametrize(
    ('page', 'result'),
    [
        ('/', 200),
        ('/about', 200),
        ('/model_outputs', 200),
        ('/flags', 200),
        ('/api', 200),
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


def test_override_on_home_page(client, db_session, cache):
    """Test to see that manual overrides show up properly on the home page. This
    test assumes that the flag for "Union Boat Club" starts off as blue and not
    overridden.

    This function also tests that the caching works. Basically, updating the
    database model by itself does not update the home page. It is also necessary
    for the cache to be cleared.
    """

    def _get_flag_count():
        res = client.get('/').data
        return {
            'blue': res.count(b'blue_flag.png'),
            'red': res.count(b'red_flag.png')
        }

    # First let's get the home page.
    flags1 = _get_flag_count()

    # Let's clear the cache and get the home page again.
    # Nothing should have changed because the database was not updated.

    cache.clear()
    flags2 = _get_flag_count()

    assert flags2['red'] == flags1['red']
    assert flags2['blue'] == flags1['blue']

    # Now update the entry in the database.

    db_session \
        .query(Boathouse) \
        .filter(Boathouse.boathouse == 'Union Boat Club') \
        .update({"overridden": True})
    db_session.commit()

    # Without clearing the cache, the page should be the exact same, even
    # though we updated the database on the backend.

    flags3 = _get_flag_count()

    assert flags3['red'] == flags1['red']
    assert flags3['blue'] == flags1['blue']

    # Now let's clear the cache. At long last, now the page should change
    # because both the model updated and the cache cleared.

    cache.clear()
    flags4 = _get_flag_count()

    assert flags4['red'] == flags1['red'] + 1
    assert flags4['blue'] == flags1['blue'] - 1
