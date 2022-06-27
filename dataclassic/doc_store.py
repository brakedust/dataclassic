"""
collections module
-------------------

A JSON document store implemented on top of sqlite.

..code::python

    >>> # Created a connection to the database
    >>> mydb = koala.Database(":memory:")
    >>> #Create the collection
    >>> shapes = koala.Collection('shapes', mydb)

    >>> # Add some objects to the collection.  The key is optional.
    >>> shapes.insert(doc={"ID":"triangle",'sides':3, 'color':'red'})
    >>> shapes.insert(doc={"ID":"rectangle",'sides':4, 'color':'blue'})
    >>> shapes.insert(doc={"ID":"pentagon", 'sides':5, 'color':'red'})
    >>> shapes.insert(doc={'ID':"hexagon", 'sides':6, 'color': 'green'})

    >>> # Search by key
    >>> triangle2 = shapes.find_by_key('triangle')[0]
    >>> triangle2['color'] == 'red'
    True

Search using SQL.  The '@' character says that color is a field in the JSON document
Use of the ? operator is highly encoured to defend agaist SQL injection attacks

..code::python

    >>> s = shapes.find('@color = ?', ('red', ))
    >>> len(s) == 2
    True
    >>> s[0]['sides'] in (3,5)
    True

Searching with a syntax similar to MongoDB is also supported (and preferred).  Available operators are:
    =======             ======================
    OP                  Equivalent SQL
    =======             ======================
    $and, and           and
    $in                 in
    $or, or             or
    &like, like         like
    $nin, not in        not in
    $between, between   between
    $null, null         is null
    $nnull, not null    is not null
    $gt, gt, >          >
    $gte, gte, >=       >=
    $lt, lt, <          <
    $lte, lte, <=       <=
    $ne, ne, <>, !=     <>
    $eq, eq, =, ==      =

..code::python

    >>> # Search using MongoDB like syntax
    >>> query = {"$eq": {"@color":"red"}}
    >>> s = shapes.find2(query)
    >>> len(s) == 2
    True
    >>> s[0]['sides'] in (3,5)
    True

    >>> # A more complex query
    >>> query = {"$and":{"$eq": {"@color":"red"}, "$lt": "@sides": 4}}
    >>> s = shapes.find2(query)
    >>> len(s) == 1
    True
    >>> s[0]['sides'] == 3
    True

The above example is equivalent to:

..code::python

    >>> query = "@color = ? and @sides < ?}"
    >>> s = shapes.find(query, ('red', 4))

"""
# from dataclasses import is_dataclass


import re
import sqlite3
import uuid
from warnings import warn

from .dataclasses import asdict, is_dataclass
from .encoders import JsonEncoder, ZlibEncoder
from .sql_helper import Column, KoalaRelationship, dialects
from .sql_helper import sqlite_dialect as dialect

# from collections import OrderedDict

#from .orm import KoalaRelationship
    #RenderTable, sqlite_type_map as db_type_map


COLLECTION_SCHEMA = [
    Column(name='ID', dtype='CHAR(32)', nullable=False, primary_key=True),
    Column(name='Document', dtype='Text', nullable=False)
    ]


class DocumentStoreNotFound(Exception):
    """
    An exception rasied when a collection is not found in a database
    """
    pass

class Row(sqlite3.Row):

    def __str__(self):
        return 'Row({0})'.format(str({k: self[k] for k in self}))

    def __repr__(self):
        return str(self)


