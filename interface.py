# GUIimport tkinter as tk
import tkinter as tk
from exploration import DBConn
import blocks as blks
import json
from anytree import Node, RenderTree
from anytree.exporter import DotExporter
from PIL import Image, ImageTk
from io import BytesIO
import pydotplus
import qep

class Interface:

  def __init__(self):
        self.db_conn = DBConn()
        self.db_conn.connect()
        self.inputQuery = """
select
      o_year,
      sum(case
        when nation = 'BRAZIL' then volume
        else 0
      end) / sum(volume) as mkt_share
    from
      (
        select
          DATE_PART('YEAR',o_orderdate) as o_year,
          l_extendedprice * (1 - l_discount) as volume,
          n2.n_name as nation
        from
          part,
          supplier,
          lineitem,
          orders,
          customer,
          nation n1,
          nation n2,
          region
        where
          p_partkey = l_partkey
          and s_suppkey = l_suppkey
          and l_orderkey = o_orderkey
          and o_custkey = c_custkey
          and c_nationkey = n1.n_nationkey
          and n1.n_regionkey = r_regionkey
          and r_name = 'AMERICA'
          and s_nationkey = n2.n_nationkey
          and o_orderdate between '1995-01-01' and '1996-12-31'
          and p_type = 'ECONOMY ANODIZED STEEL'
          and s_acctbal > 10
          and l_extendedprice > 100
      ) as all_nations
    group by
      o_year
    order by
      o_year;
      """

        # Create the main window
        self.root = tk.Tk()
        self.root.title("Db visualiser")
        self.photo = None
        # Create a Text widget for multiline input
        self.text = tk.Text(self.root, height=13, width=60)  # Set height and width as needed
        # self.text.insert(tk.END, self.inputQuery)
        # Create an output Text widget
        self.output_text = tk.Text(self.root, height=13, width=60, state=tk.DISABLED)  # Set height and width as needed, initially read-only
        
        # Create a label
        self.label = tk.Label(self.root, text="Input:\n")
        self.labelOut = tk.Label(self.root, text="Output:\n")
        # Create two buttons
        self.ExecuteBtn = tk.Button(self.root, text="Execute", command=self.processQuery)
        # self.clearBtn = tk.Button(root, text="Clear Input", command=self.clearText)
        ############################################## label input
        self.label.pack(side=tk.TOP,pady=10)
        self.text.pack(pady=10)
        ############################################# execute and output
        self.ExecuteBtn.pack(pady=5)
        
        ################################################## tree
      # Create a text widget to display the tree structure
        # self.text_widget.pack()
        
        # button2.pack(pady=5)

  def draw_tree(self, canvas, node, x, y, x_spacing=250, y_spacing=100):
      box = canvas.create_rectangle(x - 100, y - 30, x + 100, y + 30, fill = "white")
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
      if node.nodeType == "Seq Scan":
        canvas.tag_bind(box, "<Enter>", lambda event, node_id=box: self.on_node_enter(event, node_id))
        canvas.tag_bind(box, "<Leave>", lambda event, node_id=box: self.on_node_leave(event, node_id))
        canvas.tag_bind(box, "<Button-1>", lambda event, node=node: self.on_node_click(event, node))
      child_y = y + y_spacing
      for child in node.children:
          if len(node.children) == 1:
              child_x = x
          else:
              child_x = x + x_spacing * (node.children.index(child) - len(node.children) / 4) * (node.level/3)
          canvas.create_line(x, y + 30, child_x, child_y - 30, fill="black")
          self.draw_tree(canvas, child, child_x, child_y, x_spacing, y_spacing)
  def on_node_enter(self, event, node_id):
    # Change cursor on mouse enter
    event.widget.config(cursor="hand2")

  def on_node_leave(self,event, node_id):
    # Change cursor back on mouse leave
    event.widget.config(cursor="")

  def on_node_click(self, event, node):
    # You can customize this function to display content or perform any action
    print(f"Clicked on node: {node.nodeType}")
  def create_tree(self,result):
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
          if "Filter" in result.keys():
            node.condition = result["Filter"]
          node.cost = result["Total Cost"]
      
      if "Plans" in result.keys():
          for child in result["Plans"]:
              expanded_child = self.create_tree(child)
              node.children.append(expanded_child)
              if node.level < expanded_child.level + 1:
                  node.level = expanded_child.level + 1
  
      return node


  def executeQuery(self ,query):
      self.label.config(text="wait abit pls...")
      explainQuery = "explain (analyze, costs, verbose, buffers, format json)\n" + query
      self.data = qep.retrieve_query_plan(self.db_conn, explainQuery)
      


      return self.data

      # Print the tree structure
      # for pre, fill, node in RenderTree(root):
      #   # print(node.name.replace("Plans:",""))
      #   print("%s%s" % (pre, node.name))
        # self.output_text.config(state=tk.NORMAL)  # Set the text widget to editable
        # self.output_text.insert(tk.END, node.name)
        # self.output_text.config(state=tk.DISABLED)  # Set the text widget to read-only
        # print("%s%s" % (pre, node.name))

  def save_input(self):
      user_input = self.text.get("1.0", tk.END)
      with open("Query.txt", "w") as file:
        file.write(user_input)
  def getInput(self):
      return self.text.get("1.0", tk.END)
    
  def start(self):
      # Start the Tkinter event loop



      self.root.mainloop()


  def processQuery(self):
      # label.config(text="Button 2 Clicked!")
      qry = self.text.get("1.0", tk.END).strip()

      # Create a canvas and link it with the scrollbar

    #   frame=tk.Frame(self.root,width=1000,height=100)
    #   frame.pack(expand=True, fill=tk.BOTH) #.grid(row=0,column=0)
    #   canvas=tk.Canvas(frame,bg='#FFFFFF',width=1000,height=200,scrollregion=(-500,-100,500,2000))
    # Create scrollbars for both x and y axes
      scrollbar_y = tk.Scrollbar(self.root, orient="vertical")
      scrollbar_y.pack(side="right", fill="y")

      scrollbar_x = tk.Scrollbar(self.root, orient="horizontal")
      scrollbar_x.pack(side="bottom", fill="x")

    # Create a canvas and link it with the scrollbars
      canvas = tk.Canvas(self.root, xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)
      canvas.pack(side="left", fill="both", expand=True)

    # Link scrollbars to canvas
      scrollbar_x.config(command=canvas.xview)
      scrollbar_y.config(command=canvas.yview)
        # Add content to the canvas
      frame = tk.Frame(canvas)
      canvas.create_window((0, 0), window=frame, anchor="nw")
      # Configure the scrollbar to interact with the canvas
    #   canvas.pack()
      
      result = self.executeQuery(qry)
      plan = result["Plan"]
  
      root_node = self.create_tree(plan)
      self.draw_tree(canvas, root_node, 400, 50)

      frame.update_idletasks()
      canvas.config(scrollregion=canvas.bbox("all"))
     # Enable mouse wheel scrolling on the canvas
    #   canvas.bind_all("<MouseWheel>", self.on_scroll)
    #   return self.executeQuery(qry)

  # def clearText():
  #     text.delete("1.0", tk.END)
  #     label.config(text="Cleared!")

  def on_scroll(self, event):
      self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

