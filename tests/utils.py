from sqlalchemy.orm import Session
from app.models import Order


def get_random_order(db: Session) -> Order:
    return db.query(Order).first()
