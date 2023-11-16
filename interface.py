# GUIimport tkinter as tk
import tkinter as tk
from exploration import DBConn
import exploration

class Interface:

    def __init__(self):
        self.db_conn = DBConn()
        self.db_conn.connect()

        # create the main window
        self.root = tk.Tk()
        self.root.geometry("1600x800")
        self.root.title("Db visualiser")

        # create a Text widget for multiline input
        self.text = tk.Text(self.root, height=13, width=60) 
        self.outputText = tk.Text(self.root, height=5, width=35)
        self.outputText.config(state=tk.DISABLED)

        # create a label for instructions
        self.label = tk.Label(self.root, text="Enter SQL query to generate QEP:\n")

        # create button to execute SQL query
        self.ExecuteBtn = tk.Button(self.root, text="Execute", command=self.processQuery)

        # organise the different components
        self.label.pack(side=tk.TOP,pady=10)
        self.text.pack(pady=10)
        self.outputText.place(relx=0.9, rely=0.1, anchor="ne", x=-10, y=10)
        self.ExecuteBtn.pack(pady=5)

        # logic for graceful shutdown
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start(self):
        # start the Tkinter event loop
        self.root.mainloop()
        
    def on_close(self):
        self.db_conn.close() # close connection to db
        self.root.destroy() # destroy the tkinter root
  
    # draw the nodes and lines which form the query plan tree
    def draw_tree(self, canvas, node, x, y, x_spacing=250, y_spacing=120):
        box = canvas.create_rectangle(x - 100, y - 30, x + 100, y + 50, fill = "white")

        # depending on the fields that the node contains, we create different texts for the node
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

        # window that appears on hover over nodes, to display buffer information
        popup_window = tk.Toplevel(self.root)
        popup_window.withdraw()
        popup_label = tk.Label(popup_window)
        popup_label.pack()
        buffer = f"Shared Hit: {node.sharedHit}\n Shared Read: {node.sharedRead}\n Temp Read: {node.tempRead}\n Temp Written: {node.tempWritten}"

        # bind events for hovering over nodes
        canvas.tag_bind(box, "<Leave>", lambda event: self.on_node_leave(event, popup_window))
        canvas.tag_bind(box, "<Enter>", lambda event, node_id=box: self.on_node_enter(event, node_id, popup_window, popup_label, buffer, hasBlocks=(node.nodeType == "Seq Scan")))

        # bind clickable event on seq scan nodes to display new window for blocks accessed
        if node.nodeType == "Seq Scan":
            canvas.tag_bind(box, "<Button-1>", lambda event, node=node: self.on_node_click(event, node))
        
        # draw the children of a particular node
        child_y = y + y_spacing
        for child in node.children:
            if len(node.children) == 1:
                child_x = x
            else:
                child_x = x + x_spacing * (node.children.index(child) - len(node.children) / 4) * (node.level/3)
            canvas.create_line(x, y + 50, child_x, child_y - 30, fill="black")
            self.draw_tree(canvas, child, child_x, child_y, x_spacing, y_spacing)

    def on_node_enter(self, event, node_id, popup_window, popup_label, buffer, hasBlocks=False):
        # change cursor on mouse enter
        if hasBlocks:
            event.widget.config(cursor="hand2")
        x, y, _, _ = event.widget.coords(node_id)

        # make window for buffer info appear
        popup_window.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        popup_label.config(text=buffer)
        popup_window.deiconify()

    def on_node_leave(self,event, popup_window):
        # Change cursor back on mouse leave
        event.widget.config(cursor="")

        # make window for buffer info disappear
        popup_window.withdraw()

    def on_node_click(self, event, node): # open window for blocks accessed once the seq scan node is clicked
        # retrieve the pages accessed by the seq scan
        blocks = exploration.retrieve_blocks(self.db_conn, node.relation, node.condition)

        # initiliase the blocks window for this seq scan
        buffer = Blocks(self.db_conn, node.relation, blocks)
        # open the window
        buffer.start()

    # create nodes and children based on the json formatted query plan
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
        
        # append children nodes to current node
        if "Plans" in result.keys():
            for child in result["Plans"]:
                expanded_child = self.create_tree(child)
                node.children.append(expanded_child)
                # update the level on which this node is at
                if node.level < expanded_child.level + 1:
                    node.level = expanded_child.level + 1
        return node


    def executeQuery(self ,query):
        # calls exploration.retrieve_query_plan to get json data
        self.label.config(text="Executed!")
        explainQuery = "explain (analyze, costs, verbose, buffers, format json)\n" + query

        # store the generated query plan json 
        self.data = exploration.retrieve_query_plan(self.db_conn, explainQuery)

        return self.data

    def processQuery(self): # function that is being called when execute button is clicked
        # parse SQL query
        qry = self.text.get("1.0", tk.END).strip()

        # initialise scrollbars
        scrollbar_y = tk.Scrollbar(self.root, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x = tk.Scrollbar(self.root, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")

        # create a canvas and link it with the scrollbars
        canvas = tk.Canvas(self.root, xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)
        canvas.pack(side="left", fill="both", expand=True)

        # link scrollbars to canvas
        scrollbar_x.config(command=canvas.xview)
        scrollbar_y.config(command=canvas.yview)

        # creates canvas window for the tree
        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor="nw")

        # bind mousewheel events to scroll canvas
        canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(-int(event.delta / 120), "units"))
        canvas.bind("<Shift MouseWheel>", lambda event: canvas.xview_scroll(-int(event.delta / 120), "units"))

        # execute SQL to get query plan json
        result = self.executeQuery(qry)

        # print output of planning and execution time on GUI
        planTime = result["Planning Time"]
        exeTime = result["Execution Time"]
        self.outputText.config(state=tk.NORMAL)
        self.outputText.delete("1.0", tk.END)
        self.outputText.insert(tk.END, f"Planning Time: {planTime}\n")
        self.outputText.insert(tk.END, f"Execution Time: {exeTime}\n")
        self.outputText.config(state=tk.DISABLED)

        # parse query plan json to create and draw query plan tree
        plan = result["Plan"]
        root_node = self.create_tree(plan)
        self.draw_tree(canvas, root_node, 400, 50)

        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))



