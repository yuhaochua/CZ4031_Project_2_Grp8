# GUIimport tkinter as tk
from ast import literal_eval
from collections import OrderedDict
import tkinter as tk
from exploration import DBConn
import json
import exploration

class Interface:

  def __init__(self):
        self.db_conn = DBConn()
        self.db_conn.connect()
        # Create the main window
        self.root = tk.Tk()
        self.root.geometry("1600x800")
        self.root.title("Db visualiser")
        # Create a Text widget for multiline input
        self.text = tk.Text(self.root, height=13, width=60)  # Set height and width as needed
        self.outputText = tk.Text(self.root, height=5, width=35)  # Set height and width as needed
        self.outputText.config(state=tk.DISABLED)


        # Create a label
        self.label = tk.Label(self.root, text="Input:\n")
        self.labelOut = tk.Label(self.root, text="Output:\n")
        # Create two buttons
        self.ExecuteBtn = tk.Button(self.root, text="Execute", command=self.processQuery)
        # self.clearBtn = tk.Button(root, text="Clear Input", command=self.clearText)
        ############################################## label input
        self.label.pack(side=tk.TOP,pady=10)
        self.text.pack(pady=10)
        # self.outputText.place(relx=0.2, rely=0.1, anchor="ne", x=-10, y=10)
        self.outputText.place(relx=0.9, rely=0.1, anchor="ne", x=-10, y=10)

        # self.outputText.pack(side="left",pady=10)
        ############################################# execute and output
        self.ExecuteBtn.pack(pady=5)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
  def on_close(self):
      self.db_conn.close()
      self.root.destroy()
  
  def draw_tree(self, canvas, node, x, y, x_spacing=250, y_spacing=120):
      box = canvas.create_rectangle(x - 100, y - 30, x + 100, y + 50, fill = "white")
      if node.relation:
          canvas.create_text(x, y-20, text=node.nodeType)
          canvas.create_text(x, y, text=f'Relation: {node.relation}')
          canvas.create_text(x, y+20, text=f'Cost: {node.cost}')
          if node.condition:
            canvas.create_text(x, y+40, text=f'Condition: {node.condition}')
      elif node.condition:
          canvas.create_text(x, y-20, text=node.nodeType)
          canvas.create_text(x, y, text=f'Condition: {node.condition}')
          canvas.create_text(x, y+20, text=f'Cost: {node.cost}')
      elif node.cost:
          canvas.create_text(x, y-20, text=node.nodeType)
          canvas.create_text(x, y, text=f'Cost: {node.cost}')
      else:
          canvas.create_text(x, y, text=node.nodeType)

      popup_window = tk.Toplevel(self.root)
      popup_window.withdraw()
      popup_label = tk.Label(popup_window)
      popup_label.pack()
      buffer = f"Shared Hit: {node.sharedHit}\n Shared Read: {node.sharedRead}\n Temp Read: {node.tempRead}\n Temp Written: {node.tempWritten}"

      canvas.tag_bind(box, "<Leave>", lambda event: self.on_node_leave(event, popup_window))
      canvas.tag_bind(box, "<Enter>", lambda event, node_id=box: self.on_node_enter(event, node_id, popup_window, popup_label, buffer, hasBlocks=(node.nodeType == "Seq Scan")))
      if node.nodeType == "Seq Scan":
        canvas.tag_bind(box, "<Button-1>", lambda event, node=node: self.on_node_click(event, node))
      child_y = y + y_spacing
      for child in node.children:
          if len(node.children) == 1:
              child_x = x
          else:
              child_x = x + x_spacing * (node.children.index(child) - len(node.children) / 4) * (node.level/3)
          canvas.create_line(x, y + 50, child_x, child_y - 30, fill="black")
          self.draw_tree(canvas, child, child_x, child_y, x_spacing, y_spacing)

  def on_node_enter(self, event, node_id, popup_window, popup_label, buffer, hasBlocks=False):
    # Change cursor on mouse enter
    if hasBlocks:
        event.widget.config(cursor="hand2")
    x, y, _, _ = event.widget.coords(node_id)
    popup_window.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
    popup_label.config(text=buffer)
    popup_window.deiconify()

  def on_node_leave(self,event, popup_window):
    # Change cursor back on mouse leave
    event.widget.config(cursor="")
    popup_window.withdraw()

  def on_node_click(self, event, node):
    # self.root = tk.Tk()
    # self.root.title("Db visualiser")
    # self.text = tk.Text(self.root, height=13, width=60)  # Set height and width as needed
    # You can customize this function to display content or perform any action
    print(f"Clicked on node: {node.nodeType}")
    blocks = exploration.retrieve_blocks(self.db_conn, node.relation, node.condition)
    buffer = Blocks(self.db_conn, node.relation, blocks)
    buffer.start()

  def create_tree(self,result):
      node = QueryPlanNode(nodeType=result["Node Type"], 
                           sharedHit=result["Shared Hit Blocks"], 
                           sharedRead=result["Shared Read Blocks"], 
                           tempRead=result["Temp Read Blocks"],
                           tempWritten=result["Temp Written Blocks"])
  
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
      self.label.config(text="Executed")
      explainQuery = "explain (analyze, costs, verbose, buffers, format json)\n" + query
      self.data = exploration.retrieve_query_plan(self.db_conn, explainQuery)
      print(self.data["Planning Time"])
      print(self.data["Execution Time"])
      
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

      canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(-int(event.delta / 120), "units"))
      canvas.bind("<Shift MouseWheel>", lambda event: canvas.xview_scroll(-int(event.delta / 120), "units"))

      result = self.executeQuery(qry)

      planTime = result["Planning Time"]
      exeTime = result["Execution Time"]
      self.outputText.config(state=tk.NORMAL)
      self.outputText.delete("1.0", tk.END)
      self.outputText.insert(tk.END, f"Planning Time: {planTime}\n")
      self.outputText.insert(tk.END, f"Execution Time: {exeTime}\n")

      plan = result["Plan"]
      root_node = self.create_tree(plan)
      self.draw_tree(canvas, root_node, 400, 50)

      frame.update_idletasks()
      canvas.config(scrollregion=canvas.bbox("all"))


