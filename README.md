# AI ERP Error Assistant

AI ERP Error Assistant is a lightweight local AI application that helps users understand and troubleshoot ERP system errors.

The application allows users to select an ERP platform, paste an error message, and receive an AI-generated explanation with possible causes, troubleshooting steps, and a suggested resolution.

The project runs locally using Ollama and Llama 3.2, so no paid AI API is required.

## Features

- Supports multiple ERP systems:
  - NetSuite
  - Workday
  - SAP
  - Other ERP systems
- AI-powered ERP error analysis
- Explains the meaning of an error
- Identifies possible causes
- Provides troubleshooting steps
- Suggests potential resolutions
- Simple web interface using Streamlit
- Runs AI locally using Ollama
- No paid API required

## Tech Stack

- Python
- Streamlit
- Ollama
- Llama 3.2
- Git
- GitHub

## How It Works

User enters an ERP error:

```text
Invalid department reference

The application sends the error and ERP context to a locally running Llama model through Ollama.

The AI then returns structured troubleshooting information:

Error Meaning

Possible Causes

What to Check

Suggested Resolution
Project Architecture
User
  ↓
Streamlit Web Interface
  ↓
Python Application
  ↓
Ollama
  ↓
Llama 3.2
  ↓
AI Generated Troubleshooting Response
Installation

Clone the repository:

git clone https://github.com/kanderimounish-ai/ai-erp-assistant.git

Move into the project directory:

cd ai-erp-assistant

Create a Python virtual environment:

python -m venv .venv

Activate the virtual environment on Windows:

.\.venv\Scripts\Activate.ps1

Install the required Python packages:

pip install -r requirements.txt
Install Ollama

Download and install Ollama from:

https://ollama.com

Download the Llama 3.2 model:

ollama pull llama3.2:3b

Test the model:

ollama run llama3.2:3b
Run the Application

Start the Streamlit application:

streamlit run app.py

Then open:

http://localhost:8501

in your browser.

Example

ERP System:

NetSuite

Error:

Invalid department reference

The assistant analyzes the error and provides:

Error meaning
Possible causes
Checks to perform
Suggested resolution
Project Structure
ai-erp-assistant/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── .venv/

The .venv directory is excluded from GitHub through .gitignore.

Current Status

The first version of the AI ERP Error Assistant includes:

Local LLM integration
Streamlit user interface
ERP system selection
Dynamic AI prompting
Structured troubleshooting responses
Planned Improvements

Future versions may include:

Structured JSON responses
Better response parsing
Error history
Screenshot-based error analysis
ERP documentation search
RAG using internal documentation
Similar-error search
Ticket generation
NetSuite and Workday specific troubleshooting knowledge
Improved user interface
Purpose

This project was created as a hands-on learning project to understand how AI applications are built end-to-end, including:

Python development
Prompt engineering
Local large language models
AI application architecture
Streamlit interfaces
Git version control
GitHub project management
Author

Mounish Kanderi