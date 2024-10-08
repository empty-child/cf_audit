import csv, json
import time
from datetime import datetime
from .db import Stats
from io import StringIO
from flask import abort

def read_stats():
    csv_output = StringIO()

    csv_fields = Stats._meta.fields.copy();
 
    writer = csv.DictWriter(csv_output, csv_fields.keys())
    writer.writeheader()
    results = Stats.select(*csv_fields.values()).dicts()

    for result in results:
        result.update({
            'already_existed' : str(result.get('already_existed')).lower(),
            'timestamp' : result.get('timestamp').isoformat(),
        })

    writer.writerows(results)

    return csv_output.getvalue()


def is_ref_id_in_db(ref_id):
    return Stats.select(Stats.project_name).where(Stats.ref_id == ref_id).count() > 0


def update_stats(project, user, ref_id, osm_id, osm_type, action, coordinates):
    try:
        Stats(
            project_name=project,
            user=user,
            ref_id=ref_id,
            osm_id=osm_id,
            osm_type=osm_type,
            action=json.dumps(action),
            timestamp=datetime.now(),
            already_existed=is_ref_id_in_db(ref_id),
            lat=coordinates[0],
            lon=coordinates[1]
        ).save()
    except Exception:
        abort(500, "Can't connect to database")
