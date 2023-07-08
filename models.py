import datetime
from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *

DATABASE = SqliteDatabase('social.db')

class User(UserMixin, Model):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_at = DateTimeField(default=datetime.datetime.now)
    is_admin = BooleanField(default=False)
    
    

    class Meta:
        database = DATABASE
        order_by = ('-joined_at',)

    def get_posts(self):
        return Post.select().where(Post.user == self)

    def get_stream(self):
        return Post.select().where(
            (Post.user << self.following()) | (Post.user == self)
        )

    def following(self):
        return User.select().join(
            Relationship, on=Relationship.to_user
        ).where(Relationship.from_user == self)
    # python -c "from models import User; User.following()"
    def friends(self):
        return User.select().join(
            Friends_list, on=Friends_list.friend
        ).where(Friends_list.user == self)
    # python -c "from models import friends; friends()"

    def followers(self):
        return User.select().join(
            Relationship, on=Relationship.from_user
        ).where(Relationship.to_user == self)



    @classmethod
    def create_user(cls, username, email, password, admin=False):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=admin
                )
        except IntegrityError:
            raise ValueError("User already exists")






class Post(Model):
    PRIVACY_OPTIONS = [
        ('public', 'Public'),
        ('friends_only', 'Friends Only'),
        ('only_me', 'Only Me')
    ]

    timestamp = DateTimeField(default=datetime.datetime.now)
    user = ForeignKeyField(User, related_name='posts')
    content = TextField()
    privacy = CharField(choices=PRIVACY_OPTIONS, default='public')

    class Meta:
        database = DATABASE
        order_by = ('-timestamp',)


class Relationship(Model):
    from_user = ForeignKeyField(User, related_name='relationships')
    to_user = ForeignKeyField(User, related_name='related_to')

    class Meta:
        database = DATABASE
        indexes = (
            (('from_user', 'to_user'), True),
        )


class Friendship(Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    )
    
    sender = ForeignKeyField(User, backref='friendships_sent')
    receiver = ForeignKeyField(User, backref='friendships_received')
    accepted = CharField(choices=STATUS_CHOICES, default='pending')

    class Meta:
       
        database = DATABASE
        indexes = ((('sender', 'receiver'), True),)


class Friends_list(Model):
    user = ForeignKeyField(User, backref='friends')
    friend = ForeignKeyField(User, backref='friend_of')

    class Meta:
        database = DATABASE
        indexes = (
            (('user', 'friend'), True),
        )










        
def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Post, Relationship,Friendship,Friends_list], safe=True)
    DATABASE.close()

    # python -c "from models import initialize; initialize()"
