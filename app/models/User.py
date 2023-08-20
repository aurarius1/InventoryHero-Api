from database import db
from dataclasses import dataclass
@dataclass
class User(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(80), unique=True, nullable=False)
    email: str = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(1024), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


@dataclass
class Household(db.Model):
    __tablename__ = "household"
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, unique=True, nullable=False)
    creator: int = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    members = db.relationship("HouseholdMembers", back_populates="household", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }


class HouseholdMembers(db.Model):
    __tablename__ = "household_members"
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    household = db.relationship("Household", back_populates="members")