class Database(object):
    """
    Abstraction for sqlite database that can contain 'nosql' type JSON document stores.
    The @Database object provides methods that will be common across collections.
    """
    def __init__(self, connection_string, conn=None, encoder=JsonEncoder):

        dialect_name = connection_string.partition(':///')[0]
        self.dialect = dialects[dialect_name]()

        if conn is None:
            db_connection_string = connection_string.partition(':///')[-1]
            self.conn = self.dialect.connect(db_connection_string)
        else:
            self.conn = conn

        self.connection_string = connection_string
        #self.cursor = self.conn.cursor()
        #self.collections = self._get_collections()
        self.conn.row_factory = sqlite3.Row
        self.conn.create_function('field', 2, self._field)
        # self.cursor = self.conn.cursor()
        self.encoder = encoder()

        #self.collections = {c[11:]:DocumentStore(c[11:], db=self) for c in self.collection_tables()}

    def cursor(self):
        """
        get a cursor for the database connection
        """
        return self.conn.cursor()

    def connect(self):
        """
        Establish a connection to the database
        """
        db_connection_string = self.connection_string.partition(':///')[-1]
        self.conn = self.dialect.connect(db_connection_string)

    def close(self):
        """
        Close the database connection
        """
        self.conn.close()

    def reopen(self):
        """
        Closes and then opens the database collection
        """
        self.close()
        self.connect()

    def clone(self):
        """
        Closes and reestablishes the database connection
        """
        cls = type(self)
        return cls(self.connection_string, None, encoder=self.encoder)

    def tables(self):
        """
        Gets a list of tables from the database
        """
        tables = dialect.get_tables(self.conn)
        # self.cursor.execute("select name from sqlite_master where type='table';")
        # tables = [t[0] for t in self.cursor.fetchall()]
        return tables

    def collection_exists(self, collection):
        """
        Tells if a given collection exists in the database
        :param collection
        """
        try:
            if isinstance(collection, str):
                self.get_collection(collection)
                return True
            elif isinstance(collection, DocumentStore):
                self.get_collection(collection.name)
                return True
        except DocumentStoreNotFound:
            return False

    def get_collections(self):
        """
        Gets a list of tables that are collections (JSON document stores)
        """
        #c = [t for t in self.tables() if t.lower().startswith('collection_')]
        # self.cursor.execute("select name from sqlite_master where type='table'" \
        #     "and name like 'collection_%'")

        col = []
        for c in self.tables():
            if c.startswith('collection'):
                collection_name = c.partition('_')[2]
                col.append(DocumentStore(collection_name, self))
        return col

    def get_collection(self, collection_name):
        """
        Gets a collection by name
        """
        for c in self.get_collections():
            if (c.name == collection_name) or (c.table_name == collection_name):
                return c

        raise DocumentStoreNotFound('A collection with the specified name {0} does not exist.'.format(
            collection_name))


    def table_exists(self, table_name):
        """
        Tells if a given table exists in the database
        """
        #self.cursor.execute("select name from sqlite_master where type='table' and name='?';", table_name)
        return table_name in self.tables()

    #def create_function(self, name, param_count, func):
    #    self.conn.create_function(name, param_count, func)

    def encode(self, val):
        """
        Encodes the given value to be stored in the collection table
        """
        return self.encoder.encode(val)

    def decode(self, val):
        """
        Decodes a value retrieved from the collection store
        """
        return self.encoder.decode(val)

    def _field(self, val, f):
        """
        This function is meant to be added to a sqlite database using the
        create_function method on the database connection.  One can then select
        an arbitrary value from the stored document.  The sql command would
        look something like:

        .. code:: sql

        >> select document from mycollection where field(val,'a.b') > 0

        :param val: the value from the database
        :param f: the name of the field to retrieve.  It can be mutltipart like a.b
        """
        val = self.decode(val)

        if "." in f:
            fs = f.split('.')
            retval = val
            for ifs in fs:
                # recursively look up members
                if ifs in retval:
                    retval = retval[ifs]
                else:
                    # a sub member was not found, return None
                    return None
            return retval
        else:
            if f in val:
                return val[f]
            else:
                return None

    @classmethod
    def from_sa_session(cls, sa_session):
        """
        Creates a Database object from a sqlalchemy session
        """
        return cls(str(sa_session.bind.url))

    # the Database object can be used as a context manager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def opcodes(code):
    """
    Gets the function that should be used to evaluate the given constraint type
    """
    codes = {  "$and": ('and', _render_compound_op),
               "and": ('and', _render_compound_op),
               "$in": ("in", _render_list_op),
               "in": ("in", _render_list_op),
               "$or": ("or", _render_compound_op),
               "or": ("or", _render_compound_op),
               "&like": ("like", _render_compare_op),
               "like": ("like", _render_compare_op),
               "$nin": ("not in", _render_list_op),
               "not in": ("not in", _render_list_op),
               "$between": ("between", _render_list_op),
               "between": ("between", _render_list_op),
               "$null": ("is null", render_simple_op),
               "null": ("is null", render_simple_op),
               "$nnull": ("is not null", render_simple_op),
               "not null": ("is not null", render_simple_op),
               "$gt": (">", _render_compare_op),
               "gt": (">", _render_compare_op),
               ">": (">", _render_compare_op),
               "$gte": (">=", _render_compare_op),
               "gte": (">=", _render_compare_op),
               ">=": (">=", _render_compare_op),
               "$lt": ("<", _render_compare_op),
               "lt": ("<", _render_compare_op),
               "<": ("<", _render_compare_op),
               "$lte": ("<=", _render_compare_op),
               "lte": ("<=", _render_compare_op),
               "<=": ("<=", _render_compare_op),
               "$ne": ("<>", _render_compare_op),
               "ne": ("<>", _render_compare_op),
               "<>": ("<>", _render_compare_op),
               "!=": ("<>", _render_compare_op),
               "$eq": ("=", _render_compare_op),
               "eq": ("=", _render_compare_op),
               "=": ("=", _render_compare_op),
               "==": ("=", _render_compare_op)}

    return codes[code]


