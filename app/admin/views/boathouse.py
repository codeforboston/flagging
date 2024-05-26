from flask import redirect
from flask_admin.actions import action
from flask_admin.contrib.sqla import tools
from sqlalchemy.orm import Session

from app.admin.base import ModelView
from app.data.database import db
from app.data.globals import cache
from app.data.models.boathouse import Boathouse


class _BaseBoathouseView(ModelView):
    list_template = 'admin/list_boathouses.html'
    column_filters = ('reach_id',)
    column_default_sort = [('reach_id', False), ('name', False)]


class BoathouseModelView(_BaseBoathouseView):
    def __init__(self, session: Session):
        super().__init__(
            Boathouse,
            session,
            ignore_columns=['id', 'overridden', 'reason'],
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
        self.form_columns = ['boathouse', 'reach', 'overridden', 'reason']

    def _flip_all_overrides(self, ids, change_flags_to: bool):
        query = tools.get_query_for_ids(self.get_query(), self.model, ids)
        query.update({'overridden': change_flags_to},
                     synchronize_session='fetch')
        db.session.commit()
        cache.clear()
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
        form.name.render_kw = {'readonly': True}
        form.reach_id.render_kw = {'readonly': True}
        super().on_form_prefill(form, *args, **kwargs)
