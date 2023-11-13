import psycopg2

DATABASE = "postgres"
USER = "postgres"
PASSWORD = "12345"

# PostGre Connection
class PostgreConnection:
    def __init__(
        self,
        host="localhost",
        port=5432,
        database=DATABASE,
        user=USER,
        password=PASSWORD,
    ):
        self.connection = psycopg2.connect(
            host=host, port=port, database=database, user=user, password=password
        )
        self.cursor = self.connection.cursor()

    def execute(self, query, flags=None):
        if flags != None:
            flag = "set enable_" + flags + " = off;"
            self.cursor.execute(flag)
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        if flags != None:
            flag = "set enable_" + flags + " = on;"
            self.cursor.execute(flag)
        return results

    def close(self):
        self.cursor.close()
        self.connection.close()


# QEP



# Blocks


