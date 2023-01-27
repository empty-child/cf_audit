import csv
import time
from .db import Stats
from io import StringIO
from flask import abort

def read_stats():
    csv_output = StringIO()

    writer = csv.DictWriter(csv_output, Stats._meta.fields.keys())
    writer.writeheader()

    writer.writerows(Stats.select().dicts())

    return csv_output.getvalue()


def is_ref_id_in_db(ref_id):
    return Stats.select().where(Stats.ref_id == ref_id).count() > 0


def update_stats(project, user, ref_id, osm_id, type):
    try:
        Stats(project_id=project, user=user, ref_id=ref_id, osm_id=osm_id, type=type, timestamp=time.time(), already_existed = is_ref_id_in_db(ref_id)).save()
    except Data:
        abort(500, "Can't connect to database")
