from app import db, bcrypt
from datetime import datetime
from flask_login import UserMixin



# DTO MODELS TO SCHEMAS
# MODELS CANNOT HAVE DEFINITIONS. Deactivate etc go to repos because they handle DB models.


# Association table for likes.
likes = db.Table(
    'likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True)
)

# Association table for dislikes.
dislikes = db.Table(
    'dislikes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True)
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email_address = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    name = db.Column(db.String)
    gender = db.Column(db.String)
    pronouns = db.Column(db.String)
    bio = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='owned_user', lazy=True)
    status = db.Column(db.String, default='active')


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    body = db.Column(db.String, nullable=False)
    owned_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tags = db.Column(db.String)
    likes_count = db.Column(db.Integer, default=0)
    dislikes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add comments

    # Define relationships with users for likes and dislikes
    liked_users = db.relationship('User', secondary=likes, backref=db.backref('liked_posts', lazy='dynamic'))
    disliked_users = db.relationship('User', secondary=dislikes, backref=db.backref('disliked_posts', lazy='dynamic'))

    def __repr__(self):
        return self.title