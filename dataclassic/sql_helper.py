from datetime import datetime, date
from collections import OrderedDict

class KoalaRelationship:
    """
    Defines a foreign key like relationship
    """



    def __init__(self, local_column, foreign_table, foreign_column, ondelete=None, onupdate=None):

        self.local_column = local_column
        self.foreign_table = foreign_table
        self.foreign_column = foreign_column
        self.ondelete = ondelete
        self.onupdate = onupdate

class SelectFrom:

    def __init__(self, table=None, dialect=None, **kwargs):
        self.parts = {'table': table,
                      'columns': '*',
                      'limit': None,
                      'where': None,
                      'params': list()}
        self.parts.update(kwargs)

        self.return_dicts = True

        if dialect is None:
            self.dialect = sqlite_dialect
        else:
            self.dialect = dialect


    def table(self, table):

        self.parts['table'] = table
        return self

    def columns(self, columns):

        self.parts['columns'] = columns
        return self

    def limit(self, count):
        if count:
            self.parts['limit'] = count
        return self

    def where(self, clause, params):

        self.parts['where'] = clause
        self.parts['params'].extend(params)
        return self

    def render(self):

        stmt = self.dialect.render_select(**self.parts)

        return stmt, tuple(self.parts['params'])

    def fetchall(self, db):
        self.cursor = db.cursor()
        # print(*self.render())
        self.cursor.execute(*self.render())
        res = self.cursor.fetchall()
        if self.return_dicts:
            res = [{d[0]: r for d,r in zip(self.cursor.description, row)} for row in res]
        return res

    def fetchone(self, db):
        self.cursor = db.cursor
        self.cursor.execute(*self.render())
        res = self.cursor.fetchone()
        if self.return_dicts:
            res = {d[0]: r for d,r in zip(self.cursor.description, res)}
        return res

    def fetchmany(self, db):
        """
        Call this repeatedly while fetchmany returns output
        :param db: the database connection
        :returns : results
        """
        if not hasattr(self, 'cursor'):
            self.cursor = db.cursor()
            self.cursor.execute(*self.render())

        res = self.cursor.fetchmany()
        if self.return_dicts:
            res = [{d[0]: r for d,r in zip(self.cursor.description, row)} for row in res]
        return res




