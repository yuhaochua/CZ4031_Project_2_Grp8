from ast import literal_eval
from collections import OrderedDict
import psycopg2
import copy

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
        try: # try connect to postgresql
            self.connection = psycopg2.connect(
                database = self.database,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.connection.cursor()

        except (Exception, psycopg2.DatabaseError) as error: # catch error
            print(f"Error connecting to PostgreSQL: {error}")

    def execute(self, query):
        try:
            self.cursor.execute(query) # execute SQL query
            results = self.cursor.fetchall()
            return results # return results from SQL query
        
        except (Exception, psycopg2.DatabaseError) as error: # catch error
            print(f"Error executing query: {error}")


    def close(self): # close connection to postgresql
        if self.connection:
            self.cursor.close()
            self.connection.close()


# QEP
def retrieve_query_plan(db_conn, query): # retrieve qep from SQL query
    results = db_conn.execute(query)
    plan = results[0][0][0]
    result = {}

    result["Plan"] = process(plan["Plan"]) # extracting query plan details
    result["Planning Time"] = copy.deepcopy(plan["Planning Time"]) # extracting planning time
    result["Triggers"] = copy.deepcopy(plan["Triggers"]) # triggers used in SQL query
    result["Execution Time"] = copy.deepcopy(plan["Execution Time"]) # extracting execution time of entire query
        
    return result


def process(node):
    result = {}
    result["Node Type"] = copy.deepcopy(node["Node Type"]) # extract the operation done

    # information on buffer
    result["Shared Hit Blocks"] = copy.deepcopy(node["Shared Hit Blocks"]) 
    result["Shared Read Blocks"] = copy.deepcopy(node["Shared Read Blocks"])
    result["Temp Read Blocks"] = copy.deepcopy(node["Temp Read Blocks"])
    result["Temp Written Blocks"] = copy.deepcopy(node["Temp Written Blocks"])

    # different operations will have different details being drawn from the json
    if node["Node Type"] == "Hash Join":
        result["Hash Cond"] = copy.deepcopy(node["Hash Cond"])
        result["Total Cost"] = copy.deepcopy(node["Total Cost"])

    elif node["Node Type"] == "Index Scan":
        result["Parent Relationship"] = copy.deepcopy(node["Parent Relationship"])
        result["Total Cost"] = copy.deepcopy(node["Total Cost"])
        
    elif node["Node Type"] == "Hash":
        result["Parent Relationship"] = copy.deepcopy(node["Parent Relationship"])
        result["Total Cost"] = copy.deepcopy(node["Total Cost"])
        result["Hash Buckets"] = copy.deepcopy(node["Hash Buckets"])
        
    elif node["Node Type"] == "Seq Scan":
        result["Relation Name"] = copy.deepcopy(node["Relation Name"])
        if "Filter" in node.keys():
          result["Filter"] = copy.deepcopy(node["Filter"])
          if "Alias" in node.keys(): # required when alias is used to specify filter condition
            alias = copy.deepcopy(node["Alias"]) 
            result["Filter"] = result["Filter"].replace(alias, result["Relation Name"])

        result["Total Cost"] = copy.deepcopy(node["Total Cost"])
    
    if "Plans" in node.keys(): # check if there are any subtree on this node of the query plan tree
        result["Plans"] = []
        for child in node["Plans"]:
            result["Plans"].append(process(child))

    return result


# Blocks
def retrieve_blocks(db_conn: DBConn, table, filter): # retrieve the pages accessed by sequential scan on specified table
    unique_pages = OrderedDict() # dictionary holding the page numbers accessed

    if filter:
        query = f'SELECT ctid FROM {table} WHERE {filter}'
    else:
        query = f'SELECT ctid FROM {table}'
    
    results = db_conn.execute(query)
    # print()
    
    for ctid in results:
        page_offset,  = ctid # retrieve the tuple containing page + offset
        page, offset = literal_eval(page_offset) # unpack tuple
        unique_pages.setdefault(page)

    pages = list(unique_pages.keys())

    return pages

def retrieve_block(db_conn: DBConn, table, page): # retrieve a particular page accessed by the sequential scan
    query = f'SELECT * FROM {table} WHERE (ctid::text::point)[0] = {page}'

    results = db_conn.execute(query)
    
    return results

