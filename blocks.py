from exploration import DBConn
from collections import OrderedDict
from ast import literal_eval

### translate SQL query
def retrieve_blocks(db_conn: DBConn, table, filter):
    blocks = []
    unique_pages = OrderedDict()

    query = f'SELECT ctid FROM {table} WHERE {filter} LIMIT 50'
    results = db_conn.execute(query)
    print()
    
    for ctid in results:
        page_offset,  = ctid # retrieve the tuple containing page + offset
        page, offset = literal_eval(page_offset) # unpack tuple
        unique_pages.setdefault(page)

    pages = list(unique_pages.keys())
    print(pages)
        
    for page in pages:
        block = retrieve_block(db_conn, table, page)
        blocks.append(block)

    return blocks

def retrieve_block(db_conn: DBConn, table, page):
    # block = []

    query = f'SELECT * FROM {table} WHERE (ctid::text::point)[0] = {page}'

    results = db_conn.execute(query)
    
    return results
    # return block

if __name__ == "__main__":
    db_conn = DBConn()
    db_conn.connect()
    # query = "select ctid from lineitem WHERE (l_shipdate >= '1995-01-01') AND (l_shipdate <= '1996-12-31') LIMIT 60"
    table = "lineitem"
    filter = "(l_shipdate >= '1995-01-01') AND (l_shipdate <= '1996-12-31')"
    blocks = retrieve_blocks(db_conn, table, filter)
    print(len(blocks))
    for block in blocks:
        print(block[0]) # if you only wan the first tuple of each block
        # print(block) # if you wan the full content of each block