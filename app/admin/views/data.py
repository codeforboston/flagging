import io

import pandas as pd
from flask import Response
from flask import abort
from flask import redirect
from flask import request
from flask import send_file
from flask import url_for
from flask import current_app
from flask_admin import expose
from sqlalchemy.exc import ProgrammingError
from werkzeug.exceptions import HTTPException

from app.admin.base import BaseView
from app.data.celery import celery_app
from app.data.celery import live_hobolink_data_task
from app.data.celery import live_usgs_data_task
from app.data.celery import combine_data_task
from app.data.celery import prediction_task
from app.data.celery import update_db_task
from app.data.database import execute_sql
from app.data.database import get_current_time
from app.data.globals import file_cache


def send_csv_attachment_of_dataframe(
        df: pd.DataFrame,
        filename: str,
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
        filename: (str) Name of csv file to send. Be sure to include the file
                  extension here!
        date_prefix: (bool) If true, add today's date.

    Returns:
        Flask Response object with an attachment of the CSV.
    """

    # Set the file name:
    if date_prefix:
        now = get_current_time()
        todays_date = now.strftime('%Y-%m-%d')
        filename = f'{todays_date}-{filename}'

    # Flask can only return byte streams as file attachments.
    # As a warning, this is "leaky." The file_cache attempts to resolve the
    # leakiness issue by periodically closing and garbage collecting the file
    # streams.
    bytesio = io.BytesIO()
    file_cache.append(bytesio)

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
        attachment_filename=filename,
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
        'boathouse',
        'override_history'
    ]

    @expose('/')
    def index(self):
        download_style = \
            'src' if current_app.config['USE_CELERY'] else 'src_sync'
        return self.render(
            'admin/download.html',
            download_style=download_style
        )

    @expose('/csv/src/<sql_table_name>')
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
            filename=f'{sql_table_name}.csv'
        )

    @expose('/csv/src/hobolink_source')
    def source_hobolink(self):
        async_result = live_hobolink_data_task \
            .s(export_name='code_for_boston_export_90d').delay()
        return redirect(url_for(
            'admin_downloadview.csv_wait',
            task_id=async_result.id,
            data_source='hobolink'
        ))

    @expose('/csv/src/usgs_source')
    def source_usgs(self):
        async_result = live_usgs_data_task.s(days_ago=90).delay()
        return redirect(url_for(
            'admin_downloadview.csv_wait',
            task_id=async_result.id,
            data_source='usgs'
        ))

    @expose('/csv/src/processed_data_source')
    def source_combine_data(self):
        async_result = combine_data_task.s(
            export_name='code_for_boston_export_90d',
            days_ago=90).delay()
        return redirect(url_for(
            'admin_downloadview.csv_wait',
            task_id=async_result.id,
            data_source='combined'
        ))

    @expose('/csv/src/prediction_source')
    def source_prediction(self):
        async_result = prediction_task.s(
            export_name='code_for_boston_export_90d',
            days_ago=90).delay()
        return redirect(url_for(
            'admin_downloadview.csv_wait',
            task_id=async_result.id,
            data_source='prediction'
        ))

    @expose('/csv/wait')
    def csv_wait(self):
        task_id = request.args.get('task_id')
        data_source = request.args.get('data_source')
        return self.render(
            'admin/wait-for-task.html',
            task_id=task_id,
            status_url=url_for(
                'admin_downloadview.csv_status',
                task_id=task_id
            ),
            callback_url=url_for(
                'admin_downloadview.csv_download',
                data_source=data_source,
                task_id=task_id
            )
        )

    @expose('/csv/status')
    def csv_status(self):
        task_id = request.args.get('task_id')
        task = celery_app.AsyncResult(task_id)
        return {'status': task.status}, 202

    @expose('/csv/download')
    def csv_download(self):
        task_id = request.args.get('task_id')
        data_source = request.args.get('data_source')
        task = celery_app.AsyncResult(task_id)
        data = task.result
        if data is None:
            return {'status': task.status}, 202
        return send_csv_attachment_of_dataframe(
            df=pd.DataFrame(data),
            filename=f'{data_source}.csv'
        )

    # ---
    # The below views are used when USE_CELERY is turned off.

    @expose('/csv/src_sync/hobolink_source')
    def sync_source_hobolink(self):
        df = live_hobolink_data_task.run('code_for_boston_export_90d')
        return send_csv_attachment_of_dataframe(
            df=pd.DataFrame(df),
            filename='hobolink_source.csv'
        )

    @expose('/csv/src_sync/usgs_source')
    def sync_source_usgs(self):
        df = live_usgs_data_task.run(days_ago=90)
        return send_csv_attachment_of_dataframe(
            df=pd.DataFrame(df),
            filename='usgs_source.csv'
        )

    @expose('/csv/src_sync/processed_data_source')
    def sync_source_combine_data(self):
        df = combine_data_task.run(
            days_ago=90,
            export_name='code_for_boston_export_90d'
        )
        return send_csv_attachment_of_dataframe(
            df=pd.DataFrame(df),
            filename='model_processed_data.csv'
        )

    @expose('/csv/src_sync/prediction_source')
    def sync_source_prediction(self):
        df = prediction_task.run(
            days_ago=90,
            export_name='code_for_boston_export_90d'
        )
        return send_csv_attachment_of_dataframe(
            df=pd.DataFrame(df),
            filename='prediction_source.csv'
        )


class DatabaseView(BaseView):
    """Exposes an "update database" button to the user."""

    @expose('/')
    def index(self):
        return self.render('admin/update.html')

    @expose('/update-db')
    def update_db(self):
        """When this function is called, the database updates. This function is
        designed to be available in the app during runtime, and is protected by
        BasicAuth so that only administrators can run it.
        """
        async_result = update_db_task.delay()
        return redirect(url_for(
            'admin_databaseview.wait',
            task_id=async_result.id
        ))

    @expose('/wait')
    def wait(self):
        task_id = request.args.get('task_id')
        return self.render(
            'admin/wait-for-task.html',
            task_id=task_id,
            status_url=url_for(
                'admin_databaseview.check_status',
                task_id=task_id
            )
        )

    @expose('/check-status')
    def check_status(self):
        """Check the status of a pipeline task."""
        task_id = request.args.get('task_id')
        task = celery_app.AsyncResult(task_id)
        return {'status': task.status}
