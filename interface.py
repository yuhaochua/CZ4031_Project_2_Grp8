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


class Interface:

  def __init__(self):
        self.defaultQry = "select *\nfrom lineitem\nWHERE (l_shipdate >= '1995-01-01') AND (l_shipdate <= '1996-12-31')"

        # Create the main window
        self.root = tk.Tk()
        self.root.title("Db visualiser")
        self.photo = None
        # Create a Text widget for multiline input
        self.text = tk.Text(self.root, height=13, width=60)  # Set height and width as needed
        self.text.insert(tk.END, self.defaultQry)
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

          # Pack the label and buttons into the window
        ############################################## label input
        self.label.pack(side=tk.TOP,pady=10)
        self.text.pack(pady=10)
        ############################################# execute and output
        self.ExecuteBtn.pack(pady=5)
        # clearBtn.pack(pady=5)
        # Display the image in a label
        # self.labelOut.pack(side=tk.TOP,pady=10)
        # self.output_text.pack(pady=5)
        ################################################## tree
      # Create a text widget to display the tree structure
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        scrollbar_x.config(command=self.text_widget.xview)
        self.text_widget.pack()
        
        # button2.pack(pady=5)

  def executeQuery(self ,query):
      # self.output_text.config(state=tk.NORMAL)  # Set the text widget to editable
      # self.output_text.delete("1.0", tk.END) # Clear previous content
      # self.output_text.insert(tk.END, query)  # Insert input text
      # self.output_text.config(state=tk.DISABLED)  # Set the text widget to read-only
      self.label.config(text="wait abit pls...")
      # db = DBConn()
      # db.__init__()
      # db.connect()
      # Create the tree
      # Create the root node
      root = Node("Query Plan")
      self.create_tree(self.data, parent=root)
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

      
      
      # db.execute(query)


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

  json_data = '''
    {
        "Plan": {
            "Node Type": "Sort",
            "Plans": [
                {
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
                                                    "Node Type": "Hash Join",
                                                    "Hash Cond": "(lineitem.l_orderkey = orders.o_orderkey)",
                                                    "Total Cost": 197052.4,
                                                    "Plans": [
                                                        {
                                                            "Node Type": "Seq Scan",
                                                            "Relation Name": "lineitem",
                                                            "Total Cost": 143857.55
                                                        },
                                                        {
                                                            "Node Type": "Hash",
                                                            "Parent Relationship": "Inner",
                                                            "Total Cost": 40128.41,
                                                            "Hash Buckets": 524288,
                                                            "Plans": [
                                                                {
                                                                    "Node Type": "Hash Join",
                                                                    "Hash Cond": "(orders.o_custkey = customer.c_custkey)",
                                                                    "Total Cost": 40128.41,
                                                                    "Plans": [
                                                                        {
                                                                            "Node Type": "Seq Scan",
                                                                            "Relation Name": "orders",
                                                                            "Total Cost": 33948.5
                                                                        },
                                                                        {
                                                                            "Node Type": "Hash",
                                                                            "Parent Relationship": "Inner",
                                                                            "Total Cost": 4381.25,
                                                                            "Hash Buckets": 32768,
                                                                            "Plans": [
                                                                                {
                                                                                    "Node Type": "Seq Scan",
                                                                                    "Relation Name": "customer",
                                                                                    "Total Cost": 4381.25
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
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        "Planning Time": 2.721,
        "Triggers": [],
        "Execution Time": 1456.844
    }
    '''
  data = json.loads(json_data)

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




  ##########################################################################################

