from datetime import datetime
from app.extensions import db


class Artefact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    path = db.Column(db.String(300), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __str__(self):
        return f"{self.id} -> {self.name}"
