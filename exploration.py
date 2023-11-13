import psycopg2

HOST = "localhost"
PORT = 5432
DATABASE = "postgres"
USER = "postgres"
PASSWORD = "12345"

# PostGre Connection
class DBConn:
    def __init__(self,host=HOST,port=PORT,database=DATABASE,user=USER,password=PASSWORD):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.connection.cursor()

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error connecting to PostgreSQL: {error}")

    def execute(self, query):
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return results
        
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error executing query: {error}")


    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()


# QEP



# Blocks


