from exploration import DBConn
from collections import OrderedDict
from ast import literal_eval

### translate SQL query
def retrieve_blocks(db_conn: DBConn, table, filter):
    blocks = []
    unique_pages = OrderedDict()

    if filter:
        query = f'SELECT ctid FROM {table} WHERE {filter}'
    
        results = db_conn.execute(query)
        # print()
        
        for ctid in results:
            page_offset,  = ctid # retrieve the tuple containing page + offset
            page, offset = literal_eval(page_offset) # unpack tuple
            unique_pages.setdefault(page)

        pages = list(unique_pages.keys())
        print(len(pages))
        
        count = 1
        for page in pages:
            block = retrieve_block(db_conn, table, page)
            print(count)
            count += 1
            blocks.append(block)
    
    else:
        current_page = 0
        query = f'SELECT ctid, * FROM {table}'
        results = db_conn.execute(query)

        block = []
        for ctid in results:
            page_offset, *record = ctid
            page, offset = literal_eval(page_offset) # unpack tuple
            if page != current_page:
                blocks.append(block)
                block = []
                current_page = page
            block.append(record)
        
        blocks.append(block)

    return blocks

def retrieve_block(db_conn: DBConn, table, page):
    # block = []

    query = f'SELECT * FROM {table} WHERE (ctid::text::point)[0] = {page}'

    results = db_conn.execute(query)
    
    return results

if __name__ == "__main__":
    db_conn = DBConn()
    db_conn.connect()
    # query = "select ctid from lineitem WHERE (l_shipdate >= '1995-01-01') AND (l_shipdate <= '1996-12-31') LIMIT 60"
    table = "customer"
    filter = "customer.c_acctbal > 10"
    # filter = None
    blocks = retrieve_blocks(db_conn, table, filter)
    print(len(blocks))
    # for block in blocks:
        # print(block[0]) # if you only wan the first tuple of each block
        # print(block) # if you wan the full content of each block