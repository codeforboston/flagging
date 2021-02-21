from typing import Any
from typing import Dict
from typing import List

from flask import redirect
from flask_admin.actions import action
from flask_admin.contrib.sqla import tools

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import Session

from ..admin import ModelView
from .database import db
from .predictive_models import latest_model_outputs


class Boathouse(db.Model):
    __tablename__ = 'boathouses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    boathouse = db.Column(db.String(255))
    reach = db.Column(db.Integer, unique=False)
    latitude = db.Column(db.Numeric, unique=False)
    longitude = db.Column(db.Numeric, unique=False)
    overridden = db.Column(db.Boolean, unique=False, default=False)
    reason = db.Column(db.String(255), unique=False)

    def to_dict(self) -> Dict[str, Any]:
        """Represents a Boathouse object as a dict."""
        return {
            k: getattr(self, k)
            for k in self.__table__.columns.keys()
        }

    @classmethod
    def all_boathouses_dict(cls) -> List[Dict[str, Any]]:
        """Descriptive data about the boathouses, presented as a list of dicts.
        This can be queried via the REST API.

        You can think of this function as performing the following query:

            SELECT reach, boathouse, latitude, longitude, overriden, reason
            FROM boathouses
            ORDER BY reach, boathouse
        """
        res = (
            cls.query
            .order_by(
                cls.reach,
                cls.boathouse
            )
            .all()
        )

        df = latest_model_outputs()

        def _reach_is_safe(r: int) -> bool:
            return df.loc[df['reach'] == r, 'safe'].iloc[0]

        return_data = []
        for i in res:
            # remove the "id" field.
            bh = i.to_dict()
            bh['safe'] = \
                bool(_reach_is_safe(bh['reach']) and (not bh['overridden']))
            bh.pop('id')
            return_data.append(bh)
        return return_data

    @classmethod
    def boathouse_names_by_reach(cls) -> Dict[int, List[str]]:
        """Returns a dict with the following format:

          - key = reach number
          - value = list of boathouses in that reach

        The code is a bit hard to read, but it is basically performing the
        following SQL query before turning it into a dict:

            SELECT
              reach,
              array_agg(boathouse ORDER BY boathouse ASC) AS boathouse_array
            FROM boathouses
            GROUP BY reach
            ORDER BY reach
        """
        res = (
            db.session.query(
                cls.reach,
                func.array_agg(
                    aggregate_order_by(
                        cls.boathouse,
                        cls.boathouse.asc()
                    )
                )
            )
            .group_by(cls.reach)
            .order_by(cls.reach)
            .all()
        )
        return {i[0]: i[1] for i in res}

    @classmethod
    def all_flags(cls) -> Dict[str, bool]:
        data = cls.all_boathouses_dict()
        return {bh['boathouse']: bh['safe'] for bh in data}


class _BaseBoathouseView(ModelView):
    # <span class="fa fa-circle-o glyphicon glyphicon-minus-sign icon-minus-sign"></span>
    list_template = 'admin/list_boathouses.html'
    column_filters = ('reach',)
    column_default_sort = [('reach', False), ('boathouse', False)]


class BoathouseModelView(_BaseBoathouseView):
    def __init__(self, session: Session):
        super().__init__(
            Boathouse,
            session,
            ignore_columns=['id', 'overridden', 'reach', 'reason'],
            endpoint='boathouses',
            name='Boathouses'
        )


class ManualOverridesModelView(_BaseBoathouseView):
    can_delete = False
    can_create = False

    form_choices = {
        'reason': [
            ('cyanobacteria', 'Cyanobacteria'),
            ('sewage', 'Sewage'),
            ('other', 'Other'),
        ]
    }

    def __init__(self, session: Session):
        super().__init__(
            Boathouse,
            session,
            endpoint='manual_overrides',
            ignore_columns=['id', 'latitude', 'longitude'],
            name='Manual Overrides'
        )
        self.form_columns = ['overridden', 'reason']

    def _flip_all_overrides(self, ids, change_flags_to: bool):
        query = tools.get_query_for_ids(self.get_query(), self.model, ids)
        query.update({'overridden': change_flags_to}, synchronize_session='fetch')
        db.session.commit()
        return redirect(self.url)

    @action('Override',
            'Override',
            'Are you sure you want to override the selected locations?')
    def action_override_selected(self, ids):
        return self._flip_all_overrides(ids, change_flags_to=True)

    @action('Remove Override',
            'Remove Override',
            'Are you sure you want to remove the override for the selected locations?')
    def action_remove_override_selected(self, ids):
        return self._flip_all_overrides(ids, change_flags_to=False)

    def on_form_prefill(self, form, *args, **kwargs):
        form.boathouse.render_kw = {'readonly': True}
        form.reach.render_kw = {'readonly': True}
        super().on_form_prefill(form, *args, **kwargs)