# Function to create tree structure
#########################################################################################



  ##########################################################################################


json_data = '''
{
    "Plan": {
        "Node Type": "Aggregate",
        "Plans": [
            {
                "Node Type": "Gather Merge",
                "Plans": [
                    {
                        "Node Type": "Aggregate",
                        "Plans": [
                            {
                                "Node Type": "Sort",
                                "Plans": [
                                    {
                                        "Node Type": "Nested Loop",
                                        "Plans": [
                                            {
                                                "Node Type": "Nested Loop",
                                                "Plans": [
                                                    {
                                                        "Node Type": "Nested Loop",
                                                        "Plans": [
                                                            {
                                                                "Node Type": "Nested Loop",
                                                                "Plans": [
                                                                    {
                                                                        "Node Type": "Hash Join",
                                                                        "Hash Cond": "(orders.o_custkey = customer.c_custkey)",
                                                                        "Total Cost": 40716.15,
                                                                        "Plans": [
                                                                            {
                                                                                "Node Type": "Seq Scan",
                                                                                "Relation Name": "orders",
                                                                                "Total Cost": 35511.0
                                                                            },
                                                                            {
                                                                                "Node Type": "Hash",
                                                                                "Parent Relationship": "Inner",
                                                                                "Total Cost": 4492.32,
                                                                                "Hash Buckets": 32768,
                                                                                "Plans": [
                                                                                    {
                                                                                        "Node Type": "Hash Join",
                                                                                        "Hash Cond": "(customer.c_nationkey = n1.n_nationkey)",
                                                                                        "Total Cost": 4492.32,
                                                                                        "Plans": [
                                                                                            {
                                                                                                "Node Type": "Seq Scan",
                                                                                                "Relation Name": "customer",
                                                                                                "Total Cost": 4229.7
                                                                                            },
                                                                                            {
                                                                                                "Node Type": "Hash",
                                                                                                "Parent Relationship": "Inner",
                                                                                                "Total Cost": 24.29,
                                                                                                "Hash Buckets": 1024,
                                                                                                "Plans": [
                                                                                                    {
                                                                                                        "Node Type": "Hash Join",
                                                                                                        "Hash Cond": "(n1.n_regionkey = region.r_regionkey)",
                                                                                                        "Total Cost": 24.29,
                                                                                                        "Plans": [
                                                                                                            {
                                                                                                                "Node Type": "Seq Scan",
                                                                                                                "Relation Name": "nation",
                                                                                                                "Total Cost": 11.7
                                                                                                            },
                                                                                                            {
                                                                                                                "Node Type": "Hash",
                                                                                                                "Parent Relationship": "Inner",
                                                                                                                "Total Cost": 12.12,
                                                                                                                "Hash Buckets": 1024,
                                                                                                                "Plans": [
                                                                                                                    {
                                                                                                                        "Node Type": "Seq Scan",
                                                                                                                        "Relation Name": "region",
                                                                                                                        "Total Cost": 12.12
                                                                                                                    }
                                                                                                                ]
                                                                                                            }
                                                                                                        ]
                                                                                                    }
                                                                                                ]
                                                                                            }
                                                                                        ]
                                                                                    }
                                                                                ]
                                                                            }
                                                                        ]
                                                                    },
                                                                    {
                                                                        "Node Type": "Index Scan",
                                                                        "Parent Relationship": "Inner",
                                                                        "Total Cost": 1.96
                                                                    }
                                                                ]
                                                            },
                                                            {
                                                                "Node Type": "Index Scan",
                                                                "Parent Relationship": "Inner",
                                                                "Total Cost": 0.44
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "Node Type": "Index Scan",
                                                        "Parent Relationship": "Inner",
                                                        "Total Cost": 0.31
                                                    }
                                                ]
                                            },
                                            {
                                                "Node Type": "Memoize",
                                                "Plans": [
                                                    {
                                                        "Node Type": "Index Scan",
                                                        "Parent Relationship": "Outer",
                                                        "Total Cost": 0.17
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    },
    "Planning Time": 28.775,
    "Triggers": [],
    "Execution Time": 3795.251
}
    '''
