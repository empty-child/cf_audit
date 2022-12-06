from www import app
from .db import database, User, Feature, Project, Task, fn_Random
from .util import update_features, update_audit, update_features_cache, update_csv, read_csv
from flask import (
    session,
    url_for,
    redirect,
    request,
    render_template,
    flash,
    jsonify,
)
from flask_oauthlib.client import OAuth
from peewee import fn, OperationalError
from pathlib import Path
import json
import config
import codecs
import datetime
import math
import os


oauth = OAuth()
openstreetmap = oauth.remote_app(
    'OpenStreetMap',
    base_url='https://api.openstreetmap.org/api/0.6/',
    request_token_url='https://www.openstreetmap.org/oauth/request_token',
    access_token_url='https://www.openstreetmap.org/oauth/access_token',
    authorize_url='https://www.openstreetmap.org/oauth/authorize',
    consumer_key=app.config['OAUTH_KEY'] or '123',
    consumer_secret=app.config['OAUTH_SECRET'] or '123',
)


@app.before_request
def before_request():
    database.connect()


@app.teardown_request
def teardown(exception):
    if not database.is_closed():
        database.close()


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


app.jinja_env.globals['dated_url_for'] = dated_url_for


def get_user():
    if 'osm_uid' in session:
        try:
            return User.get(User.uid == session['osm_uid'])
        except User.DoesNotExist:
            # Logging user out
            if 'osm_token' in session:
                del session['osm_token']
            if 'osm_uid' in session:
                del session['osm_uid']
    return None


def is_admin(user, project=None):
    if not user:
        return False
    if config.EVERY_ONE_IS_ADMIN:
        return True
    if user.uid in config.ADMINS:
        return True
    if not project:
        return user.admin
    return user == project.owner


@app.route('/')
def front():
    user = get_user()
    projects = Project.select().order_by(Project.updated.desc())

    def local_is_admin(proj):
        return is_admin(user, proj)

    return render_template(
        'index.html',
        user=user,
        projects=projects,
        admin=is_admin(user),
        is_admin=local_is_admin,
    )


@app.route('/robots.txt')
def robots():
    return app.response_class(
        'User-agent: *\nDisallow: /', mimetype='text/plain'
    )


@app.route('/login')
def login():
    if 'osm_token' not in session:
        session['objects'] = request.args.get('objects')
        if request.args.get('next'):
            session['next'] = request.args.get('next')
        return openstreetmap.authorize(callback=url_for('oauth'))
    return redirect(url_for('front'))


@app.route('/oauth')
def oauth():
    resp = openstreetmap.authorized_response()
    if resp is None:
        return 'Denied. <a href="' + url_for('login') + '">Try again</a>.'
    session['osm_token'] = (resp['oauth_token'], resp['oauth_token_secret'])
    user_details = openstreetmap.get('user/details').data
    uid = int(user_details[0].get('id'))
    session['osm_uid'] = uid
    try:
        User.get(User.uid == uid)
    except User.DoesNotExist:
        User.create(uid=uid)

    if session.get('next'):
        redir = session['next']
        del session['next']
    else:
        redir = url_for('front')
    return redirect(redir)


@openstreetmap.tokengetter
def get_token(token='user'):
    if token == 'user' and 'osm_token' in session:
        return session['osm_token']
    return None


@app.route('/logout')
def logout():
    if 'osm_token' in session:
        del session['osm_token']
    if 'osm_uid' in session:
        del session['osm_uid']
    return redirect(url_for('front'))