def render_op(d):
    """
    Renders a query operation to sql specified by dict d. A query may look like {'$gt':{'a':2}}. This would
    translate to the sql expresions 'a > 2'.  The syntax for sql injection prevention is used and
    ? characters are put in place of the query parameters and a tuple of the parameters is returned

    :param dict d: a dict containing the query
    :returns str sql_text: the text of the sql command
    :returns tuple params: the parameters to be passed to the database connection's execute method
    """
    opname = list(d.keys())[0]
    func_str = opcodes(opname)[0]
    render_func = opcodes(opname)[1]
    return render_func(func_str, d[opname])

def _render_compare_op(func_str, children):
    """
    Renders a simple compare op to sql

    :param str func_str: the operation string (i.e '>' or '=' or '<>')
    :param dict children:
    """
    column_name = list(children.keys())[0]
    value = children[column_name]
    return "{0} {1} ?".format(column_name, func_str), (value, )


def _render_compound_op(func_str, children):
    """
    Renders compound opertions (and, or) to sql
    """
    parts = []
    params = []
    for child in children:
        part, param = render_op({child: children[child]})
        parts.append(part)
        params.extend(param)

    sqlstr = (" {0} ".format(func_str)).join(parts)  # join the parts with *and* or *or*
    sqlstr = "({0})".format(sqlstr)  # put () around the whole expression
    return sqlstr, tuple(params)


def _render_list_op(func_str, children):
    """
    Renders list operations (in, not in) to sql
    """
    column_name = list(children.keys())[0]
    value = children[column_name]
    # if isinstance(value[0], str):
    #     value = ['"{0}"'.format(v) for v in value]
    # else:
    #     value = [str(v) for v in value]
    # value = '(' + ",".join(value) + ')'
    ques = '(' + ','.join(['?']*len(value)) + ')'
    return "{0} {1} {2}".format(column_name, func_str, ques), tuple(value)


def render_simple_op(func_str, children):
    """
    Renders simpler operations (is null, is not null) to sql
    """
    column_name = children
    return column_name + " " + func_str, tuple()



attribute_regex = re.compile(r'(\@\S+\b)') # an attribute in a query string is preceded by an @ character


