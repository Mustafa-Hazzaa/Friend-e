from flask_login import UserMixin
from web_interface import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    avatar = db.Column(db.String(20),nullable=False, default='profile_pics/default.jpg')
    def __repr__(self):
        return f'User {self.username} {self.email} {self.image_file}'