class QueryPlanNode:
    def __init__(self, nodeType, cost=None, relation=None, condition=None, children=None):
        self.nodeType = nodeType
        self.cost = cost
        self.relation = relation
        self.condition = condition
        self.children = children or []
        self.level = 1


def main(self):
    root = tk.Tk()
    root.title("Query Plan Tree")

    canvas = tk.Canvas(root, width=2000, height=2000)
    canvas.pack()
    
    json_string = '''{"Plan": {"Node Type": "Sort", "Plans": [{"Node Type": "Aggregate", "Plans": [{"Node Type": "Gather Merge", "Plans": [{"Node Type": "Aggregate", "Plans": [{"Node Type": "Sort", "Plans": [{"Node Type": "Hash Join", "Hash Cond": "(lineitem.l_orderkey = orders.o_orderkey)", "Total Cost": 197052.4, "Plans": [{"Node Type": "Seq Scan", "Relation Name": "lineitem", "Filter": "(lineitem.l_extendedprice > '10'::numeric)", "Total Cost": 143857.55}, {"Node Type": "Hash", "Parent Relationship": "Inner", "Total Cost": 40128.41, "Hash Buckets": 524288, "Plans": [{"Node Type": "Hash Join", "Hash Cond": "(orders.o_custkey = customer.c_custkey)", "Total Cost": 40128.41, "Plans": [{"Node Type": "Seq Scan", "Relation Name": "orders", "Filter": "(orders.o_totalprice > '10'::numeric)", "Total Cost": 33948.5}, {"Node Type": "Hash", "Parent Relationship": "Inner", "Total Cost": 4381.25, "Hash Buckets": 32768, "Plans": [{"Node Type": "Seq Scan", "Relation Name": "customer", "Filter": "(customer.c_mktsegment = 'BUILDING'::bpchar)", "Total Cost": 4381.25}]}]}]}]}]}]}]}]}]}, "Planning Time": 6.528, "Triggers": [], "Execution Time": 2649.252}'''
    result = json.loads(json_string)
    plan = result["Plan"]

    root_node = self.create_tree(plan)
    draw_tree(canvas, root_node, 400, 50)

    root.mainloop()

if __name__ == "__main__":
    main()