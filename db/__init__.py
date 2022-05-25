import peewee

from fastapiProject.settings import DATABASE

Engine = getattr(peewee, f'{DATABASE.pop("engine", None)}Database', None)
if Engine is None:
    raise ImportError('The database engine is specified incorrectly')

db = Engine(
    DATABASE.pop('name', None),
    **DATABASE
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
