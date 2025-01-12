# Research-Rag
# RAG System with Snowflake and Mistral LLM

## Overview
This repository implements a Retrieval-Augmented Generation (RAG) system using Snowflake for data storage and Mistral LLM for advanced natural language processing. The system processes PDFs from various streams, extracts data, converts titles and abstracts into vectors, and stores all details in a Snowflake SQL table. A Cortex search system then retrieves relevant papers based on user queries by searching both vectors and titles. The Mistral LLM can either answer the user's query using the relevant research papers or assist in drafting a new research paper based on user input and examples.

---

## Installation and Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Snowflake account and access credentials
- Streamlit for building the web interface

### Steps to Run the Application

1. **Clone the Repository**
   ```bash
   git clone https://github.com/kforkool11234/Research-Rag.git
   cd Research-Rag
   ```

2. **Install Dependencies**
   Use the following command to install all required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   Start the Streamlit web application:
   ```bash
   streamlit run app.py
   ```

---

## System Workflow

1. **Data Acquisition**
   - Download multiple PDFs from various sources.

2. **Data Processing**
   - Extract data from the PDFs part by part.
   - Convert titles and abstracts into vector representations.

3. **Data Storage**
   - Store all extracted details, including vector representations, in a Snowflake SQL table.

4. **Search System**
   - User queries trigger a Cortex search that retrieves relevant research papers by searching through stored vectors and titles.

5. **Mistral LLM Integration**
   - Use Mistral LLM to:
     - Answer user queries based on retrieved research papers.
     - Generate new research papers based on user input, using examples from the retrieved papers.

---

## Example Usage

1. **Query Search**
   - User enters a query (e.g., "What are the latest trends in AI research?").
   - The system retrieves relevant papers and provides answers or summaries.

2. **Research Paper Generation**
   - User provides data and an example of how they want the paper structured.
   - The system uses Mistral LLM to draft a paper using relevant research papers as references.

---

## Contribution
Feel free to open issues or submit pull requests to improve this repository. Make sure to follow best practices and provide detailed descriptions for your contributions.

---

## License
This project is licensed under the [MIT License](LICENSE).

---

## Contact
For further inquiries or collaboration opportunities, please reach out via [GitHub](https://github.com/kforkool11234/Research-Rag).

