import os, sqlite3, pandas as pd

class SqliteDB:
  """
    implementation classe for sqlite3 files

    usage: db=SqliteDB('file.db')
  """
  def __init__(self, db_file):
    self.db_file = db_file
    self.conn = self.connect()
    self.conn.row_factory = sqlite3.Row
    self.cur = None

  def connect(self):
    """ internal (open connection to db)"""
    return sqlite3.connect(self.db_file, check_same_thread=False)

  def __del__(self):
    print('sqlite destructor')
    if self.conn is not None:
      self.conn.close()
      self.conn=None

    # if self.cur is not None:
    #   self.cur.close()
    #   self.cur=None

  def execute(self, query, params=None):
    """
      execute a query

      usage: db.execute('sql query ? ?',(param1, param2))
      note if only 1 parameter use (param1,)
    """
    cur = self.conn.cursor()

    if params is None:
      cur.execute(query)
    else:
      cur.execute(query, params)

    self.conn.commit()

    return cur

  def table_as_pd(self, table_name:str):
    """
      return a table as a pd dataset

      use: db.table_as_pd('tablename')
    """
    return self.query_as_pd(f"SELECT * FROM {table_name}")

  def query_as_pd(self, query, params=None):
    """
      return a query as a pd dataset

      use: db.query_as_pd('query ?', (parameter1,))
    """
    return pd.read_sql_query(query, self.conn, params=params)


class SqliteChatHistory:
  """
    implement an interface for LLM chat with history

    usage: chatHistory=SqliteChatHistory(fname)

    if fname is None the file created is: sqlite_chat_history.db
  """
  def __init__(self, db_file='sqlite_chat_history.db'):
    if not os.path.exists(db_file):
      schema="""\
        CREATE TABLE message_store (
            id INTEGER NOT NULL,
            session_id TEXT,
            question TEXT,
            answer TEXT,
            PRIMARY KEY (id)
        );
        """
      self.db=SqliteDB(db_file)
      self.db.execute(schema)
    else:
      self.db=SqliteDB(db_file)

  def get_chat_history_list(self, sid:str, fnCall=None) ->list :
    """
      returns the complete chat history of sid

      usage: chatList=get_chat_history_list('theID',function_to_call)
    """
    chat_history=[]

    cursor=self.db.execute(
      "select * from message_store where session_id=? order by id",
      (sid,)
    )
    # By default, sqlite3 represents each row as a tuple.
    # If a tuple does not suit your needs, you can use
    # the sqlite3.Row class or a custom row_factory.
    for row in cursor.fetchall():
      if fnCall is None:
        chat_history.extend((row['question'], row['answer']))
      else:
        chat_history.extend(fnCall(row['question'], row['answer']))

    return chat_history

  def save_chat_history(self, sid:str, question:str, answer:str):
      """
        insert new data to the chat history

        usage: save_chat_history(sid,'question','answer')
      """
      self.db.execute(
        "insert into message_store (session_id, question, answer) values (?,?,?)",
        (sid, question, answer)
      )

def fn2call(question,answer):
  x=f'({question}, {answer})'
  print('x:',x)
  return x

if __name__ == "__main__":
  print('*** main ***')
  # from utils import download_url, unzip
  import utils as ut
  import os

  chatdb=SqliteChatHistory()

  # chatdb.save_chat_history('1','domanda11','risposta1')
  # chatdb.save_chat_history('1','domanda12','risposta2')
  # chatdb.save_chat_history('2','domanda21','risposta1')

  x=fn2call
  x('uno', 'due')
  print(chatdb.get_chat_history_list('1',fn2call))
  print(chatdb.get_chat_history_list('2'))

  exit(0)

  db_file='legalAI.db'
  if not os.path.exists(db_file):
    if not os.path.exists('legalsqlite.zip'):
      ut.download_url('https://legalai.commonweb.net/shared_datas/legalsqlite.zip')
    ut.unzip('legalsqlite.zip')

  legalai = SqliteDB(db_file)

  df_test=legalai.table_as_pd('test')

  print(df_test)