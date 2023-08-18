from database import db
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Mapped
from datetime import datetime
import sys

class ContainerTypes(Enum):
    Box = 1
    Location = 2


@dataclass
class Location(db.Model):
    __tablename__ = "location"
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False)
    household_id: int = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    creation_date: datetime = db.Column(db.DateTime, default=datetime.utcnow())

    boxes = db.relationship("Box", back_populates="location")
    product_mappings = db.relationship("ProductContainerMapping", back_populates="location")


@dataclass
class Box(db.Model):
    __tablename__ = "box"
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id", ondelete="SET NULL"), nullable=True)
    household_id: int = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    creation_date: datetime = db.Column(db.DateTime, default=datetime.utcnow())

    product_mappings = db.relationship("ProductContainerMapping", back_populates="box")
    location: Mapped[Location] = db.relationship("Location", back_populates="boxes")