class sqlite_dialect:
    """
    The sqlite database dialect of sql
    """
    typemap = {int: 'INTEGER',
               float: 'FLOAT',
               str: 'TEXT',
               datetime: 'DATETIME',
               date: 'DATE',
               bool: 'BOOLEAN',
               list: 'TEXT',
               dict: 'TEXT'}

    def __init__(self):
        pass

    def connect(self, dbfile):
        """
        Establishes a connection to a sqlite database
        """
        import sqlite3
        return sqlite3.connect(dbfile)

    @classmethod
    def render_column(cls, column):

        # Look for the type in the typemap.  If it's not there
        # assume that a string of an actual database type has been given
        dtype = cls.typemap.get(column.dtype, column.dtype)

        s = '    {n} {t}'.format(n=cls.qname(column.name), t=dtype)
        if column.primary_key:
            s += ' PRIMARY KEY '
        if column.autoinc:
            s += ' AUTOINCREMENT '
        if not column.nullable:
            s += ' Not Null '
        if column.default is not None:
            s += ' {0} '.format(str(column.default))
        if column.unique:
            s += ' UNIQUE '
        if column.check:
            s += ' CHECK ({0})'.format(column.check)

        return s

    @classmethod
    def render_foreign_key(cls, fk):
        """
        :param KoalaRelationship fk:
        """

        cmd = '    FOREIGN KEY ({local_column}) REFERENCES {table}({foreign_column})'
        cmd = cmd.format(local_column=cls.qname(fk.local_column),
                         table=cls.qname(fk.foreign_table),
                         foreign_column=(fk.foreign_column))
        if fk.ondelete:
            cmd += ' ON DELETE ' + fk.ondelete

        if fk.onupdate:
            cmd += ' ON UPDATE ' + fk.onupdate

        return cmd

    @classmethod
    def render_table(cls, name, columns, foreign_keys=None):
        """
        Renders the sql to create a table
        :param name: name of the table
        :param db_columns: columns for the table
        :return:
        """
        cmd = 'Create Table if not exists {name}('.format(name=cls.qname(name))

        cmd += ','.join(('\n' + cls.render_column(col) for col in columns))

        if foreign_keys:
            cmd += ','
            cmd += ','.join(('\n' + cls.render_foreign_key(fk) for fk in foreign_keys))

        cmd += '\n)'

        return cmd

    @classmethod
    def render_add_column(cls, table, column):
        """
        Renders and alter table sql statement to add a column to a table
        :param str table: the name of the table
        :param column: The column to add
        """
        cmd = 'Alter Table "{t}"\n  Add Column {c}'
        cmd = cmd.format(t=cls.qname(table),
                         c=cls.render_column(column))

        return cmd

    def render_drop_column(self, table, column):
        """
        Renders an alter table statement.
        **NOT SUPPORTED BY SQLITE**.  This will raise a NotImplementedError
        """
        raise NotImplementedError('SQLite does not support column deletetions')

    @classmethod
    def render_select(cls, table, columns, where=None, limit=None, **kwargs):
        """
        :param str table: Name of the table to select from
        :param (dict,list,str) columns: the columns to select
        """
        if isinstance(columns, (dict, OrderedDict)):
            cols = []
            for key in columns:
                if key.startswith('@'):
                    cols.append('{0} as {1}'.format(key, cls.qname(columns[key])))
                else:
                    cols.append('{0} as {1}'.format(cls.qname(key),
                                                        cls.qname(columns[key])))
            col_str = ", ".join(cols)
            # col_str = ", ".join(('"{0}" as "{1}"'.format(key, columns[key]) for key in columns))
        elif isinstance(columns, list):
            col_str = ", ".join([cls.qname(c) for c in columns])
        else:
            col_str = cls.qname(columns)

        cmd = 'select {c} from {t}'.format(c=col_str,
                                           t=cls.qname(table))

        if where is not None:
            cmd += ' WHERE {0}'.format(where)

        if limit is not None:
            cmd += ' LIMIT {0}'.format(limit)

        return cmd

    @classmethod
    def render_insert(cls, table, dict_):

        k = dict_.keys()
        cols = ",".join((cls.qname(c) for c in k))
        vals = ",".join(["?"] * len(dict_))
        cmd = 'insert into {t} ({c}) values({v})'.format(t=cls.qname(table),
                                                         c=cols,
                                                         v=vals)
        params = tuple((dict_[c] for c in k))
        return cmd, params

    @classmethod
    def render_update(cls, table, colname, colvalue, wherename, whereval):
        """
        """

        cmd_update = 'update {t} set {c} = ? where {w} = ?'
        return cmd_update.format(t=cls.qname(table),
                                 c=cls.qname(colname),
                                 w=cls.qname(wherename)), (colvalue, whereval)

    @classmethod
    def render_delete(cls, table, where_col, where_val=None):

        cmd = 'delete from {t} where {c} = ?'
        cmd = cmd.format(t=cls.qname(table),
                         c=cls.qname(where_col))
        return cmd, (where_val,)

    @classmethod
    def get_tables(cls, db):

        tables = SelectFrom('sqlite_master').columns('name').where("type = ?", ('table',)).fetchall(db)
        tables = [t['name'] for t in tables]
        return tables

    @classmethod
    def render_index(cls, name, table, attribute):
        cmd = 'create index {n} on {t} ({a});'
        cmd = cmd.format(n=cls.qname(name),
                         t=cls.qname(table),
                         a=cls.qname(attribute))
        return cmd

    @classmethod
    def _is_quoted(cls, v, quote_char):


        for q in quote_char:
            if v.startswith(q) and v.endswith(q):
                return True

        return False

    @classmethod
    def is_qval(cls, v):
        """
        Tells is a given value *v* is already quoted
        """
        # retval = (v.startswith("'") and v.endswith("'")) or \
        #          (v.startswith('"') and v.endswith("'"))
        return cls._is_quoted(v, ("'", '"'))

    @classmethod
    def is_qname(cls, n):
        """
        Tells is a given name *n* is already quoted
        """
        # retval = (n.startswith("'") and n.endswith("'")) or \
        #          (n.startswith('"') and n.endswith("'"))
        # return retval
        return cls._is_quoted(n, ("'", '"'))

    @classmethod
    def qval(cls, v):
        """
        Quotes string values or converts other types a a string
        """
        if v is None:
            return 'NULL'
        else:
            try:
                if cls.is_qval(v):
                    return v
                else:
                    return '"' + str(v) + '"'
            except AttributeError:
                return str(v)

    @classmethod
    def qname(cls, *n):
        """
        quotes table and column names
        """

        for i in range(len(n)):
            if cls.is_qname(n[i]):
                n[i] = n[i]
            else:
                return '"' + str(n[i]) + '"'

        return ".".join(n)



