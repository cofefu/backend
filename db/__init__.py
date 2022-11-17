from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declared_attr, Session

from fastapiProject.settings import DATABASE


# DATA_BASE_URL = "dialect+driver://username:password@host:port/database"
def db_url():
    return f"{DATABASE.get('engine')}" \
           f"{f'+{x}' if (x := DATABASE.get('driver')) else ''}://" \
           f"{f'{x}' if (x := DATABASE.get('user')) else ''}" \
           f"{f':{x}' if (x := DATABASE.get('password')) else ''}" \
           f"{f'@{x}' if (x := DATABASE.get('host')) else ''}" \
           f"{f':{x}' if (x := DATABASE.get('port')) else ''}/" \
           f"{DATABASE.get('name')}"


DATABASE_URL = db_url()

engine = create_engine(
    DATABASE_URL,
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
