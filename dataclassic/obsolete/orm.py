from functools import partial
from collections import OrderedDict

from ..sql_helper import Column, KoalaRelationship, dialects, SelectFrom
from koala.doc_store import DocumentStore, Database, render_op
# import koala.doc_store
# DocumentStore = koala.doc_store.DocumentStore
# Database = koala.doc_store.Database






def make_property(name, doc=''):
    """Creates a property where the value is stored in the parent objects dbdict attribute.

    """
    def make_getter(name):
        def getter(self):
            return self.dbdict[name]
        return getter


    def maker_setter(name):
        def setter(self, value):
            self.dbdict[name] = value
        return setter


    def make_deleter(name):
        def deleter(self):
            self.dbdict.pop(name)
        return deleter

    return property(make_getter(name),
                    maker_setter(name),
                    make_deleter(name), doc=doc)


def make_fk_property(local_col, foreign_table, foreign_col):

    # foreign_table = foreign_table
    # if not isinstance(foreign_table, KoalaMetaClass):
    #     foreign_table = foreign_table()

    def getter(foreign_table, foreign_col, self):
        # ty = KoalaMetaClass[foreign_table]
        myval = self.dbdict[local_col]
        fcls = KoalaMetaClass.table_registry[foreign_table]
        if fcls._is_collection:
            foreign_col = foreign_col
            datastore = self.db.get_collection(foreign_table)
            try:
                item = datastore.find2({"$eq": {foreign_col: myval}}, limit=1)[0]
                item = fcls(**item)
            except:
                item = None
        else:
            item = fcls.query(db=self.db, query={"$eq": {foreign_col: myval}})[0]
        # )
        # s = SelectFrom(table=foreign_table, columns=foreign_col)
        # s = s.where('@{0} = ?'.format(foreign_col), (self.__columns__[local_col].value, ))
        # d = s.fetchone(self._db)
        # # coll = foreign_table.get_collection(self._db)
        # # d = coll.find2({'$eq': {foreign_col: self.__columns__[local_col]}})[0]
        #
        # item = foreign_table(**{k: v for k, v in d.items()})
        return item

    getter = partial(getter, foreign_table, foreign_col)

    def setter(self, value):
        print('setting fk')
        self.dbdict[local_col] = getattr(value, foreign_col)

    return property(getter, setter)

# def make_fk_sqlalchemy_property(local_col, foreign_table, foreign_col):
#
#     def getter(foreign_table, self):
#
#         d = SelectFrom(table=foreign_table, columns=foreign_col).fetchone(self._db)
#
#         item = foreign_table(**{k: v for k, v in d.items()})
#         return item
#
#     getter = partial(getter, foreign_table)
#
#     def setter(self, value):
#         print('setting fk')
#         self.__columns__[local_col] = getattr(value, foreign_col)
#
#     return property(getter, setter)


class KoalaMetaClass(type):
    """
    Meta class for orm layer for Koala Collections
    """
    table_registry = {}

    def __new__(cls, clsname, bases, cls_attrs):
        #print('metaclass called on ' + clsname)

        __columns__ = {}
        __foreign_keys__ = {}
        dbdict = OrderedDict()
        for c in list(cls_attrs.keys()):
            if isinstance(cls_attrs[c], Column):
                #print(clsname, c)
                #make propertes for regular columns
                __columns__[c] = cls_attrs[c]  # store the column information
                __columns__[c].name = c
                # __columns__[c].value = __columns__[c].default
                dbdict[c] = __columns__[c].default
                if __columns__[c].primary_key:
                    cls_attrs['primary_key'] = c
                cls_attrs[c] = make_property(name=c, doc=cls_attrs[c].doc)  # make a property in place of the column

            elif isinstance(cls_attrs[c], KoalaRelationship):
                # make foreign key properties for relationships
                loccol = cls_attrs[c].local_column
                fkcol = cls_attrs[c].foreign_column
                fktbl = cls_attrs[c].foreign_table
                __foreign_keys__[c] = cls_attrs[c]
                cls_attrs[c] = make_fk_property(loccol, fktbl, fkcol)


        cls_attrs['__columns__'] = __columns__
        cls_attrs['__foreign_keys__'] = __foreign_keys__
        cls_attrs['dbdict'] = dbdict
        if not '__tablename__' in cls_attrs:
            cls_attrs['__tablename__'] = clsname  # a different table name may be specified, but assume one if it isn't

        cls = super(KoalaMetaClass, cls).__new__(cls, clsname, bases, cls_attrs)
        KoalaMetaClass.table_registry[clsname] = cls

        return cls


