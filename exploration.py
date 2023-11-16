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
        try:
            self.connection = psycopg2.connect(
                database = self.database,
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
def retrieve_query_plan(db_conn, query):
    results = db_conn.execute(query)
    plan = results[0][0][0]
    result = {}

    result["Plan"] = process(plan["Plan"])
    result["Planning Time"] = copy.deepcopy(plan["Planning Time"])
    result["Triggers"] = copy.deepcopy(plan["Triggers"])
    result["Execution Time"] = copy.deepcopy(plan["Execution Time"])
        
    return result


def process(node):
    result = {}
    result["Node Type"] = copy.deepcopy(node["Node Type"])
    result["Shared Hit Blocks"] = copy.deepcopy(node["Shared Hit Blocks"])
    result["Shared Read Blocks"] = copy.deepcopy(node["Shared Read Blocks"])
    result["Temp Read Blocks"] = copy.deepcopy(node["Temp Read Blocks"])
    result["Temp Written Blocks"] = copy.deepcopy(node["Temp Written Blocks"])

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
          if "Alias" in node.keys():
            alias = copy.deepcopy(node["Alias"])
            result["Filter"] = result["Filter"].replace(alias, result["Relation Name"])

        result["Total Cost"] = copy.deepcopy(node["Total Cost"])
    
    if "Plans" in node.keys():
        result["Plans"] = []
        for child in node["Plans"]:
            result["Plans"].append(process(child))

    return result


# Blocks
def retrieve_blocks(db_conn: DBConn, table, filter):
    blocks = []
    unique_pages = OrderedDict()

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
    print(len(pages))

    return pages
    
    # else:
    #     print("no filter")
    #     current_page = 0
    #     query = f'SELECT ctid, * FROM {table}'
    #     print(query)
    #     results = self.db_conn.execute(query)
    #     print(results)

    #     block = []
    #     for ctid in results:
    #         page_offset, *record = ctid
    #         page, offset = literal_eval(page_offset) # unpack tuple
    #         if page != current_page:
    #             blocks.append(block)
    #             block = []
    #             current_page = page
    #         print(record)
    #         block.append(record)
    
    #     blocks.append(block)

    # return blocks
    

def retrieve_block(db_conn: DBConn, table, page):
    query = f'SELECT * FROM {table} WHERE (ctid::text::point)[0] = {page}'

    results = db_conn.execute(query)
    
    return results