@app.route('/project/<name>')
@app.route('/project/<name>/')
@app.route('/project/<name>/<region>')
def project(name, region=None):
    project = Project.get(Project.name == name)
    desc = project.description.replace('\n', '<br>')
    cnt = Feature.select(Feature.id).where(Feature.project == project)
    val1 = Feature.select(Feature.id).where(
        Feature.project == project, Feature.validates_count > 0
    )
    val2 = Feature.select(Feature.id).where(
        Feature.project == project, Feature.validates_count >= 2
    )
    corrected = Feature.select(Feature.id).where(
        Feature.project == project,
        Feature.audit.is_null(False),
        Feature.audit != '',
    )
    skipped = Feature.select(Feature.id).where(
        Feature.project == project, Feature.audit.contains('"skip": true')
    )

    if region is not None:
        val1 = val1.where(Feature.region == region)
        val2 = val2.where(Feature.region == region)
        cnt = cnt.where(Feature.region == region)
        corrected = corrected.where(Feature.region == region)
        skipped = skipped.where(Feature.region == region)
    if project.validate_modified:
        val1 = val1.where(Feature.action == 'm')
        val2 = val2.where(Feature.action == 'm')
        cnt = cnt.where(Feature.action == 'm')

    regions = []
    if project.regional:
        regions = (
            Feature.select(
                Feature.region,
                fn.Count(),
                fn.Sum(fn.Min(Feature.validates_count, 1)),
            )
            .where(Feature.project == project)
            .group_by(Feature.region)
            .order_by(Feature.region)
            .tuples()
        )
        if len(regions) == 1:
            regions = []
        else:
            regions = [(None, cnt.count(), val1.count())] + list(regions)

    user = get_user()
    if user:
        has_skipped = (
            Task.select()
            .join(Feature)
            .where(
                Task.user == user,
                Task.skipped == True,
                Feature.project == project,
            )
            .count()
            > 0
        )
    else:
        has_skipped = False
    return render_template(
        'project.html',
        project=project,
        admin=is_admin(user, project),
        count=cnt.count(),
        desc=desc,
        val1=val1.count(),
        val2=val2.count(),
        corrected=corrected.count(),
        skipped=skipped.count(),
        has_skipped=has_skipped,
        region=region,
        regions=regions,
    )


@app.route('/browse/<name>')
@app.route('/browse/<name>/<ref>')
def browse(name, ref=None, region=None):
    project = Project.get(Project.name == name)
    region = request.args.get('region')
    return render_template(
        'browse.html',
        project=project,
        ref=ref,
        region=region,
        mapillary_id=config.MAPILLARY_CLIENT_ID,
    )


@app.route('/map/<name>')
@app.route('/map/<name>/<ref>')
def show_map(name, ref=None, region=None):
    project = Project.get(Project.name == name)
    region = request.args.get('region')
    return render_template('map.html', project=project, ref=ref, region=region)

csv_file = Path(os.environ.get('CSV_FILE', ''))

@app.route('/run/<name>')
@app.route('/run/<name>/<ref>')
def tasks(name, ref=None, region=None):
    if not get_user():
        return redirect(url_for('login', next=request.path))
    project = Project.get(Project.name == name)
    region = request.args.get('region')
    if not project.can_validate:
        if ref:
            return redirect(url_for('browse', name=name, ref=ref))
        else:
            flash('Project validation is disabled')
            return redirect(url_for('project', name=name))
    return render_template(
        'task.html',
        project=project,
        ref=ref,
        region=region,
        mapillary_id=config.MAPILLARY_CLIENT_ID,
    )


