from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin):
    """Lightweight user wrapper around a MongoDB document"""
    def __init__(self, doc):
        self._doc = doc
        self.id = str(doc['_id'])
        self.username = doc.get('username')
        self.email = doc.get('email')
        self.password_hash = doc.get('password_hash')
        self.last_login = doc.get('last_login')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        d = dict(self._doc)
        d['id'] = str(d.pop('_id'))
        return d

    def __repr__(self):
        return f'<User {self.username}>'
