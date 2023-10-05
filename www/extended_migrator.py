from playhouse.migrate import MySQLMigrator, operation, SqliteMigrator, PostgresqlMigrator
from peewee import Entity

class ExtendedMySQLMigrator(MySQLMigrator):
    @operation
    def change_column_type(self, table, new_field, new_type):
        ctx = self.make_context()
        change_ctx = (self
                    .make_context()
                    .literal('ALTER TABLE ')
                    .sql(Entity(table))
                    .literal(' MODIFY ')
                    .literal(f' "{new_field}" ')
                    .literal(f' {new_type} '))
        return change_ctx

class ExtendedSqliteMigrator(SqliteMigrator):
    @operation
    def change_column_type(self, table, new_field, new_type):
        ctx = self.make_context()
        change_ctx = (self
                    .make_context()
                    .literal('ALTER TABLE ')
                    .sql(Entity(table))
                    .literal(' MODIFY ')
                    .literal(f' "{new_field}" ')
                    .literal(f' {new_type} '))
        return change_ctx

class ExtendedPostgresqlMigrator(PostgresqlMigrator):
    @operation
    def change_column_type(self, table, new_field, new_type):
        ctx = self.make_context()
        change_ctx = (self
                    .make_context()
                    .literal('ALTER TABLE ')
                    .sql(Entity(table))
                    .literal(' ALTER COLUMN ')
                    .literal(f' "{new_field}" ')
                    .literal(f' TYPE {new_type} '))
        return change_ctx