# Lifted from http://flask.pocoo.org/snippets/44/
class Pagination(object):
    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(math.ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(
        self, left_edge=2, left_current=2, right_current=5, right_edge=2
    ):
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or num > self.pages - right_edge
                or (
                    num > self.page - left_current - 1
                    and num < self.page + right_current
                )
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    show_validated = request.args.get('all') == '1'
    if show_validated:
        args['all'] = '1'
    return url_for(request.endpoint, **args)


app.jinja_env.globals['url_for_other_page'] = url_for_other_page


@app.route('/table/<name>', defaults={'page': 1})
@app.route('/table/<name>/<int:page>')
def table(name, page):
    PER_PAGE = 200
    project = Project.get(Project.name == name)
    region = request.args.get('region')
    query = (
        Feature.select()
        .where(Feature.project == project)
        .order_by(Feature.id)
        .paginate(page, PER_PAGE)
    )
    show_validated = request.args.get('all') == '1'
    if not show_validated:
        query = query.where(Feature.validates_count < 2)
    if region:
        query = query.where(Feature.region == region)
    pagination = Pagination(page, PER_PAGE, query.count(True))
    columns = set()
    features = []
    for feature in query:
        data = json.loads(feature.feature)
        audit = json.loads(feature.audit or 'null')
        if audit and len(audit.get('move', '')) == 2:
            coord = audit['move']
        else:
            coord = data['geometry']['coordinates']
        f = {
            'ref': feature.ref,
            'lon': coord[0],
            'lat': coord[1],
            'action': data['properties']['action'],
        }
        tags = {}
        for p, v in list(data['properties'].items()):
            if not p.startswith('tags') and not p.startswith(
                'ref_unused_tags'
            ):
                continue
            k = p[p.find('.') + 1 :]
            if k.startswith('ref'):
                continue
            tag = {}
            if data['properties']['action'] in (
                'create',
                'delete',
            ) and p.startswith('tags.'):
                columns.add(k)
                tag['before'] = ''
                tag['after'] = v
                tag['accepted'] = not audit or k not in audit.get('keep', [])
                tag['action'] = data['properties']['action']
            else:
                if p.startswith('tags.'):
                    continue
                if p.startswith('tags_') or p.startswith('ref_unused_tags'):
                    columns.add(k)
                tag['accepted'] = p.startswith('tags_') or (
                    audit and k in audit.get('override', [])
                )
                if p.startswith('tags_new'):
                    tag['before'] = ''
                    tag['after'] = v
                    tag['action'] = 'created'
                elif p.startswith('tags_del'):
                    tag['before'] = ''  # swapping to print deleted value
                    tag['after'] = v
                    tag['action'] = 'deleted'
                elif p.startswith('tags_cha'):
                    i = v.find(' -> ')
                    tag['before'] = v[:i]
                    tag['after'] = v[i + 4 :]
                    tag['action'] = 'changed'
                elif p.startswith('ref_unused'):
                    tag['before'] = data['properties'].get('tags.' + k, '')
                    tag['after'] = v
                    tag['action'] = 'changed'
            tags[k] = tag
        f['tags'] = tags
        features.append(f)

    return render_template(
        'table.html',
        project=project,
        pagination=pagination,
        columns=sorted(columns),
        rows=features,
        show_validated=show_validated,
    )


@app.route('/newproject')
@app.route('/editproject/<pid>')
def add_project(pid=None):
    user = get_user()
    if not is_admin(user):
        return redirect(url_for('front'))
    if pid:
        project = Project.get(Project.id == pid)
    else:
        project = Project()
    return render_template('newproject.html', project=project)


@app.route('/newproject/upload', methods=['POST'])
def upload_project():
    def add_flash(pid, msg):
        flash(msg)
        return redirect(url_for('add_project', pid=pid))

    user = get_user()
    if not is_admin(user):
        return redirect(url_for('front'))
    pid = request.form['pid']
    if pid:
        pid = int(pid)
        project = Project.get(Project.id == pid)
        if not is_admin(user, project):
            return redirect(url_for('front'))
        update_audit(project)
    else:
        pid = None
        project = Project()
        project.feature_count = 0
        project.bbox = ''
        project.owner = user
        project.regional = True
    project.name = request.form['name'].strip()
    if not project.name:
        return add_flash(pid, 'Empty name - bad')
    project.title = request.form['title'].strip()
    if not project.title:
        return add_flash(pid, 'Empty title - bad')
    project.url = request.form['url'].strip()
    if not project.url:
        project.url = None
    project.description = request.form['description'].strip()
    project.can_validate = request.form.get('validate') is not None
    project.validate_modified = (
        request.form.get('validate_modified') is not None
    )
    project.hidden = request.form.get('is_hidden') is not None
    project.regional = request.form.get('regional') is not None
    project.prop_sv = request.form.get('prop_sv') is not None

    if 'json' not in request.files or request.files['json'].filename == '':
        if not pid:
            return add_flash(
                pid, 'Would not create a project without features'
            )
        features = []
    else:
        try:
            features = json.load(
                codecs.getreader('utf-8')(request.files['json'])
            )
        except ValueError as e:
            return add_flash(
                pid, 'Error in the uploaded features file: {}'.format(e)
            )
        if 'features' not in features or not features['features']:
            return add_flash(pid, 'No features found in the JSON file')
        features = features['features']

    audit = None
    if 'audit' in request.files and request.files['audit'].filename:
        try:
            audit = json.load(
                codecs.getreader('utf-8')(request.files['audit'])
            )
        except ValueError as e:
            return add_flash(
                pid, 'Error in the uploaded audit file: {}'.format(e)
            )
        if not audit:
            return add_flash(pid, 'No features found in the audit JSON file')

    proj_audit = json.loads(project.audit or '{}')
    if audit:
        proj_audit.update(audit)
        project.audit = json.dumps(proj_audit, ensure_ascii=False)
    if features or audit or not project.updated:
        project.updated = datetime.datetime.utcnow().date()
    project.save()

    if features or audit:
        with database.atomic():
            update_features(project, features, proj_audit)

    if project.feature_count == 0 and not pid:
        project.delete_instance()
        return add_flash(pid, 'Zero features in the JSON file')

    return redirect(url_for('project', name=project.name))


@app.route('/clear_skipped/<int:pid>')
def clear_skipped(pid):
    project = Project.get(Project.id == pid)
    user = get_user()
    if user:
        features = Feature.select().where(Feature.project == project)
        query = Task.delete().where(
            Task.user == user, Task.skipped == True, Task.feature.in_(features)
        )
        query.execute()
    return redirect(url_for('project', name=project.name))


@app.route('/delete/<int:pid>')
def delete_project(pid):
    project = Project.get(Project.id == pid)
    if not is_admin(get_user(), project):
        return redirect(url_for('front'))
    project.delete_instance(recursive=True)
    return redirect(url_for('front'))


@app.route('/export_audit/<int:pid>')
def export_audit(pid):
    project = Project.get(Project.id == pid)
    if not is_admin(get_user(), project):
        return redirect(url_for('front'))
    audit = update_audit(project)
    try:
        project.save()
    except OperationalError:
        pass
    return app.response_class(
        audit or '{}',
        mimetype='application/json',
        headers={
            'Content-Disposition': 'attachment;filename=audit_{}.json'.format(
                project.name
            )
        },
    )

@app.route('/export_csv/')
@app.route('/export_csv')
def download_csv():
    if not is_admin(get_user()):
        return redirect(url_for('front'))
    csv = read_csv(csv_file)
    return app.response_class(
        csv or '',
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=audit_csv.csv"
                 }
    )