class QueryPlanNode:
    def __init__(self, nodeType, sharedHit, sharedRead, tempRead, tempWritten, cost=None, relation=None, condition=None, children=None):
        self.nodeType = nodeType
        self.cost = cost
        self.relation = relation
        self.condition = condition
        self.sharedHit = sharedHit
        self.sharedRead = sharedRead
        self.tempRead = tempRead
        self.tempWritten = tempWritten
        self.children = children or []
        self.level = 1

class Blocks:
    def __init__(self, db_conn: DBConn, relation, pages):
        self.db_conn = db_conn
        # self.db_conn.connect()
        # self.node = node
        # blocks = self.retrieve_blocks(self.node.relation, self.node.condition)
        self.pages = pages
        self.relation = relation
        self.pageStartIndex = 0

        self.root = tk.Tk()
        self.root.geometry("1400x400")
        self.root.title("Blocks Accessed")
        self.tuplesText = None # String that says Tuples in Block:
        self.tupleText = None # String that says Tuple:
        self.drawnBlocks = [] # What blocks have been drawn
        self.drawnBlocksText = [] # Block ID drawn on the blocks
        self.tuples = [] # what tuples have been drawn
        self.tupleNums = [] # tuple id drawn on the blocks
        self.tupleRows = 0 # so that we know where to print the tuple
        self.root.focus_force()

        scrollbar_y = tk.Scrollbar(self.root, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x = tk.Scrollbar(self.root, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")
        self.canvas = tk.Canvas(self.root, xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar_x.config(command=self.canvas.xview)
        scrollbar_y.config(command=self.canvas.yview)
            # Add content to the canvas
        self.frame = tk.Frame(self.canvas)
        
        self.canvas.create_window((0, 0), window=self.frame, anchor="center")

        self.canvas.bind("<MouseWheel>", lambda event: self.canvas.yview_scroll(-int(event.delta / 120), "units"))
        self.canvas.bind("<Shift MouseWheel>", lambda event: self.canvas.xview_scroll(-int(event.delta / 120), "units"))

        
        self.previousBtn = tk.Button(self.canvas, text="PREVIOUS", command=self.previous_set_blocks, state=tk.DISABLED)
        self.previousBtn.place(x=150, y=250)

        if len(self.pages) > 50:
            self.nextBtn = tk.Button(self.canvas, text="NEXT", command=lambda: self.next_set_blocks(offset=50), state=tk.NORMAL)
        else:
            self.nextBtn = tk.Button(self.canvas, text="NEXT", command=lambda: self.next_set_blocks(offset=50), state=tk.DISABLED)
        self.nextBtn.place(x=250, y=250)

        self.blocks = None
        self.next_set_blocks()
        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))


    def start(self):
        self.root.mainloop()

    def draw_blocks(self, x, y, pageStart):
        level = 0
        self.canvas.create_text(x-100, y, text='Blocks Accessed: ')
        for blkNum in range(pageStart, pageStart + len(self.blocks)):
            modBlk = blkNum % 10
            block = self.canvas.create_rectangle(x-20+modBlk*40, y-20+level*40, x+20+modBlk*40, y+20+level*40, fill = "white")
            self.drawnBlocks.append(block)
            text = self.canvas.create_text(x+modBlk*40, y+level*40, text=f'{blkNum}')
            self.drawnBlocksText.append(text)
            self.canvas.tag_bind(block, "<Enter>", lambda event, block_id=block: self.on_block_enter(event, block_id))
            self.canvas.tag_bind(block, "<Leave>", lambda event, block_id=block: self.on_block_leave(event, block_id))
            self.canvas.tag_bind(block, "<Button-1>", lambda event, block_id=block, blkNum=blkNum: self.on_block_click(event, block_id, blkNum, x, y))


            if(modBlk == 9):
                level += 1 # start drawing blocks on next level

        
    def next_set_blocks(self, offset=0):
        self.clear_blocks()
        self.clear_tuples()
        if self.pageStartIndex > 0:
            self.previousBtn['state'] = tk.NORMAL
        
        self.pageStartIndex += offset
        
        blocks = []
        count = 1
        for page in self.pages[self.pageStartIndex:]:
            blocks.append(exploration.retrieve_block(self.db_conn, self.relation, page))
            count += 1
            if count > 50:
                break
        
        if count > 50: # so that the blocks count correctly
            count -= 1


        if self.pageStartIndex + count >= len(self.pages): # last possible set of blocks
            self.nextBtn['state'] = tk.DISABLED

        self.blocks = blocks.copy()
        self.draw_blocks(200, 50, self.pageStartIndex)


    def previous_set_blocks(self):
        self.clear_blocks()
        self.clear_tuples()

        self.pageStartIndex -= 50
        print(self.pageStartIndex)
        if self.pageStartIndex <= 0:
            self.previousBtn['state'] = tk.DISABLED
        if self.nextBtn['state'] == tk.DISABLED:
            self.nextBtn['state'] = tk.NORMAL

        blocks = []
        count = 1
        for page in self.pages[self.pageStartIndex:]:
            blocks.append(exploration.retrieve_block(self.db_conn, self.relation, page))
            count += 1
            if count > 50:
                break
        

        self.blocks = blocks.copy()
        self.draw_blocks(200, 50, self.pageStartIndex)

    
    def on_block_enter(self, event, block_id):
        # Change cursor on mouse enter
        event.widget.config(cursor="hand2")
        self.canvas.itemconfig(block_id, fill="lightblue")
        x, y, _, _ = event.widget.coords(block_id)

    def on_block_leave(self, event, block_id):
        # Change cursor back on mouse leave
        self.canvas.itemconfig(block_id, fill="white")
        event.widget.config(cursor="")

    def on_block_click(self, event, block_id, blkNum, x, y):
        self.clear_tuples() # clear the tuple drawings

        x += 500
        self.tuplesText = self.canvas.create_text(x, y, text=f'Tuples in Block {blkNum}: ')
        x += 100
        level = 0
        for tupleNum in range(len(self.blocks[blkNum%50])):
            modTuple = tupleNum % 10
            tuple = self.canvas.create_rectangle(x-20+modTuple*40, y-20+level*40, x+20+modTuple*40, y+20+level*40, fill = "white")
            self.tuples.append(tuple) # Keep track of what tuples are being drawn
            tupleNumber = self.canvas.create_text(x+modTuple*40, y+level*40, text=f'{tupleNum}')
            self.tupleNums.append(tupleNumber) # Keep track of what tuples are being drawn

            self.canvas.tag_bind(tuple, "<Enter>", lambda event, tuple_id=tuple: self.on_tuple_enter(event, tuple_id))
            self.canvas.tag_bind(tuple, "<Leave>", lambda event, tuple_id=tuple: self.on_tuple_leave(event, tuple_id))
            self.canvas.tag_bind(tuple, "<Button-1>", lambda event, tuple_id=tuple, blkNum=blkNum, tupleNum=tupleNum: self.on_tuple_click(event, tuple_id, blkNum, tupleNum, x-100, y))

            if(modTuple == 9):
                level += 1 # start drawing blocks on next level
        
        self.tupleRows = level + 1
        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def on_tuple_enter(self, event, tuple_id):
        # Change cursor on mouse enter
        event.widget.config(cursor="hand2")
        self.canvas.itemconfig(tuple_id, fill="lightgreen")
        x, y, _, _ = event.widget.coords(tuple_id)

    def on_tuple_leave(self, event, tuple_id):
        # Change cursor back on mouse leave
        self.canvas.itemconfig(tuple_id, fill="white")
        event.widget.config(cursor="")

    def on_tuple_click(self, event, tuple_id, blkNum, tupleNum, x, y):
        if self.tupleText:
            self.canvas.delete(self.tupleText)
        y += self.tupleRows * 40
        self.tupleText = self.canvas.create_text(x, y, anchor='w', text=f'Tuple {tupleNum}: {self.blocks[blkNum%50][tupleNum]}')
        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
    def clear_tuples(self):
        if self.tuplesText:
            self.canvas.delete(self.tuplesText)
        for tuple in self.tuples:
            self.canvas.delete(tuple)
        for tupleNum in self.tupleNums:
            self.canvas.delete(tupleNum)
        if self.tupleText:
            self.canvas.delete(self.tupleText)

        self.tuples = []
        self.tupleNums = []

    def clear_blocks(self):
        for drawn in self.drawnBlocks:
            self.canvas.delete(drawn)
        for text in self.drawnBlocksText:
            self.canvas.delete(text)

        self.drawnBlocks = []
        self.drawnBlocksText = []

