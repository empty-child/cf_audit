from tabnanny import verbose
from peewee import (
    fn,
    Model,
    CharField,
    IntegerField,
    ForeignKeyField,
    TextField,
    FixedCharField,
    BooleanField,
    DateField,
    DoubleField,
    BigIntegerField,
    DateTimeField,
)
from playhouse.migrate import (
    migrate as peewee_migrate,
    SqliteMigrator,
    MySQLMigrator,
    PostgresqlMigrator,
)
from playhouse.db_url import connect
import config
import logging
import datetime

from .extended_migrator import (
    ExtendedMySQLMigrator,
    ExtendedSqliteMigrator,
    ExtendedPostgresqlMigrator
)

database = connect(config.DATABASE_URI)
if 'mysql' in config.DATABASE_URI:
    fn_Random = fn.Rand
else:
    fn_Random = fn.Random


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    uid = IntegerField(primary_key=True)
    admin = BooleanField(default=False)
    bboxes = TextField(null=True)


class Project(BaseModel):
    class Meta:
        db_table = 'project'

    name = CharField(max_length=32, index=True, unique=True)
    title = CharField(max_length=250)
    description = TextField()
    url = CharField(max_length=1000, null=True)
    feature_count = IntegerField()
    can_validate = BooleanField()
    hidden = BooleanField(default=False)
    bbox = CharField(max_length=250)
    updated = DateField()
    owner = ForeignKeyField(User, related_name='projects')
    overlays = TextField(null=True)
    audit = TextField(null=True)
    validate_modified = BooleanField(default=False)
    features_js = TextField(null=True)
    prop_sv = BooleanField(default=False)
    regional = BooleanField(default=False)


class Feature(BaseModel):
    project = ForeignKeyField(
        Project, index=True, related_name='features', on_delete='CASCADE'
    )
    ref = CharField(max_length=250, index=True)
    lat = IntegerField()  # times 1e7
    lon = IntegerField()
    region = CharField(max_length=200, null=True, index=True)
    action = FixedCharField(max_length=1)
    feature = TextField()
    feature_md5 = FixedCharField(max_length=32)
    audit = TextField(null=True)
    validates_count = IntegerField(default=0)


class Task(BaseModel):
    user = ForeignKeyField(User, index=True, related_name='tasks')
    feature = ForeignKeyField(Feature, index=True, on_delete='CASCADE')
    skipped = BooleanField(default=False)

class Stats(BaseModel):
    project_name = CharField(max_length=512, index=True)
    user = BigIntegerField()
    ref_id = CharField(max_length=512, index=True)
    osm_id = BigIntegerField()
    osm_type = CharField(max_length=256)
    action = CharField(max_length=512)
    timestamp = DateTimeField()
    already_existed = BooleanField()
    lat = DoubleField(default=0)
    lon = DoubleField(default=0)


# ------------------------------ MIGRATION ------------------------------


LAST_VERSION = 7


class Version(BaseModel):
    version = IntegerField()


@database.atomic()
def migrate():
    database.create_tables([Version], safe=True)
    try:
        v = Version.select().get()
    except Version.DoesNotExist:
        database.create_tables([User, Project, Feature, Task, Stats])

        v = Version(version=LAST_VERSION)
        v.save()

    if v.version >= LAST_VERSION:
        return

    if 'mysql' in config.DATABASE_URI:
        migrator = ExtendedMySQLMigrator(database)
    elif 'sqlite' in config.DATABASE_URI:
        migrator = ExtendedSqliteMigrator(database)
    else:
        migrator = ExtendedPostgresqlMigrator(database)

    v.version = 7
    if v.version == 0:
        # Making a copy of Project.owner field, because it's not nullable
        # and we need to migrate a default value.
        admin = (
            User.select(User.uid)
            .where(User.uid == list(config.ADMINS)[0])
            .get()
        )
        owner = ForeignKeyField(
            User, related_name='projects', to_field=User.uid, default=admin
        )

        peewee_migrate(
            migrator.add_column(
                User._meta.db_table, User.admin.db_column, User.admin
            ),
            migrator.add_column(
                Project._meta.db_table, Project.owner.db_column, owner
            ),
            migrator.add_column(
                Project._meta.db_table,
                Project.hidden.db_column,
                Project.hidden,
            ),
            migrator.add_column(
                Project._meta.db_table,
                Project.overlays.db_column,
                Project.overlays,
            ),
            migrator.add_column(
                Task._meta.db_table, Task.skipped.db_column, Task.skipped
            ),
            migrator.drop_column(Project._meta.db_table, 'validated_count'),
        )
        v.version = 1
        v.save()

    if v.version == 1:
        peewee_migrate(
            migrator.add_column(
                Project._meta.db_table,
                Project.validate_modified.db_column,
                Project.validate_modified,
            ),
            migrator.add_column(
                Project._meta.db_table, Project.audit.db_column, Project.audit
            ),
        )
        v.version = 2
        v.save()

    if v.version == 2:
        peewee_migrate(
            migrator.add_column(
                Project._meta.db_table,
                Project.features_js.db_column,
                Project.features_js,
            ),
        )
        v.version = 3
        v.save()

    if v.version == 3:
        peewee_migrate(
            migrator.add_column(
                Project._meta.db_table,
                Project.regional.db_column,
                Project.regional,
            ),
            migrator.add_column(
                Project._meta.db_table,
                Project.prop_sv.db_column,
                Project.prop_sv,
            ),
            migrator.add_column(
                Feature._meta.db_table,
                Feature.region.db_column,
                Feature.region,
            ),
        )

        v.version = 4
        v.save()

    if v.version == 4:
        database.create_tables([Stats])

        v.version = 5
        v.save()
    if v.version == 5:
        if 'mysql' in config.DATABASE_URI:
            peewee_migrate( 
                migrator.change_column_type(Project._meta.name, 'bbox', 'varchar(255)')
            )
        else:
            peewee_migrate( 
                migrator.change_column_type(Project._meta.name, 'bbox', 'character varying(255)')
            )

        v.version = 6
        v.save()
    if v.version == 6:
        peewee_migrate(
            migrator.add_column(
                Stats._meta.table_name,
                'lat',
                Stats.lat,
            ),
            migrator.add_column(
                Stats._meta.table_name,
                'lon',
                Stats.lon,
            ),
        )

        v.version = 7
        v.save()

    logging.info('Migrated the database to version %s', v.version)
    if v.version != LAST_VERSION:
        raise ValueError(
            'LAST_VERSION in db.py should be {}'.format(v.version)
        )