class DocumentStore(object):
    """
    http://backchannel.org/blog/friendfeed-schemaless-mysql

    """
    def __init__(self, name, db=None, use_zlib_encoder=False, dtype=None):
        """
        Initializes the collection class
        :param str name: name of the collection
        :param Database db: database being used
        :param bool use_zlib_encoder: whether or not to use compression on the json blobs
        :param type dtype: dataclass type that can be inserted and retrieved from the collection
        """

        self.name = name
        self.dtype = dtype

        if isinstance(db, str):
            # a connection string was provided
            db = Database(db)
        self.db = db

        tables = db.tables()
        if ('collectionj_' + name) in tables:
            #table exists and uses a json encoder
            self.table_name = 'collectionj_' + name
            self._encoder = JsonEncoder()
        elif ('collection_' + name) in tables:
            #table exists and uses a json encoder
            self.table_name = 'collection_' + name
            self._encoder = JsonEncoder()
        elif ('collectionz_' + name) in tables:
            #tables exists and uses a zlib encoder
            self.table_name = 'collectionz_' + name
            self._encoder = ZlibEncoder()
        else:
            #table does not exist
            if use_zlib_encoder:
                self.table_name = 'collectionz_' + name
                self._encoder = ZlibEncoder()
            else:
                self.table_name = 'collectionj_' + name
                self._encoder = JsonEncoder()

            self.create()
        # self.db.encoder = self._encoder
        # if not self.table_name in tables:
        #     self.create()


    def create(self, index_attributes=None):
        """
        Creates the collection in the database

        """

        cmd = dialect.render_table(self.table_name, COLLECTION_SCHEMA)

        self.db.cursor().execute(cmd)

    def encode(self, val):
        """
        Encodes the given value to be stored in the collection table
        """
        return self._encoder.encode(val)

    def decode(self, val):
        """
        Decodes a value retrieved from the collection store
        """
        return self._encoder.decode(val)

    def get_index_name(self, attribute_name):
        """
        Gets the name of an index for the given attribute name.  It does not gaurantee the indexes existance.
        It simply constructs the name
        """
        return "index_" + attribute_name + "_on_" + self.name

    def has_index(self, attribute_name):
        """
        Returns true if an index table for this attribute exists
        """
        index_name = self.get_index_name(attribute_name)

        return index_name in self.db.tables()

    def add_index(self, attribute_name, sqltype, suppress_warning=False):
        """
        Adds an tables into the database name like *index_{attribute_name}_on_{table_name}.
        This index is joined to the collection table at query time and should speed up queries,
        as the json documents do not need to be decoded for the search.  This index table has two
        columns: The attribute name (of type *sqltype*) and ID (the same ID as in the collection table

        Additionally a sqlite itself indexes this index table to make searches on it fast.
        """
        index_name = self.get_index_name(attribute_name)

        if index_name in self.db.tables():
            if not suppress_warning:
                msg = 'Index of attribute {0} on collection {1} not created ' \
                      'because it already exists.'.format(attribute_name, self.name)
                warn(msg)

        else:
            IndexSchema = [
                Column(name='ID', dtype='CHAR(32)', primary_key=True, nullable=False),
                Column(name=attribute_name, dtype=sqltype, nullable=False)
                ]

            fk = KoalaRelationship('ID', self.table_name, 'ID', ondelete='CASCADE')
            cmd = dialect.render_table(index_name, IndexSchema, [fk])
            #print(cmd)
            self.db.conn.execute(cmd)

            index_cmd = dialect.render_index(name='index_'+index_name,
                                             table=index_name,
                                             attribute=attribute_name)

            self.db.conn.execute(index_cmd)

    def update_index(self, attribute_name, echo_sql=False):
        """
        Parses the json documents and populats the index tables associated with *attribute_name*
        """
        index_name = self.get_index_name(attribute_name)

        # cmd_find = 'select ID, @' + attribute_name + ' as ' + attribute_name + ' from ' + self.table_name
        cmd_find = dialect.render_select(self.table_name,
                                         dict([('ID', 'ID'),
                                                      ('@' + attribute_name, attribute_name)]))
        cmd_find = self._resolve_attributes(cmd_find)

        #cmd_insert1 = 'insert into ' + index_name + '(ID,' + attribute_name + ') values(?,?)'
        cmd_insert, __ = dialect.render_insert(index_name, dict([('ID', None), (attribute_name, None)]))
        #cmd_update = 'update ' + index_name + ' set ' + attribute_name + ' = ? where ID = ?'
        cmd_update, __ = dialect.render_update(index_name, attribute_name, None, 'ID', None)

        # if the index does not exist, infer the type and create it
        if attribute_name not in self.find_indexes():
            try:
                cursor_find = self.db.conn.execute(cmd_find)
                result = cursor_find.fetchone()
                ty = type(result[attribute_name])
                sqltype = dialect.typemap[ty]
                self.add_index(attribute_name, sqltype)
            except:
                raise DocumentStoreNotFound('Index "{0}" not found and type '
                                                  'could not be inferred for auto creation.'.format(index_name))

        # now do the update
        cursor_find = self.db.conn.execute(cmd_find)
        result = cursor_find.fetchmany(10)
        cursor_insert = self.db.conn.cursor()
        while result:

            for doc in result:
                #print(*r)
                try:
                    if echo_sql:
                        print('Trying Insert:')
                        print('    ' + cmd_insert, (doc['ID'], doc[attribute_name]))
                    cursor_insert.execute(cmd_insert, (doc['ID'], doc[attribute_name]))
                except sqlite3.IntegrityError as err:
                    if echo_sql:
                        print('Insert failed trying update:')
                        print('    ' + cmd_insert, (doc['ID'], doc[attribute_name]))
                    cursor_insert.execute(cmd_update, (doc[attribute_name], doc['ID']))

            result = cursor_find.fetchmany()

        self.db.conn.commit()

        # update the other.  look for items in the index who no longer have matching items in the
        # collection table
        cmd_find_index = dialect.render_select(index_name, 'ID')
        cursor_find_index = self.db.conn.execute(cmd_find_index)
        result = cursor_find_index.fetchmany()
        cmd_find_table = dialect.render_select(self.table_name, 'ID', where='ID = ?')
        cmd_delete, __ = dialect.render_delete(index_name, 'ID', None)

        while result:
            #loop over rows in the index table
            for doc in result:
                # look for rows in the colleciton table with a matching ID
                inner_cursor = self.db.conn.cursor()
                inner_cursor.execute(cmd_find_table, (doc['ID'],))
                inner_result = inner_cursor.fetchone()
                if not inner_result:
                    # if a matching id is not found, delete the row in the index table
                    # because it nows points to nothing.
                    inner_cursor.execute(cmd_delete, (doc['ID'],))


            result = cursor_find_index.fetchmany()

        self.db.conn.commit()

    def find_indexes(self, relook=False):
        """
        Returns a dict of indexes for this table.  The keys are the attribute names that indexed and
        the values are the names of the index tables.
        """
        self._indexes = getattr(self, '_indexes', None)
        if (not self._indexes) or (relook == True):
            index_name_regex = re.compile('index_(\S+)_on_' + self.name)

            self._indexes = {}

            for t in self.db.tables():
                m = index_name_regex.match(t)
                if m:
                    attribute = m.groups()[0]
                    self._indexes[attribute] = t

        return self._indexes

    def insert(self, doc, upsert=False):
        """
        Inserts a document into the collection table

        :param dict doc: the document (dict) to insert
        :param bool upsert: If True and the document already exists, then the existing document is updated
        """

        if is_dataclass(doc):
            doc_obj = doc
            doc = asdict(doc_obj)

        doc['ID'] = doc.get('ID', uuid.uuid1().hex)

        encoded_item = self.encode(doc)
        #cmd1 = 'insert into {n} values(?,?)'.format(n=self.table_name)
        cmd, params = dialect.render_insert(self.table_name, {'ID': doc['ID'], 'Document': encoded_item})

        indexes = self.find_indexes()

        with self.db.conn as conn:
            try:
                conn.execute(cmd, params)

                for attribute_name in indexes:
                    index_name = indexes[attribute_name]
                    cmd_insert, __ = dialect.render_insert(index_name, dict([('ID', None), (attribute_name, None)]))
                    conn.execute(cmd_insert, (doc['ID'], doc[attribute_name]))

            except sqlite3.IntegrityError as err:
                if upsert:
                    #cmd_update = 'update ' + self.table_name + ' set Document = ? where ID = ?'
                    cmd_update, params = dialect.render_update(self.table_name, 'Document', encoded_item, 'ID', doc['ID'])
                    conn.execute(cmd_update, params)
                    for attribute_name in indexes:
                        index_name = indexes[attribute_name]
                        cmd_update, __ = dialect.render_update(index_name, attribute_name, None, 'ID', None)
                        conn.execute(cmd_update, (doc[attribute_name], doc['ID']))
                else:
                    msg = 'Document with id={0} already exists. To update use insert(..,upsert=True)'.format(doc['ID'])
                    warn(msg)

        return doc

    def insert_many(self, docs, cursor=None, do_commit=False):
        """
        Inserts multiple documents into the collection table

        :param docs: list of documents (dicts) to insert
        :param cursor: a database connection cursor to use.  If this is None a new cursor is created
        :param do_commit: whether or not to commit the changes after all documents have been inserted

        Using the cursor and do_commit parameters are included for performance considerations.  The calling code
        could provide an existing cursor and handle calling commit.  This can lead to performane improvements if
        many inserts and deletes are being done.
        """
        cmd, __ = dialect.render_insert(self.table_name, dict([('ID', None), ('Document', None)]))

        _docs = []
        for doc in docs:
            if is_dataclass(doc):
                doc_obj = doc
                doc = asdict(doc_obj)
            doc['ID'] = doc.get('ID', uuid.uuid1().hex)
            _docs.append(doc)

        docs = _docs

        indexes = self.find_indexes()

        params = tuple([(doc['ID'], self.encode(doc)) for doc in docs])
        if not cursor:
            cursor = self.db.cursor()

        try:
            cursor.executemany(cmd, params)

            for attribute_name in indexes:
                index_name = indexes[attribute_name]
                index_params = tuple([((doc['ID'], doc[attribute_name])) for doc in docs])
                cmd_insert, __ = dialect.render_insert(index_name, dict([('ID', None), (attribute_name, None)]))
                cursor.executemany(cmd_insert, index_params)

        except sqlite3.IntegrityError:
            msg = 'Document with id={0} already exists.'
            warn(msg)

        if do_commit:
            self.db.conn.commit()

        return docs

    def delete(self, doc):
        """Deletes a single document from the DocumentStore
        :param doc: the document (dict) to delete
        """
        if is_dataclass(doc):
            uid = doc.ID
        else:
            uid = doc['ID']

        #cmd = 'DELETE FROM {t} WHERE ID = ?'
        cmd_delete, params = dialect.render_delete(self.table_name, 'ID', uid)

        with self.db.conn as conn:
            try:
                conn.execute(cmd_delete, params)
                indexes = self.find_indexes()
                for attribute_name in indexes:
                    cmd_delete, params = dialect.render_delete(indexes[attribute_name], 'ID', uid)
                    conn.execute(cmd_delete, params)
            except Exception as e:

                msg = 'Could not delete document with ID = {0}'.format(id)
                warn(msg + '\n' + msg)

    def delete_many(self, docs, cursor=None, do_commit=False):
        """
        Deletes multiple documents from the DocumentStore

        :param docs: list of documents (dicts) to delete
        :param cursor: a database connection cursor to use.  If this is None a new cursor is created
        :param do_commit: whether or not to commit the changes after all documents have been inserted

        Using the cursor and do_commit parameters are included for performance considerations.  The calling code
        could provide an existing cursor and handle calling commit.  This can lead to performane improvements if
        many inserts and deletes are being done.
        """
        if not docs:
            return

        uids = []
        for doc in docs:
            if is_dataclass(doc) and hasattr(doc, "ID"):
                uids.append(doc.ID)
            if 'ID' in doc:
                uids.append((doc['ID'], ))
        # uids = [(doc['ID'],) for doc in docs]

        #cmd = 'DELETE FROM {t} WHERE ID = ?'
        cmd, params = dialect.render_delete(self.table_name, 'ID', None)

        if cursor is None:
            cursor = self.db.cursor()

        try:
            cursor.executemany(cmd, uids)
            indexes = self.find_indexes()
            for attribute_name in indexes:
                cmd_delete, __ = dialect.render_delete(indexes[attribute_name], 'ID', None)
                cursor.executemany(cmd_delete, uids)

        except Exception as e:
            msg = 'Could not delete one document in = {0}'.format(uids)
            warn(msg + '\n' + msg)

        if do_commit:
            self.db.conn.commit()

    def _resolve_attributes(self, sql_command, use_index=False):
        """
        Searches for attributes in the sql command (prepended by an @ character) and replaces them with a
        call to the user defined function *field*
        """
        global attribute_regex

        self.db.encoder = self._encoder

        indexes = self.find_indexes()

        if not use_index:
            m = attribute_regex.findall(sql_command)
            for mi in m:
                sub = 'field(Document, "{f}")'.format(f=mi[1:])
                sql_command = sql_command.replace(mi,sub)

            return sql_command

        else:
            sqljoins = []
            m = attribute_regex.findall(sql_command)
            for mi in m:
                attribute = mi[1:]
                if attribute in indexes.keys():
                    #the index tables will be joined, so the attribute will be an actual column
                    sub = '{i}.{f}'.format(i=indexes[attribute], f=attribute)
                    sqljoins.append(' join {0} on {1}.ID={0}.ID'.format(indexes[attribute],
                                                                        self.table_name))
                else:
                    #the attribute is not indexed, so we must fetch it from the Document
                    sub = 'field(document, "{f}")'.format(f=attribute)
                sql_command = sql_command.replace(mi, sub)

            return sql_command, "\n".join(sqljoins)

    def find(self, clause=None, params=None, limit=None, dtype=None, echo_sql=False):
        """
        Searches for records in the collection.  To search for a field inside of the document
        use an *@* to prefix the the field name.

        :param str clause: the *where* clause to use in the query
        :param int limit: the limit for the number of records to retrieve
        :param bool full_record: if False then only the matching documents are returnd.  If True then the full
                                 database row is returned (the document is still parsed back into a python object)

        Examples:

            >>> mydb = koala.db.Database(":memory:")
            >>> shapes = koala.db.DocumentStore('shapes', mydb)

            >>> shapes.insert(key='triangle', doc={'sides':3, 'color':'red'})
            >>> shapes.insert(key='square', doc={'sides':4, 'color': 'green'})
            >>> shapes.insert(key='pentagon', doc={'sides':5, 'color':'red'})
            >>> shapes.insert(key='hexagon', doc={'sides':6, 'color': 'green'})

            >>> s = shapes.find('@color = "red"')
            [{'sides':3, 'color':'red'},{'sides':5, 'color':'red'}]

        """

        cmd = dialect.render_select(table=self.table_name, columns='Document')

        #Find JSON fields to include in query and replace them with calls to the field function
        sqljoin = ''
        if clause and len(clause) > 0:
            clause, sqljoin = self._resolve_attributes(clause, use_index=True)
            cmd += sqljoin + ' where ' + clause

        #apply the record limit
        if limit is not None:
            cmd += " limit {0}".format(int(limit))
        #print(cmd)

        #execute
        if echo_sql:
            print('sql   ={0}\nparams={1}'.format(cmd, params))

        cursor = self.db.cursor()
        if params:
            cursor.execute(cmd, params)
        else:
            cursor.execute(cmd)

        #now parse the fetched documents
        results = [self.decode(item['Document']) for item in cursor.fetchall()]

        dtype = dtype or self.dtype

        if dtype is not None:
            from dataclasses import is_dataclass
            if is_dataclass(dtype):
                results = [dtype(**res) for res in results]

        return results


    def find2(self, where=None, limit=None, echo_sql=False):
        """
        Search the colleciton using mongodb like syntax like:
        {'$gt':{'a':2}}
        This translates to
        "@a > "
        """

        if where is not None:
            where_clause, params = render_op(where)
        else:
            where_clause, params = None, None

        return self.find(where_clause, params, limit, echo_sql)

    def __eq__(self, other):

        return (self.name == other.name) and (self.db == other.db)


