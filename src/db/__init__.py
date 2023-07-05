from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declared_attr, Session

from src.config.settings import settings

engine = create_engine(
    settings.database_url,
    # connect_args={"check_same_thread": False}  # SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(declarative_base()):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, unique=True, autoincrement=True)

    # created_at = Column(TIMESTAMP, nullable=False)
    # updated_at = Column(TIMESTAMP, nullable=False)

    @declared_attr
    def __tablename__(cls):
        return f'{cls.__name__.lower()}s'

    # todo add **kwargs
    def data(self, *args: str) -> dict:
        """args: names of fields to hide"""
        hidden = {'_sa_instance_state'}.union(args)
        return {k: v for k, v in self.__dict__.items() if k not in hidden}

    def save(self, db: Session):
        db.add(self)
        db.commit()
        db.refresh(self)

    def delete(self, db: Session):
        db.delete(self)
        db.commit()

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id!r})>"
