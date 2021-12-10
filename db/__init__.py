# noinspection PyPackageRequirements
import os

from peewee import Model, SqliteDatabase
from backend.settings import BASE_DIR, DATABASE

# TODO creation of various databases

db = SqliteDatabase(os.path.join(BASE_DIR, DATABASE['NAME']))


class BaseModel(Model):
    def data(self, **kwargs) -> dict:
        """Returns a dictionary with fields, excluding hidden_fields"""
        hidden = getattr(self._meta, 'hidden_fields', None)
        # + kwargs.get('hidden_fields', None) # TODO
        if hidden is None:
            return self.__data__
        return {k: v for k, v in self.__data__.items() if k not in hidden}

    class Meta:
        database = db
        order_by = 'id'
