# noinspection PyPackageRequirements
import os

from peewee import Model, SqliteDatabase

from fastapiProject.settings import BASE_DIR, DATABASE

# TODO creation of various databases

db = SqliteDatabase(os.path.join(BASE_DIR, DATABASE['NAME']), pragmas={
    'foreign_keys': 1,
    # 'journal_mode': 'wal',
    'cache_size': -1 * 64000,  # 64MB
})


def get_data(inst):
    if isinstance(inst, BaseModel):
        return inst.data()
    return inst


class BaseModel(Model):
    def data(self, **kwargs) -> dict:
        """Returns a dictionary with fields, excluding hidden_fields"""
        fields = set(self.__data__.keys()).union(set(kwargs.pop('fields', '')))
        fields -= set(kwargs.pop('hide', ''))

        if fields is None:
            return self.__data__
        return {k: get_data(getattr(self, k)) for k in self.__data__.keys() if k in fields}

    class Meta:
        database = db
        order_by = 'id'
