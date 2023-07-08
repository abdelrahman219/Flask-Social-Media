

from playhouse.migrate import *
from peewee import *


import models

database = SqliteDatabase('social.db')
migrator = SqliteMigrator(database)

migrate(
    query = models.Post.update(privacy='public').where(models.Post.privacy.is_null())
)
