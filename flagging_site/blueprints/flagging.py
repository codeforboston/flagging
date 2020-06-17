import pandas as pd
from flask import Blueprint
from flask import render_template
from flagging_site.data.hobolink import get_hobolink_data
from flagging_site.data.usgs import get_usgs_data
from flagging_site.data.model import process_data
from flagging_site.data.model import reach_2_model
from flagging_site.data.model import reach_3_model
from flagging_site.data.model import reach_4_model
from flagging_site.data.model import reach_5_model

bp = Blueprint('flagging', __name__)

def stylize_model_output(df: pd.DataFrame):
    """ 
    This function function stylizes the dataframe that we will output for our 
    web page
    
    Args: 
        data frame 
        
    Returns: 
        Dataframe with properties set for color, border-style, flag colors, and 
        border-width
    """
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
    """
    Retrieves data from hobolink and usgs and processes data, then displays data 
    on `index_model.html`     

    returns: render model on index.html
    """
    df_hobolink = get_hobolink_data('code_for_boston_export_21d')
    df_usgs = get_usgs_data()
    df = process_data(df_hobolink, df_usgs)
    flags = {
        2: reach_2_model(df, rows=1)['r2_safe'].iloc[0],
        3: reach_3_model(df, rows=1)['r3_safe'].iloc[0],
        4: reach_4_model(df, rows=1)['r4_safe'].iloc[0],
        5: reach_5_model(df, rows=1)['r5_safe'].iloc[0]
    }
    return render_template('index.html', flags=flags)


@bp.route('/output_model')
def output_model() -> str:
    """
    Retrieves data from hobolink and usgs and processes data and then 
    displays data on 'output_model.html'
    
    args: no argument
    
    returns: render model on output_model.html
    """
    df_hobolink = get_hobolink_data('code_for_boston_export_21d')
    df_usgs = get_usgs_data()
    df = process_data(df_hobolink, df_usgs)
    table_html = '<br /><br />'.join(map(stylize_model_output, [
        reach_2_model(df),
        reach_3_model(df),
        reach_4_model(df),
        reach_5_model(df)
    ]))
    return render_template('output_model.html', tables=table_html)