@app.route('/external_audit/<int:pid>')
def external_audit(pid):
    project = Project.get(Project.id == pid)
    if not is_admin(get_user(), project):
        return redirect(url_for('front'))
    query = Feature.select().where(
        Feature.project == project, Feature.audit.is_null(False)
    )
    result = {}
    for feat in query:
        audit = json.loads(feat.audit or {})
        props = json.loads(feat.feature)['properties']
        eaudit = {}
        if 'move' in audit:
            if audit['move'] == 'osm':
                if 'were_coords' in props['were_coords']:
                    eaudit['move'] = props['were_coords']
            elif isinstance(audit['move'], list) and len(audit['move']) == 2:
                eaudit['move'] = audit['move']
        if 'keep' in audit:
            keep = {}
            for k in audit['keep']:
                orig = None
                if 'tags_deleted.' + k in props:
                    orig = props['tags_deleted.' + k]
                elif 'tags_changed.' + k in props:
                    orig = props['tags_changed.' + k]
                    orig = orig[: orig.find(' -> ')]
                if orig:
                    keep[k] = orig
            if keep:
                eaudit['keep'] = keep
        if audit.get('skip'):
            if audit.get('comment', '').lower() != 'duplicate':
                eaudit['skip'] = audit.get('comment', '<no reason>')
        if eaudit:
            result[feat.ref] = eaudit
    return app.response_class(
        json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True),
        mimetype='application/json',
        headers={
            'Content-Disposition': 'attachment;filename=ext_audit_{}.json'.format(
                project.name
            )
        },
    )


@app.route('/admin')
def admin():
    user = get_user()
    if not user or user.uid not in config.ADMINS:
        return redirect(url_for('front'))
    admin_uids = User.select(User.uid).where(User.admin == True).tuples()
    uids = '\n'.join([str(u[0]) for u in admin_uids])
    return render_template('admin.html', uids=uids)