class Find:

    def __init__(self, dtype: type):
        self.dtype: type = dtype

        self._param_name = None
        self._op = None
        self._test_val = None

    def where(self, param_name):
        self._param_name = param_name
        return self

    def is_greater_than(self, test_val):
        self._op = ">"
        self._test_val = test_val
        return self

    def __gt__(self, test_val):
        return self.is_greater_than(test_val)

    def  is_greater_than_or_equal_to(self, test_val):
        self._op = ">="
        self._test_val = test_val
        return self

    def __gte__(self, test_val):
        return self.is_greater_than_or_equal_to(test_val)

    def is_less_than(self, test_val):
        self._op = ">"
        self._test_val = test_val
        return self

    def __lt__(self, test_val):
        return self.is_less_than(test_val)

    def  is_less_than_or_equal_to(self, test_val):
        self._op = "<="
        self._test_val = test_val
        return self

    def __lte__(self, test_val):
        return self.is_less_than_or_equal_to(test_val)

    def  is_equal_to(self, test_val):
        self._op = "<="
        self._test_val = test_val
        return self

    def __eq__(self, test_val: object) -> 'Find':
        return self.is_equal_to(test_val)

    def __str__(self):
        return f"{self._param_name} {self._op} {self._test_val}"



# if __name__ == "__main__":
#
#     db = Database(':memory:')
#
#     animals = DocumentStore('animals', db)
#
#     d1 = {'Color':'Brown', 'Height':5.2,'Legs':4,'Species':'canine','face':{'nose':'smooshed'}}
#     animals.insert(d1, key='pug')
#     animals.insert({'Color':'White', 'Height':3.0,'Legs':4,'Species':'feline','face':{'nose':'normal'}}, key='persian cat')
#     animals.insert({'Color':'Black', 'Height':6.0,'Legs':4,'Species':'canine','face':{'nose':'normal'}}, key='schnauzer')
#     animals.db.cursor.execute('select document from collection_animals where key="dog"')
#     print(animals.db.cursor.fetchall())
#
#     d2=animals.fetchone(key='pug')
#     print(d1)
#     print(d2)
#     print(set(d1.keys()) == set(d2.keys()))
#
#     animals.add_index('Species')
#
#     animals.db.cursor.execute('select * from collection_animals where field(document,"Species")="canine"')
#     res = animals.db.cursor.fetchall()
#     canines = animals.find('@Species like "%ine"')
#     print('Canines found')
#     print(canines)
#
#     print('Smooshed Noses')
#     print(animals.find('@face.nose = "smooshed"'))
#
#     print('All noses')
#     print(animals.find('@face.nose in ("smooshed","normal") and @Species = "canine"'))
#     a=1
#
#     #db.create_collection('animal',index_attributes=['size','color'])
