import csv
import time
from .db import Stats

def read_csv():
    csv_string = 'sep=;\rproject;user;ref_id;osm_id;type;timestamp;already_existed\r'
    for item in Stats.select():
        csv_string += f'{item.project_id};{item.user};{item.ref_id};{item.osm_id};{item.type};{item.timestamp};{item.already_existed}\r'
    return csv_string

def write_csv_header(file):
    with open(file, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["project", "user", "ref_id", "osm_id", "type", "timestamp", "already_existed"])


def update_csv(file, project, user, ref_id, osm_id, type):
    if not file.exists():
        write_csv_header(file)
    try:
        with open(file, 'a') as csv_file:
            writer = csv.writer(csv_file)
            exited_before = feature_in_db(ref_id)
            writer.writerow([project, user, ref_id, osm_id, type, time.time(), exited_before])
            Stats(project_id=project, user=user, ref_id=ref_id, osm_id=osm_id, type=type, timestamp=time.time(), already_existed = exited_before).save()
    except OSError:
        print(f"Couldn't write: {file}")


def feature_in_db(feature_ref):
    return Stats.select().where(Stats.ref_id == feature_ref).count() > 0