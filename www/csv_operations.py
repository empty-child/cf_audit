import csv
import time

def read_csv(file):
    if file.exists():
        try:
            with open(file, 'r') as csv_file:
                return csv_file.read()
        except OSError:
            return f"Couldn't read: {file}"
    else:
        try:
            write_csv_header(file)
        except OSError:
            return f"Couldn't write: {file}"
    return read_csv(file)


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
            exited_before = feature_in_csv(file, ref_id)
            writer.writerow([project, user, ref_id, osm_id, type, time.time(), exited_before])
    except OSError:
        print(f"Couldn't write: {file}")


def feature_in_csv(file, feature_ref):
    try:
        with open(file, 'r') as csv_file:
            reader = csv.DictReader(csv_file)

            for row in reader:
                if row['ref_id'] == feature_ref:
                    return True
            return False
    except OSError:
        print(f"Couldn't read: {file}")
        return False