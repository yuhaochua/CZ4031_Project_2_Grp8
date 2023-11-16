# CZ4031
DSP Project 2

## Setup and Installation

### Prerequisites

- Ensure you have [Python](https://www.python.org/downloads/) installed on your system.
- Ensure [Git](https://git-scm.com/downloads) is installed on your system.

### Step-by-Step Guide

1. **Clone the Repository**

   Clone the project repository from GitHub to your local machine.

   `git clone https://github.com/yuhaochua/CZ4031_Project_2_Grp8.git`
   
   `cd CZ4031_Project_2_Grp8`

2. **Create and Activate the Virtual Environment**

   On Windows:

   `python -m venv dbsp`
   
   `.\dbsp\Scripts\activate`

   On macOS and Linux:

   `python -m venv dbsp`
   
   `source dbsp/bin/activate`

3. **Install Dependencies**

   Use the requirements.txt file to install the necessary dependencies.

   `pip install -r requirements.txt`

4. **Running and using the GUI**

   Before launching UI, ensure that db connection details are correct in `exploration.py`, on lines 6 to 10

   Launch the GUI

   `python project.py`

   Enter SQL query and press the "Execute" button.

   Hover over the nodes to see buffer information.

   Click on "Seq Scan" nodes to open new window displaying blocks.