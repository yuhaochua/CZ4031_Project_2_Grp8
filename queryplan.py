import tkinter as tk
import json

class QueryPlanNode:
    def __init__(self, nodeType, cost=None, relation=None, condition=None, children=None):
        self.nodeType = nodeType
        self.cost = cost
        self.relation = relation
        self.condition = condition
        self.children = children or []

def draw_tree(canvas, node, x, y, x_spacing=250, y_spacing=100):
    canvas.create_rectangle(x - 100, y - 30, x + 100, y + 30)
    if node.relation:
        canvas.create_text(x, y-20, text=node.nodeType)
        canvas.create_text(x, y, text=f'Relation: {node.relation}')
        canvas.create_text(x, y+20, text=f'Cost: {node.cost}')
    elif node.condition:
        canvas.create_text(x, y-20, text=node.nodeType)
        canvas.create_text(x, y, text=f'Condition: {node.condition}')
        canvas.create_text(x, y+20, text=f'Cost: {node.cost}')
    elif node.cost:
        canvas.create_text(x, y-20, text=node.nodeType)
        canvas.create_text(x, y, text=f'Cost: {node.cost}')
    else:
        canvas.create_text(x, y, text=node.nodeType)

    child_y = y + y_spacing
    for child in node.children:
        if len(node.children) == 1:
            child_x = x
        else:
            child_x = x + x_spacing * (node.children.index(child) - len(node.children) / 4)
        canvas.create_line(x, y + 30, child_x, child_y - 30, fill="black")
        draw_tree(canvas, child, child_x, child_y, x_spacing, y_spacing)

def create_tree(result):
    node = QueryPlanNode(nodeType=result["Node Type"])

    if result["Node Type"] == "Hash Join":
        node.condition = result["Hash Cond"]
        node.cost = result["Total Cost"]

    elif result["Node Type"] == "Index Scan":
        node.cost = result["Total Cost"]
        
    elif result["Node Type"] == "Hash":
        node.cost = result["Total Cost"]
        

    elif result["Node Type"] == "Seq Scan":
        node.relation = result["Relation Name"]
        node.condition = result["Filter"]
        node.cost = result["Total Cost"]
    
    if "Plans" in result.keys():
        for child in result["Plans"]:
            node.children.append(create_tree(child))

    return node

def main():
    root = tk.Tk()
    root.title("Query Plan Tree")

    canvas = tk.Canvas(root, width=2000, height=2000)
    canvas.pack()
    
    json_string = '''{"Plan": {"Node Type": "Sort", "Plans": [{"Node Type": "Aggregate", "Plans": [{"Node Type": "Gather Merge", "Plans": [{"Node Type": "Aggregate", "Plans": [{"Node Type": "Sort", "Plans": [{"Node Type": "Hash Join", "Hash Cond": "(lineitem.l_orderkey = orders.o_orderkey)", "Total Cost": 197052.4, "Plans": [{"Node Type": "Seq Scan", "Relation Name": "lineitem", "Filter": "(lineitem.l_extendedprice > '10'::numeric)", "Total Cost": 143857.55}, {"Node Type": "Hash", "Parent Relationship": "Inner", "Total Cost": 40128.41, "Hash Buckets": 524288, "Plans": [{"Node Type": "Hash Join", "Hash Cond": "(orders.o_custkey = customer.c_custkey)", "Total Cost": 40128.41, "Plans": [{"Node Type": "Seq Scan", "Relation Name": "orders", "Filter": "(orders.o_totalprice > '10'::numeric)", "Total Cost": 33948.5}, {"Node Type": "Hash", "Parent Relationship": "Inner", "Total Cost": 4381.25, "Hash Buckets": 32768, "Plans": [{"Node Type": "Seq Scan", "Relation Name": "customer", "Filter": "(customer.c_mktsegment = 'BUILDING'::bpchar)", "Total Cost": 4381.25}]}]}]}]}]}]}]}]}]}, "Planning Time": 6.528, "Triggers": [], "Execution Time": 2649.252}'''
    result = json.loads(json_string)
    plan = result["Plan"]

    root_node = create_tree(plan)
    draw_tree(canvas, root_node, 400, 50)

    root.mainloop()

if __name__ == "__main__":
    main()