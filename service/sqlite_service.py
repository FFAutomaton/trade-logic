import sqlite3


class SqlLite_Service:
    def __init__(self):
        self.conn =None
        self.conn = self.get_conn()

    def get_conn(self, db_name):
        if self.conn:
            return self.conn
        self.conn = sqlite3.connect(f'./coindata/{db_name}.db')
        return self.conn
