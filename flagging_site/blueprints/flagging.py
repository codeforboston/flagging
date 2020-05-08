from flask import Blueprint
from flagging_site.data.hobolink import get_hobolink_data

bp = Blueprint('flagging', __name__)


@bp.route('/')
def index() -> str:
    return 'Hello, world!'


@bp.route('/test_hobolink')
def test_hobolink() -> str:
    return get_hobolink_data().to_html()
