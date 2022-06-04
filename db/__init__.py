import peewee

from fastapiProject.settings import DATABASE

db_settings = DATABASE.copy()

Engine = getattr(peewee, f'{db_settings.pop("engine", None)}Database', None)
if Engine is None:
    raise ImportError('The database engine is specified incorrectly')

db = Engine(
    db_settings.pop('name', None),
    **db_settings
)


def get_data(inst):
    if isinstance(inst, BaseModel):
        return inst.data()
    return inst


class BaseModel(peewee.Model):
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
