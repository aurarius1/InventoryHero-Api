from database import db
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.orm import Mapped


from .StorageContainer import Box, Location

@dataclass
class Product(db.Model):
    __tablename__ = "products"
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False)
    household_id: int = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    starred: bool = db.Column(db.Boolean, nullable=False, default=False)
    creation_date: datetime = db.Column(db.DateTime, default=datetime.utcnow())
    mappings = db.relationship("ProductContainerMapping", back_populates="product", cascade="all, delete-orphan")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "household_id": self.household_id,
            "starred": self.starred,
            "creation_date": self.creation_date
        }


@dataclass
class ProductContainerMapping(db.Model):
    __tablename__ = "product_container_mapping"
    id: int = db.Column(db.Integer, primary_key=True)
    product_id: int = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    box_id = db.Column(db.Integer, db.ForeignKey("box.id", ondelete="SET NULL"), nullable=True, default=None)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id", ondelete="SET NULL"), nullable=True, default=None)
    amount: int = db.Column(db.Integer, nullable=False, default=0)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow())

    product = db.relationship("Product", back_populates="mappings")
    box: Mapped[Box] = db.relationship("Box", back_populates="product_mappings")
    location: Mapped[Location] = db.relationship("Location", back_populates="product_mappings")

    def serialize(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "box": self.box,
            "location": self.location,
            "amount": self.amount,
            "updated_at": self.updated_at,
            "product": self.product
        }
