import csv
import time
from datetime import datetime
from .db import Stats
from io import StringIO
from flask import abort

def read_stats():
    csv_output = StringIO()

    writer = csv.DictWriter(csv_output, Stats._meta.fields.keys())
    print(Stats._meta.fields.keys())
    print(type(Stats._meta.fields.keys()))
    writer.writeheader()
    results = Stats.select().dicts()

    for result in results:
        result.update({
            'already_existed' : 'true' if bool(result.get('Stats.already_existed')) else 'false',
            'timestamp' : result.get('timestamp').isoformat()
                       })

    writer.writerows(results)

    return csv_output.getvalue()


def is_ref_id_in_db(ref_id):
    return Stats.select().where(Stats.ref_id == ref_id).count() > 0


def update_stats(project, user, ref_id, osm_id, action):
    try:
        Stats(
            project_name=project,
            user=user,
            ref_id=ref_id,
            osm_id=osm_id,
            action=action,
            timestamp=datetime.now(),
            already_existed=is_ref_id_in_db(ref_id),
        ).save()
    except Exception as e :
        print(e)
        abort(500, "Can't connect to database")
