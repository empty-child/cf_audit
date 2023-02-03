import csv
import time
from datetime import datetime
from .db import Stats
from io import StringIO
from flask import abort

def read_stats():
    csv_output = StringIO()

    keys = Stats._meta.fields.keys();

    new_keys = list(keys)
    new_keys.remove('id')

    writer = csv.DictWriter(csv_output, new_keys)
    writer.writeheader()
    results = Stats.select().dicts()

    for result in results:
        result.update({
            'already_existed' : 'true' if bool(result.get('Stats.already_existed')) else 'false',
            'timestamp' : result.get('timestamp').isoformat()
                       })

        result.pop('id')

    writer.writerows(results)

    return csv_output.getvalue()


def is_ref_id_in_db(ref_id):
    return Stats.select(Stats.project_name).where(Stats.ref_id == ref_id).count() > 0


def update_stats(project, user, ref_id, osm_id, osm_type, action):
    try:
        Stats(
            project_name=project,
            user=user,
            ref_id=ref_id,
            osm_id=osm_id,
            osm_type=osm_type,
            action=action,
            timestamp=datetime.now(),
            already_existed=is_ref_id_in_db(ref_id),
        ).save()
    except Exception as e :
        abort(500, "Can't connect to database")
