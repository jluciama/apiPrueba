from app import db, bcrypt
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(), nullable=False)
    email_address = db.Column(db.String(), nullable=False)
    password_hash = db.Column(db.String(), nullable=False)
    posts = db.relationship('Post', backref='owned_user', lazy=True)

    def set_password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

class Post(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(), nullable=False)
    body = db.Column(db.String(), nullable=False)
    owned_user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    tags = db.Column(db.String())

    def __repr__(self):
        return self.title