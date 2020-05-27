import pandas as pd
from flask import Blueprint
from flagging_site.data.hobolink import get_hobolink_data
from flagging_site.data.usgs import get_usgs_data
from flagging_site.data.model import (
    process_data, reach_2_model, reach_3_model, reach_4_model, reach_5_model
)

bp = Blueprint('flagging', __name__)


def stylize_model_output(df: pd.DataFrame):
    def color_flags(x):
        return 'color: blue' if x is True \
            else 'color: red' if x is False \
            else ''
    return (
        df
        .style
        .hide_index()
        .set_properties(**{
            'border-color': '#888888',
            'border-style': 'solid',
            'border-width': '1px'
        })
        .applymap(color_flags)
        .render()
    )


@bp.route('/')
def index() -> str:
    return 'Hello, world!'


@bp.route('/output_model')
def output_model() -> str:
    df_hobolink = get_hobolink_data('code_for_boston_export_21d')
    df_usgs = get_usgs_data()
    df = process_data(df_hobolink, df_usgs)
    return '<br /><br />'.join(map(stylize_model_output, [
        reach_2_model(df),
        reach_3_model(df),
        reach_4_model(df),
        reach_5_model(df)
    ]))
