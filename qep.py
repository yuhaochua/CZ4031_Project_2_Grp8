import json
import copy
from exploration import DBConn

HOST = "localhost"
PORT = 5432
DATABASE = "postgres"
USER = "postgres"
PASSWORD = "CHANGE_HERE"
QUERY = """
explain (analyze, costs, verbose, buffers, format json)
select
      l_orderkey,
      sum(l_extendedprice * (1 - l_discount)) as revenue,
      o_orderdate,
      o_shippriority
    from
      customer,
      orders,
      lineitem
    where
      c_mktsegment = 'BUILDING'
      and c_custkey = o_custkey
      and l_orderkey = o_orderkey
      and o_totalprice > 10
      and l_extendedprice > 10
    group by
      l_orderkey,
      o_orderdate,
      o_shippriority
    order by
      revenue desc,
      o_orderdate;
"""

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

        result["Total Cost"] = copy.deepcopy(node["Total Cost"])
    
    if "Plans" in node.keys():
        result["Plans"] = []
        for child in node["Plans"]:
            result["Plans"].append(process(child))

    return result


if __name__ == "__main__":
    db_conn = DBConn()
    db_conn.connect()
    result = retrieve_query_plan(db_conn, QUERY)
    print(json.dumps(result))
