# 📊 Graphico — AI-Powered Data Analysis & Visualization

**Graphico** is an AI-powered platform that automatically **analyzes your CSV data** and **generates visualizations** from simple natural-language commands.  
Just upload your file, type a request like:  Scatter of Age vs Fare colored by Survived from titanic.csv


…and Graphico will handle the rest.

---

## 🚀 How It Works

Graphico uses **Microsoft AutoGen** to run a **dual-agent system**:

1. **🧠 Data Analyst Agent**  
   - Reads and understands your request  
   - Analyzes the uploaded CSV file  
   - Generates the Python visualization code  

2. **⚙️ Code Executor Agent**  
   - Runs the generated code **inside a Docker container** for safety  
   - Returns the visualization  
   - If there’s an error, sends feedback to the Data Analyst Agent to automatically fix and retry  

💡 **Round-robin collaboration:** The agents work in cycles until your visualization is perfect.

---

## ✨ Features

- 📂 Upload any CSV file  
- 💬 Give plain-English visualization commands  
- 📊 Supports **scatter plots, bar charts, pie charts, histograms, line plots,** and more  
- 🛡 Secure execution using Docker isolation  
- 🔄 Automatic error detection and correction  
- ⚡ Continuous improvement loop between agents  

---

## 🛠 Installation

### **1. Clone the repository**
```bash
git clone https://github.com/<your-username>/Graphico.git
cd Graphico
2. Install dependencies

pip install -r requirements.txt
3. (Optional) Setup Docker

Make sure Docker is installed and running — Graphico uses it for secure code execution.
4. Run the Streamlit app

streamlit run "Analyzer Gpt\streamlit_app.py"

## 💡 Example Commands

**Important:** Always **add the name of your CSV file at the end of your command** so Graphico knows which dataset to use.  

After uploading your CSV, you can type commands like:
if customers-100.csv is your csv file name - then use commands like 
Bar of Country vs Count of Customers from customers-100.csv



## 📂 Project Structure
Graphico/
│── Analyzer Gpt/             # Main application folder
│   ├── agents/               # Agent definitions
│   ├── config/               # Configuration files
│   ├── team/                 # Agent team setup
│   ├── .env                  # Environment variables (API keys, config)
│   ├── main.py               # Entry point for CLI usage
│   ├── streamlit_app.py      # Streamlit web frontend
│
│── temp/                     # Stores uploaded CSV files and generated visualization PNGs
│── requirements.txt          # Python dependencies


🖼 Workflow Diagram

flowchart LR
    A[User Uploads CSV + Command] --> B[🧠 Data Analyst Agent]
    B --> C[Generate Python Visualization Code]
    C --> D[⚙️ Code Executor Agent (Docker)]
    D -->|Success| E[📊 Visualization Output]
    D -->|Error| B

flowchart LR
    A[User Uploads CSV + Command] --> B[🧠 Data Analyst Agent]
    B --> C[Generate Python Visualization Code]
    C --> D[⚙️ Code Executor Agent (Docker)]
    D -->|Success| E[📊 Visualization Output]
    D -->|Error| B


```
💡 Powered by:

    Microsoft AutoGen

    Streamlit

    Pandas

    Matplotlib & Seaborn