class KoalaSqlalchemyRelationship:

    def __init__(self, local_column, foreign_table, foreign_column):

        self.local_column = local_column
        self.foreign_table = foreign_table
        self.foreign_column = foreign_column


class KoalaBase(metaclass=KoalaMetaClass):
    """
    Base class for koala ORM classes.  By default these classes will be stored in the database
    as a DocumentStore.  This behavior is controlled by the class attribute _is_collection.
    _is_collection is True by default.  If it is set to False, then the class is stored as
    a standard sql table and each column on the object gets it's own column in the database

    """

    _is_collection = True

    def __init__(self, **kwargs):
        self._db = None
        #self.dict_['ID'] = kwargs.pop('ID', uuid.uuid1().hex)

        for k in kwargs:
            try:
                self.dbdict[k] = kwargs[k]
            except KeyError:
                pass
        # if len(kwargs) > 0:
        #     self.dict_.update(kwargs)

    def columns(self):
        return list(self.__columns__.keys())
        #return self.dict_.keys()

    def as_dict(self, include_empties=False):

        if include_empties:
            return self.dbdict
            # return {k: c[k].value for k in c}
        else:
            c = self.dbdict
            return {k: c[k] for k in self.dbdict if c[k] is not None}

    @property
    def db(self):
        return self.__dict__['_db']

    @db.setter
    def db(self, value):
        self.__dict__['_db'] = value

    @classmethod
    def get_collection(cls, db=None, connection_string=None):

        if db is None:
            db = Database(connection_string)

        return DocumentStore(cls.__tablename__, db)

    @classmethod
    def connect(cls, connection_string):
        return KSession(connection_string)

    @classmethod
    def query(cls, db, query=None):

        col = cls.get_collection(db)
        if query is None:
            items = col.find()
        elif isinstance(query, (dict, OrderedDict)):
            items = col.find2(query)

        items = [cls(**item) for item in items]

        for item in items:
            item.db = col.db

        return items

    @classmethod
    def from_datatable(cls, table):
        return [cls(**dict(row)) for row in table.iter_rows()]


class StandardTable(KoalaBase):

    @classmethod
    def create(cls, db):
        """
        Creates the database in the table
        """
        c = db.cursor()
        cmd = db.dialect.render_table(cls.__tablename__,
                                      list(cls.__columns__.values()),
                                      list(cls.__foreign_keys__.values()))
        c.execute(cmd)
        db.conn.commit()

class DocStoreTable(KoalaBase):
    pass



def fetchmany_gen(cursor, size=10):
    """
    Uses the cursors' fetchmany method to create a generator that produces
    dictionaries of rows.
    """
    result = cursor.fetchmany(size)
    d = cursor.description()
    while result:
        for r in result:
            yield OrderedDict(zip(d, r))

        result = cursor.fetchmany(size)


class KSession(Database):
    """
    A KSession object that behaves a little like a sqlalchemy session
    """

    def query(self, object_type, filter=None, limit=None):

        if DocStoreTable in object_type.__mro__:
            collection_name = object_type.__name__
            ds = self.get_collection(collection_name)
            items = ds.find2(filter, limit=limit)

        elif StandardTable in object_type.__mro__:
            tablename = object_type.__name__
            if not tablename in self.tables():
                object_type.create(self)

            if filter:
                where_clause, params = render_op(filter)
            else:
                where_clause, params = None, None

            c = self.cursor()
            cmd, params = SelectFrom(tablename, self.dialect).where(where_clause, params).limit(limit).render()
            c.execute(cmd, params)
            # return fetchmany_gen(c, 10)
            items = c.fetchall()

        res = [object_type(**item) for item in items]

        for obj in res:
            obj.db = self

        return res

    def add(self, obj):
        c = DocumentStore(obj.__tablename__, self)
        # c = obj.get_collection(self)
        c.insert(obj.as_dict())
        obj.db = self

    def update(self, obj):
        c = DocumentStore(obj.__tablename__, self)
        # c = obj.get_collection(self)
        c.insert(obj.as_dict(), upsert=True)

    def delete(self, obj):
        c = DocumentStore(obj.__tablename__, self)
        # c = obj.get_collection(self)
        c.delete(obj.as_dict())

