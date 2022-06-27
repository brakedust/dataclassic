# coding: utf-8
"""
sqlalchemy_collections module
=============================

This module provides a function to create a "collection" class similar to a nosql document collection.  The bulk of
the content is stored in a zlib compressed json string in a **Doc** attribute.

Creating a Collection
---------------------

A collection is created by calling the **create_collection** function.

"""

import sqlalchemy as sa
import sqlalchemy.sql as sql
import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base
base = declarative_base()
import uuid
from koala.encoders import ZlibEncoder, JsonEncoder





def make_indexed_property(name, doc_string=''):
    """
    Creates a property for an indexed column on a collection. The setter will store the value in an
    attribute of the same name as the column but prepended with an underscore character. The setter also
    sets the value in the Doc dictionary.

    The getter returns the value from the class instance attribute.

    The deleter does nothing, since we can't delete the column in the database.
    """
    def make_getter(name):
        def getter(self):
            return getattr(self, '_' + name)
        return getter

    def maker_setter(name):
        def setter(self, value):
            setattr(self, '_' + name, value)
            self.Doc[name] = value
        return setter

    def make_deleter(name):
        pass

    return property(make_getter(name),
                    maker_setter(name),
                    make_deleter(name), doc=doc_string)


def make_property(name, doc_string=''):
    """
    Creates a property for an indexed column on a collection. The setter will store the value in an
    attribute of the same name as the column but prepended with an underscore character. The setter also
    sets the value in the Doc dictionary.

    The getter returns the value from the class instance attribute.

    The deleter does nothing, since we can't delete the column in the database.
    """
    def make_getter(name):
        def getter(self):
            return self.Doc.get(name, None)
        return getter

    def maker_setter(name):
        def setter(self, value):
            self.Doc[name] = value
        return setter

    def make_deleter(name):
        def deleter(self, name):
            del self.Doc[name]
        return deleter

    return property(make_getter(name),
                    maker_setter(name),
                    make_deleter(name), doc=doc_string)


