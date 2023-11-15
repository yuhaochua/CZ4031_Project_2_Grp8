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
        scrollbar_x = tk.Scrollbar(self.root, orient=tk.HORIZONTAL)
        self.text_widget = tk.Text(self.root, height=50, width=110, wrap=tk.NONE,xscrollcommand=scrollbar_x.set)
        ############################################## label input
        self.label.pack(side=tk.TOP,pady=10)
        self.text.pack(pady=10)
        ############################################# execute and output
        self.ExecuteBtn.pack(pady=5)
        
        ################################################## tree
      # Create a text widget to display the tree structure
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        scrollbar_x.config(command=self.text_widget.xview)
        self.text_widget.pack()
        
        # button2.pack(pady=5)

  def executeQuery(self ,query):
      self.label.config(text="wait abit pls...")
      explainQuery = "explain (analyze, costs, verbose, buffers, format json)\n" + query
      self.data = qep.retrieve_query_plan(self.db_conn, explainQuery)
      
      # Create the tree
      # Create the root node
    #   self.data = json.loads(json_data)
      root = Node("Query Plan")
      self.create_tree(self.data, parent=root)
      self.label.config(text="Executed!")

      self.text_widget.delete(1.0, tk.END)  # Clear previous content
      for pre, _, node in RenderTree(root):
        self.text_widget.insert(tk.END, "%s%s\n" % (pre, node.name))

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
      self.executeQuery(qry)

  # def clearText():
  #     text.delete("1.0", tk.END)
  #     label.config(text="Cleared!")


# Function to create tree structure
  def create_tree(self,data, parent=None):
      arr = []
      if isinstance(data, dict):
          for key, value in data.items():
              if key == "Plans":
                  # arr = value
                  # value = "plan"
                  node = Node(f'{key}: plan', parent=parent)
                  self.create_tree(value, parent=node)
                  
              else:
                  node = Node(f'{key}: {value}', parent=parent)
                  self.create_tree(value, parent=node)
      elif isinstance(data, list):
          for item in data:
              node = Node("", parent=parent)
              self.create_tree(item, parent=node)
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
