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
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Db visualiser")
        # Create a Text widget for multiline input
        self.text = tk.Text(self.root, height=13, width=60)  # Set height and width as needed
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
    self.root = tk.Tk()
    self.root.title("Db visualiser")
    self.text = tk.Text(self.root, height=13, width=60)  # Set height and width as needed
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

    
  def start(self):
      # Start the Tkinter event loop
      self.root.mainloop()


  def processQuery(self):
      # label.config(text="Button 2 Clicked!")
      qry = self.text.get("1.0", tk.END).strip()

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
      result = self.executeQuery(qry)
      plan = result["Plan"]
      root_node = self.create_tree(plan)
      self.draw_tree(canvas, root_node, 400, 50)

      frame.update_idletasks()
      canvas.config(scrollregion=canvas.bbox("all"))

  def on_scroll(self, event):
      self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
class QueryPlanNode:
    def __init__(self, nodeType, cost=None, relation=None, condition=None, children=None):
        self.nodeType = nodeType
        self.cost = cost
        self.relation = relation
        self.condition = condition
        self.children = children or []
        self.level = 1

class Blocks:
    def __init__(self, db_conn: DBConn):
        self.db_conn = db_conn
        self.db_conn.connect()