@app.route('/admin_users', methods=['POST'])
def admin_users():
    uids = [int(x.strip()) for x in request.form['uids'].split()]
    User.update(admin=False).where(User.uid.not_in(uids)).execute()
    User.update(admin=True).where(User.uid.in_(uids)).execute()
    return redirect(url_for('admin'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = get_user()
    if not user:
        return redirect(url_for('login', next=request.path))
    if request.method == 'POST':
        user.bboxes = request.form['bboxes']
        user.save()
    return render_template('profile.html', user=user)


@app.route('/api')
def api():
    return 'API Endpoint'


@app.route('/api/features/<int:pid>.js')
def all_features(pid):
    project = Project.get(Project.id == pid)
    region = request.args.get('region')
    if region:
        query = (
            Feature.select(
                Feature.ref, Feature.lat, Feature.lon, Feature.action
            )
            .where(Feature.project == project, Feature.region == region)
            .tuples()
        )
        features = []
        for ref, lat, lon, action in query:
            features.append([ref, [lat / 1e7, lon / 1e7], action])
        features_js = json.dumps(features, ensure_ascii=False)
    else:
        if not project.features_js:
            update_features_cache(project)
            try:
                project.save()
            except OperationalError:
                # Sometimes wait is too long and MySQL disappears
                pass
        features_js = project.features_js
    return app.response_class(
        'features = {}'.format(features_js), mimetype='application/javascript'
    )


class BBoxes(object):
    def __init__(self, user):
        self.bboxes = []
        if user.bboxes:
            for bbox in user.bboxes.split(';'):
                self.bboxes.append([float(x.strip()) for x in bbox.split(',')])

    def update(self, user):
        if not self.bboxes:
            user.bboxes = None
        user.bboxes = ';'.join([','.join(x) for x in self.bboxes])

    def contains(self, lat, lon):
        for bbox in self.bboxes:
            if bbox[0] <= lat <= bbox[2] and bbox[1] <= lon <= bbox[3]:
                return True
        return False


@app.route('/api/feature/<int:pid>', methods=['GET', 'POST'])
def api_feature(pid):
    user = get_user()
    project = Project.get(Project.id == pid)
    if user and request.method == 'POST' and project.can_validate:
        ref_and_audit = request.get_json()
        if ref_and_audit and len(ref_and_audit) == 2:
            skipped = ref_and_audit[1] is None
            feat = Feature.get(
                Feature.project == project, Feature.ref == ref_and_audit[0]
            )
            user_did_it = (
                Task.select(Task.id)
                .where(Task.user == user, Task.feature == feat)
                .count()
                > 0
            )

            Task.create(user=user, feature=feat, skipped=skipped)
            if not skipped:
                if len(ref_and_audit[1]):
                    new_audit = json.dumps(
                        ref_and_audit[1], sort_keys=True, ensure_ascii=False
                    )
                else:
                    new_audit = None
                if feat.audit != new_audit:
                    feat.audit = new_audit
                    feat.validates_count = 1
                elif not user_did_it:
                    feat.validates_count += 1
                feat.save()

                update_csv(csv_file, project, user, ref_and_audit[0], ref_and_audit[1])
    region = request.args.get('region')
    fref = request.args.get('ref')
    if fref:
        feature = Feature.get(Feature.project == project, Feature.ref == fref)
    elif not user or request.args.get('browse') == '1':
        query = Feature.select().where(Feature.project == project)
        if region:
            query = query.where(Feature.region == region)
        feature = query.order_by(fn_Random()).get()
    else:
        try:
            # Maybe use a join: https://stackoverflow.com/a/35927141/1297601
            task_query = Task.select(Task.id).where(
                Task.user == user, Task.feature == Feature.id
            )
            query = (
                Feature.select()
                .where(Feature.project == project, Feature.validates_count < 2)
                .where(~fn.EXISTS(task_query))
                .order_by(Feature.validates_count, fn_Random())
            )
            if project.validate_modified:
                query = query.where(Feature.action == 'm')
            if region:
                query = query.where(Feature.region == region)
            if user.bboxes:
                bboxes = BBoxes(user)
                feature = None
                for f in query:
                    if bboxes.contains(f.lat / 1e7, f.lon / 1e7):
                        feature = f
                        break
                    elif not feature:
                        feature = f
                if not feature:
                    raise Feature.DoesNotExist()
            else:
                feature = query.get()
        except Feature.DoesNotExist:
            return jsonify(feature={}, ref=None, audit=None)
    return jsonify(
        feature=json.loads(feature.feature),
        ref=feature.ref,
        audit=json.loads(feature.audit or 'null'),
    )