class JSONEncodedDict(sa.TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::
        JSONEncodedDict()
    """

    impl = sa.VARCHAR(2048)
    encoder = JsonEncoder()

    def process_bind_param(self, value, dialect):
        if value is not None:
            # value = json.dumps(value)
            value = self.encoder.encode(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            # value = json.loads(value)
            value = self.encoder.decode(value)
        return value

    def python_type(self, value):
        if value is not None:
            # value = json.loads(value)
            value = self.encoder.decode(value)
        return value


def create_collection(name, bases=None, indexes=None, tablename=None, other_columns=None):
    """
    Creates a collection class which is a special sqlalchemy declarative class.  It has **Doc**
    attribute for storing most of it's conent.  **indexes** is a dictionary of columns that you want to be able
    to query.  It is a dict with names of columns as the keys and sqlalchemy types as the values.

    :param str name: The name of the collection class.  If tablename is None, then this will be the table name too.
    :param bases: list of base classes
    :param dict indexes: List of columns to be indexed
    :param str tablename: Name of the table in the database.
    :param list other_columns: A list of other columns that you would like a property on the class for accessing.  This
        is merely a convience and does not affect how the table is actually created.  The properties are convenience
        methods for getting and setting items in the Doc dict.
    """
    base = declarative_base()
    
    if bases is None:
        bases = []
    else:
        bases = list(bases)
    bases.insert(0, base)

    if tablename is None:
        tablename = name

    index_columns = []
    if indexes is not None:
        for key in indexes:
            # index_columns.append(sa.Column('_' + key, indexes[key], nullable=True, default=None))
            index_columns.append(sa.Column(key, indexes[key], nullable=True, default=None))

    
    table = sa.Table(tablename, base.metadata,
        sa.Column('ID', sa.String(32), nullable=False, primary_key=True),
        sa.Column('Doc', JSONEncodedDict(), nullable=False),
        *index_columns
        )
        
    def init(self, **kwargs):
            self.ID = kwargs.pop('ID', None)
            self.Doc = kwargs.pop('Doc', None)

            # creat the document if it doesn't exist
            if not self.Doc:
                self.Doc = {}

            # create the document ID is it hasn't been specified
            if not self.ID:
                self.ID = self.Doc.get('ID', uuid.uuid1().hex)
                self.Doc['ID'] = self.ID

            column_names = [c.name for c in self.__table__.columns]
            for field in list(self.Doc.keys()):
                if field in column_names:  # or '_'+field in column_names:
                    setattr(self, field, self.Doc[field])
                    self.Doc.pop(field)
            
            super(type(self), self).__init__()
            
    def _repr(self):
        d = self.__dict__
        mykwargs = ', '.join(['{0}={1}'.format(str(k), repr(d[k])) for k in d
                              if k not in ['_sa_instance_state']])
        return '{0}({1})'.format(type(self).__name__, mykwargs)
            
    # def update_index_columns(self):
    #
    #     for c in self.Doc.keys(): #(c2 for c2 in self.get_column_names() if c2 not in ('ID', 'Doc')):
    #         if c == 'ID':
    #             setattr(self, c, self.Doc[c])
    #         else:
    #             setattr(self, '_' + c, self.Doc[c])

    def as_dict(self):
        """
        returns a dict representation of the data in this class
        """
        # self.update_index_columns()
        #
        return {c: getattr(self, c) for c in self.get_column_names()}

    def as_flat_dict(self):
        d = self.as_dict()
        doc = d.pop('Doc')
        d.update(doc)
        return d

    @classmethod
    def create(cls, bind):
        """
        Creates the table in the database if necessary
        :param bind: the sqlalchemy engine
        :param bool checkfirst: if true the presence of the table is checked for before trying to create the table
        """
        print('Creating table on database if necessary.')
        cls.__table__.create(bind=bind, checkfirst=True)

    def get_column_names(self):
        """
        Returns the column names in the database
        """
        cols = list(self.__table__.columns.keys())
        # for i in range(len(cols)):
        #     if cols[i].startswith('_') and hasattr(self, cols[i][1:]):
        #         cols[i] = cols[i][1:]
        return cols

    def get_doc_fields(self):
        """
        Returns the column names in the database plus the names of the keys in the Doc dict
        """
        doc_keys = tuple(self.Doc.keys())
        return doc_keys
    # def __getattr__(self, item):
    #
    #     if ('Doc' in self.__dict__) and (item in self.__dict__['Doc']):
    #         return self.Doc[item]
    #     elif item in self.__dict__:
    #         return super(type(self), self).__getattr__(item)
    def get(self, item, default=None):
        """
        Retrieves an item from the Doc.  An optional default value may be supplied if desired.  This simply
        calls the get method on the Doc dict.
        """
        return self.Doc.get(item, default)

    @classmethod
    def insert_many(cls, connection, dicts):
        """
        Inserts a list of dicts into the table
        :param dicts: the list of dicts
        :param connection: the database connection
        """
        dicts = [cls(**d).as_dict() for d in dicts]  # the class constructor makes the
                                                     # indexes consistent with the doc content

        expr = cls.__table__.insert()
        connection.execute(expr, *dicts)

    @classmethod
    def delete_many(cls, connection, dicts):
        """
        Deletes a list of dicts from the table.  The dicts must have an ID key to be deletable this way.
        :param dicts: the list of dicts
        :param connection: the database connection
        """
        expr = cls.__table__.delete()
        dicts = [d for d in dicts if 'ID' in d]
        connection.execute(expr, *dicts)


    collection_class_attrs = {'__table__': table,
                              '__init__': init,
                              '__repr__': _repr,
                              '__tablename__': tablename,
                              'as_dict': as_dict,
                              'as_flat_dict': as_flat_dict,
                              'create': create,
                              'get': get,
                              'get_column_names': get_column_names,
                              'get_doc_fields': get_doc_fields,
                              # 'update_index_columns': update_index_columns,
                              'insert_many': insert_many,
                              'delete_many': delete_many}

    # if indexes:
    #     for key in indexes:
    #         collection_class_attrs[key] = make_indexed_property(key)

    if other_columns:
        for key in other_columns:
            collection_class_attrs[key] = make_property(key)

    new_class = type(name, tuple(bases), collection_class_attrs)

    return new_class
            

# if __name__ == "__main__":
#     engine = sa.create_engine('sqlite:///:memory:')
#     conn = engine.connect()
#     session_factory = orm.sessionmaker(bind=engine)
#
#     # In[4]:
#
#     Shape = create_collection('shapes', indexes={'sides': sa.Integer})
#     Shape.create(bind=engine, checkfirst=True)
#     # Shape.__table__.create(bind=engine, checkfirst=True)
#     # metadata.create_all(engine)
#     print(engine.table_names())
#     # print(dir(metadata))
#
#
#     # In[5]:
#
#     cmd = str(Shape.__table__.insert())
#     cmd
#
#
#     # In[6]:
#
#     new_shapes = [Shape(Doc={'type': 'triangle', 'sides': 3, 'color':'red', 'filled': False}),
#                   Shape(Doc={'type': 'square', 'sides': 4, 'color': 'green'}),
#                   Shape(Doc={'type': 'pentagon', 'sides': 5, 'color':'red'}),
#                   Shape(Doc={'type': 'hexagon', 'sides': 6, 'color': 'green', 'filled': True})]
#     print(new_shapes[0])
#
#
#     # In[7]:
#
#     expr = Shape.__table__.insert()
#     print(str(expr))
#     conn.execute(expr, *[s.as_dict() for s in new_shapes])
#
#
#     print(engine.table_names())
#     session = session_factory()
#     res = session.query(Shape).all()
#
#     # In[8]:
#
#     # c=conn.execute('select * from shapes')
#     # res = session.query(Shape).all()
#     print(res)
#
#
#     # In[10]:
#
#
#
#     # In[12]:
#
#     res = session.query(Shape).filter(Shape._sides < 5).all()
#     print(res)
#
#     print(res[0].Doc['type'])
#     print(res[0].get('type'))
#     print(res[0].get_column_names())
#     print(res[0].get_doc_fields())