class mysql_dialect:
    pass


class sqlserver_dialect:

    typemap = {int: 'INT',
               float: 'REAL',
               str: 'TEXT',
               datetime: 'DATETIME2',
               date: 'DATE',
               bool: 'BIT',
               list: 'TEXT',
               dict: 'TEXT' }

    def get_tables(self, db):

        cursor = db.cursor()
        cursor.execute('show tables')
        tables = cursor.fetchall()
        if len(tables) > 0:
            tables = [t[0] for t in tables]

        return tables



dialects = {'sqlite': sqlite_dialect,
            'mysql': mysql_dialect,
            'sqlserver': sqlserver_dialect}

def isquoted(v):
    """
    Tells is a given value *v* is already quoted
    """
    retval = (v.startswith("'") and v.endswith("'")) or \
             (v.startswith('"') and v.endswith("'"))
    return retval


def quoteit(v):
    """
    Quotes string values or converts other types a a string
    """
    if v is None:
        return 'NULL'
    else:
        try:
            if isquoted(v):
                return v
            else:
                return '"' + str(v) + '"'
        except AttributeError:
            return str(v)


class Column(object):

    def __init__(self, dtype=str, doc='', default=None, foreign_key=None,
                 name=None, nullable=True, autoinc=False, primary_key=False, unique=False,
                 check=None):

        # if not type_hint in typemap.keys():
        #     raise TypeError('typehint must be one of ' + str(valid_type_hints))

        self.name = name
        self.doc = doc
        self.dtype = dtype
        self.default = default
        self.foreign_key = foreign_key
        self.value = default
        self.nullable = nullable
        self.autoinc = autoinc
        self.primary_key = primary_key
        self.unique = unique
        self.check = check

    def __eq__(self, other):

        cmd = '"{n}" = ?'.format(self.name)
        return cmd, (other, )

# class Column(object):
#
#     def __init__(self, name, dtype, nullable=True, default=None, autoinc=False,
#                  primary_key=False, unique=False):
#
#         self.name = name
#         self.dtype = dtype
#         self.nullable = nullable
#         self.default = default
#         self.autoinc = autoinc
#         self.primary_key = primary_key
#         self.unique = unique

    # def _render_sqlite(self):
    #
    #     s = '    "{n}" {t}'.format(n=self.name, t=self.dtype)
    #     if self.primary_key:
    #         s += ' PRIMARY KEY '
    #     if self.autoinc:
    #         s += ' AUTOINCREMENT '
    #     if not self.nullable:
    #         s += ' Not Null '
    #     if self.default is not None:
    #         s += ' {0} '.format(str(self.default))
    #     if self.unique:
    #         s += ' UNIQUE '
    #
    #
    #
    #     return s

    # def render(self, dialect=sqlite_dialect):
    #
    #     return dialect.render_column(self)

#
# def RenderTable(name, db_columns):
#     """
#     Renders the sql to create a table
#     :param name: name of the table
#     :param db_columns: columns for the table
#     :return:
#     """
#     cmd = 'Create Table if not exists {name}('.format(name=name)
#     for col in db_columns[:-1]:
#         cmd += '\n' + col.render() + ','
#     cmd += '\n' + db_columns[-1].render()
#     cmd += '\n)'
#
#     return cmd
#
#
# sqlite_type_map = {int:'INTEGER',
#                    float:'REAL',
#                    str:'TEXT',
#                    bool:'NUMERIC',
#                    None:'NULL'}