class QueryPlanNode: # node strucure to contain the different kinds of details from query plan json
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
        self.level = 1 # keep track of which level this node is at, root node being the highest level

class Blocks:
    def __init__(self, db_conn: DBConn, relation, pages):
        self.db_conn = db_conn
        self.pages = pages # list of pages being accessed by this sequential scan
        self.relation = relation # the table on which this sequential scan is being performed
        self.pageStartIndex = 0 # the page number of the first block being displayed currently

        self.root = tk.Tk()
        self.root.geometry("1400x400")
        self.root.title("Blocks Accessed")
        self.tuplesText = None # String that says Tuples in Block:
        self.tupleText = None # String that says Tuple:
        self.drawnBlocks = [] # What blocks objects have been drawn
        self.drawnBlocksText = [] # Block ID drawn on the blocks
        self.tuples = [] # what tuple objects have been drawn
        self.tupleNums = [] # tuple id drawn on the blocks
        self.tupleRows = 0 # so that we know where to print the tuple
        self.root.focus_force() # bring the window to focus

        # initialise scrollbars
        scrollbar_y = tk.Scrollbar(self.root, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x = tk.Scrollbar(self.root, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")

        # create a canvas and link it with the scrollbars
        self.canvas = tk.Canvas(self.root, xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)
        self.canvas.pack(side="left", fill="both", expand=True)

        # link scrollbars to canvas
        scrollbar_x.config(command=self.canvas.xview)
        scrollbar_y.config(command=self.canvas.yview)
        
        # creates canvas window for the tree
        self.frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="center")

        # bind mousewheel events to scroll canvas
        self.canvas.bind("<MouseWheel>", lambda event: self.canvas.yview_scroll(-int(event.delta / 120), "units"))
        self.canvas.bind("<Shift MouseWheel>", lambda event: self.canvas.xview_scroll(-int(event.delta / 120), "units"))

        # create buttons to navigate through different sets of blocks
        self.previousBtn = tk.Button(self.canvas, text="PREVIOUS", command=self.previous_set_blocks, state=tk.DISABLED)
        self.previousBtn.place(x=150, y=250)

        if len(self.pages) > 50:
            self.nextBtn = tk.Button(self.canvas, text="NEXT", command=lambda: self.next_set_blocks(offset=50), state=tk.NORMAL)
        else:
            self.nextBtn = tk.Button(self.canvas, text="NEXT", command=lambda: self.next_set_blocks(offset=50), state=tk.DISABLED)
        self.nextBtn.place(x=250, y=250)


        self.blocks = None # list of blocks being displayed currently
        self.next_set_blocks()
        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.frame.bbox("all"))

    def start(self):
        # start the Tkinter event loop
        self.root.mainloop()

    def draw_blocks(self, x, y, pageStart):
        level = 0 # which level to draw blocks on

        self.canvas.create_text(x-100, y, text='Blocks Accessed: ') # text for blocks accessed
        for blkNum in range(pageStart, pageStart + len(self.blocks)):
            modBlk = blkNum % 10 # used for positioning of blocks, 10 in a row
            
             # draw block
            block = self.canvas.create_rectangle(x-20+modBlk*40, y-20+level*40, x+20+modBlk*40, y+20+level*40, fill = "white")
            self.drawnBlocks.append(block) # keep track of which block drawn

            # put text on block
            text = self.canvas.create_text(x+modBlk*40, y+level*40, text=f'{blkNum}')
            self.drawnBlocksText.append(text) # keep track of what text has been put

            # bind events for interacting with blocks
            self.canvas.tag_bind(block, "<Enter>", lambda event, block_id=block: self.on_block_enter(event, block_id))
            self.canvas.tag_bind(block, "<Leave>", lambda event, block_id=block: self.on_block_leave(event, block_id))
            self.canvas.tag_bind(block, "<Button-1>", lambda event, block_id=block, blkNum=blkNum: self.on_block_click(event, block_id, blkNum, x, y))

            if(modBlk == 9):
                level += 1 # start drawing blocks on next level

    def next_set_blocks(self, offset=0): # load the set of blocks
        self.clear_blocks() # clear the current blocks being displayed
        self.clear_tuples() # clear the current tuples being displayed
        
        self.pageStartIndex += offset # determines the block numbers being displayed
        if self.pageStartIndex > 0:
            self.previousBtn['state'] = tk.NORMAL # enable the previous button
        
        blocks = [] # hold the information of the different blocks
        count = 1 # count how many blocks are being drawn
        for page in self.pages[self.pageStartIndex:]:
            blocks.append(exploration.retrieve_block(self.db_conn, self.relation, page))
            count += 1
            if count > 50: # we only want 50 blocks displayed at a time
                break
        
        if count > 50: # so that the blocks count correctly
            count -= 1

        if self.pageStartIndex + count >= len(self.pages): # last possible set of blocks
            self.nextBtn['state'] = tk.DISABLED

        self.blocks = blocks.copy()
        self.draw_blocks(200, 50, self.pageStartIndex) # draw the blocks on the GUI


    def previous_set_blocks(self): # load the previous set of blocks
        self.clear_blocks() # clear the current blocks being displayed
        self.clear_tuples() # clear the current tuples being displayed

        self.pageStartIndex -= 50  # determines the block numbers being displayed

        # enable or disable buttons accordingly
        if self.pageStartIndex <= 0:
            self.previousBtn['state'] = tk.DISABLED
        if self.nextBtn['state'] == tk.DISABLED:
            self.nextBtn['state'] = tk.NORMAL

        blocks = [] # hold information of vblocks being displayed
        count = 1 
        for page in self.pages[self.pageStartIndex:]:
            blocks.append(exploration.retrieve_block(self.db_conn, self.relation, page))
            count += 1
            if count > 50: # we only want 50 blocks displayed at a time
                break
        
        self.blocks = blocks.copy()
        self.draw_blocks(200, 50, self.pageStartIndex) # draw the blocks on the GUI

    def on_block_enter(self, event, block_id):
        # Change cursor on mouse enter
        event.widget.config(cursor="hand2")
        self.canvas.itemconfig(block_id, fill="lightblue") # highlight block being hovered on
        x, y, _, _ = event.widget.coords(block_id)

    def on_block_leave(self, event, block_id):
        # Change cursor back on mouse leave
        self.canvas.itemconfig(block_id, fill="white") # un-highlight block
        event.widget.config(cursor="")

    def on_block_click(self, event, block_id, blkNum, x, y):
        self.clear_tuples() # clear the tuple drawings

        x += 500
        self.tuplesText = self.canvas.create_text(x, y, text=f'Tuples in Block {blkNum}: ') # create text for tuples
        x += 100

        level = 0 # which level to draw the tuples on
        for tupleNum in range(len(self.blocks[blkNum%50])):
            modTuple = tupleNum % 10 # used for positioning of tuples, 10 in a row
            tuple = self.canvas.create_rectangle(x-20+modTuple*40, y-20+level*40, x+20+modTuple*40, y+20+level*40, fill = "white")
            self.tuples.append(tuple) # Keep track of what tuples are being drawn
            tupleNumber = self.canvas.create_text(x+modTuple*40, y+level*40, text=f'{tupleNum}')
            self.tupleNums.append(tupleNumber) # Keep track of what tuples are being drawn

            # bind events for interacting with tuples
            self.canvas.tag_bind(tuple, "<Enter>", lambda event, tuple_id=tuple: self.on_tuple_enter(event, tuple_id))
            self.canvas.tag_bind(tuple, "<Leave>", lambda event, tuple_id=tuple: self.on_tuple_leave(event, tuple_id))
            self.canvas.tag_bind(tuple, "<Button-1>", lambda event, tuple_id=tuple, blkNum=blkNum, tupleNum=tupleNum: self.on_tuple_click(event, tuple_id, blkNum, tupleNum, x-100, y))

            if(modTuple == 9):
                level += 1 # start drawing blocks on next level

        self.tupleRows = level + 1
        self.frame.update_idletasks() # update window
        self.canvas.config(scrollregion=self.canvas.bbox("all")) # update scroll region

    def on_tuple_enter(self, event, tuple_id):
        # Change cursor on mouse enter
        event.widget.config(cursor="hand2")
        self.canvas.itemconfig(tuple_id, fill="lightgreen") # highlight tuple being hovered on
        x, y, _, _ = event.widget.coords(tuple_id)

    def on_tuple_leave(self, event, tuple_id):
        # Change cursor back on mouse leave
        self.canvas.itemconfig(tuple_id, fill="white") # unhighlight tuple
        event.widget.config(cursor="")

    def on_tuple_click(self, event, tuple_id, blkNum, tupleNum, x, y):
        if self.tupleText:
            self.canvas.delete(self.tupleText) # delete any tuple information
        
        y += self.tupleRows * 40 # position the tuple information text
        self.tupleText = self.canvas.create_text(x, y, anchor='w', text=f'Tuple {tupleNum}: {self.blocks[blkNum%50][tupleNum]}')
        self.frame.update_idletasks() # update window
        self.canvas.config(scrollregion=self.canvas.bbox("all")) # update scroll region
        
    # clear the tuples being drawn on the GUI currently
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
    
    # clear the blocks being drawn on the GUI currently
    def clear_blocks(self):
        for drawn in self.drawnBlocks:
            self.canvas.delete(drawn)
        for text in self.drawnBlocksText:
            self.canvas.delete(text)

        self.drawnBlocks = []
        self.drawnBlocksText = []

