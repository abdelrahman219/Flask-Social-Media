from playhouse.migrate import *
from peewee import *

database = SqliteDatabase('social.db')
migrator = SqliteMigrator(database)

migrate(
    migrator.add_column('post', 'privacy', TextField(null=True)),
)

