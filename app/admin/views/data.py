import io

import pandas as pd
from flask import Response, send_file, abort, url_for
from flask_admin import expose
from sqlalchemy.exc import ProgrammingError
from werkzeug.exceptions import HTTPException

from app.admin.base import BaseView
from app.data.database import get_current_time
from app.data.database import execute_sql
from app.data.database import update_db
from app.data.processing.hobolink import get_live_hobolink_data
from app.data.processing.usgs import get_live_usgs_data
from app.data.processing.predictive_models import process_data
from app.data.processing.predictive_models import all_models


def send_csv_attachment_of_dataframe(
        df: pd.DataFrame,
        file_name: str,
        date_prefix: bool = True
) -> Response:
    """Turn a Pandas DataFrame into a response object that sends a CSV
    attachment. This is used to download some of our tables from the database
    (especially useful for tables we don't have SQLAlchemy for), and also for
    DataFrames we build live.

    I think there is a strong possibility that this function causes a memory
    leak because it doesn't handle the byte stream in a great way. For our
    extremely small and infrequent use case, this is fine. But do keep in mind
    that this doesn't scale.

    Args:
        df: (pd.DataFrame) DataFrame to turn into a CSV.
        file_name: (str) Name of csv file to send. Be sure to include the file
                   extension here!
        date_prefix: (bool) If true, add today's date.

    Returns:
        Flask Response object with an attachment of the CSV.
    """

    # Set the file name:
    if date_prefix:
        now = get_current_time()
        todays_date = now.strftime('%Y_%m_%d')
        file_name = f'{todays_date}-{file_name}'

    # Flask can only return byte streams as file attachments.
    # As a warning, this is "leaky." Handle with care!
    bytesio = io.BytesIO()

    # Write csv to stream, then encode it.
    with io.StringIO() as strio:
        df.to_csv(strio, index=False)
        b = strio.getvalue().encode('utf-8')
        bytesio.write(b)

    # It's safest to set the stream position at the start
    bytesio.seek(0)

    return send_file(
        bytesio,
        as_attachment=True,
        attachment_filename=file_name,
        mimetype='text/csv'
    )


class DownloadView(BaseView):
    """This admin view renders a landing page for downloading tables either from
    the Postgres Database or live from the external APIs. The lives downloads
    are handy because they get around limitations of the Heroku free tier.
    """

    TABLES = [
        'hobolink',
        'usgs',
        'processed_data',
        'prediction',
        'boathouses',
        'override_history'
    ]

    @expose('/')
    def index(self):
        return self.render('admin/download.html')

    @expose('/csv/<sql_table_name>')
    def download_from_db(self, sql_table_name: str):
        # Do not ever delete the following two lines!
        # This is necessary for security.
        if sql_table_name not in self.TABLES:
            raise abort(404)

        # WARNING:
        # Be careful when parameterizing queries like how we do it below.
        # The reason it's OK in this case is because users don't touch it.
        # However it is dangerous to do this in some other contexts.
        query = f'''SELECT * FROM {sql_table_name}'''
        try:
            df = execute_sql(query)
        except ProgrammingError:
            raise HTTPException(
                'Invalid SQL.',
                Response(
                    f'<b>Invalid SQL query:</b> <samp>{query}</samp>',
                    status=500
                )
            )

        return send_csv_attachment_of_dataframe(
            df=df,
            file_name=f'{sql_table_name}.csv'
        )

    @expose('/csv/hobolink_source')
    def source_hobolink(self):
        df_hobolink = get_live_hobolink_data('code_for_boston_export_90d')

        return send_csv_attachment_of_dataframe(
            df=df_hobolink,
            file_name='hobolink_source.csv'
        )

    @expose('/csv/usgs_source')
    def source_usgs(self):
        df_usgs = get_live_usgs_data(days_ago=90)

        return send_csv_attachment_of_dataframe(
            df=df_usgs,
            file_name='usgs_source.csv'
        )

    @expose('/csv/processed_data_source')
    def source_processed_data(self):
        df_usgs = get_live_usgs_data(days_ago=90)
        df_hobolink = get_live_hobolink_data('code_for_boston_export_90d')
        df = process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)

        return send_csv_attachment_of_dataframe(
            df=df, file_name='model_processed_data.csv')

    @expose('/csv/prediction_source')
    def source_model_outputs(self):
        df_usgs = get_live_usgs_data(days_ago=90)
        df_hobolink = get_live_hobolink_data('code_for_boston_export_90d')
        df = process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)
        model_outs = all_models(df, rows=len(df))

        return send_csv_attachment_of_dataframe(
            df=model_outs,
            file_name='prediction_source.csv'
        )


class DatabaseView(BaseView):
    """Exposes an "update database" button to the user."""

    @expose('/')
    def index(self):
        return self.render('admin/update.html')

    @expose('/run-update')
    def update_db(self):
        """When this function is called, the database updates. This function is
        designed to be available in the app during runtime, and is protected by
        BasicAuth so that only administrators can run it.
        """
        update_db()

        # Notify the user that the update was successful, then redirect:
        return self.render('admin/redirect.html',
                           message='Database updated.',
                           redirect_to=url_for('admin.index'))
