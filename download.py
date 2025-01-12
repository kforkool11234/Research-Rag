import requests
import os
import re
from xml.etree import ElementTree as ET

# Base URL for arXiv API
ARXIV_API_URL = "http://export.arxiv.org/api/query"

# Search parameters
query = input("enter topic to search: ")  # Replace with your search query
max_results = 50         # Number of papers to fetch
output_folder = "../data/archive"  # Folder to save PDFs

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Function to sanitize file names for Windows
def sanitize_filename(filename):
    """Sanitize file name to remove invalid characters."""
    return re.sub(r'[\/:*?"<>|\\\n]', '_', filename)

# Fetch and download PDFs from arXiv
def fetch_and_download_pdfs(query, max_results, output_folder):
    """Fetch metadata from arXiv and download associated PDFs."""
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results
    }
    response = requests.get(ARXIV_API_URL, params=params)
    if response.status_code != 200:
        print(f"Error: Unable to fetch data (Status Code: {response.status_code})")
        return

    # Parse the XML response
    root = ET.fromstring(response.text)
    ns = {"ns": "http://www.w3.org/2005/Atom"}
    entries = root.findall("ns:entry", ns)

    # Download PDFs
    for entry in entries:
        title = entry.find("ns:title", ns).text.strip()
        sanitized_title = sanitize_filename(title)
        pdf_url = entry.find("ns:link[@type='application/pdf']", ns).attrib["href"]

        print(f"Downloading: {title}")
        pdf_response = requests.get(pdf_url)
        if pdf_response.status_code == 200:
            file_name = os.path.join(output_folder, f"{sanitized_title}.pdf")
            with open(file_name, "wb") as pdf_file:
                pdf_file.write(pdf_response.content)
            print(f"Saved to: {file_name}")
        else:
            print(f"Failed to download PDF for: {title}")

# Main function
def main():
    fetch_and_download_pdfs(query, max_results, output_folder)

if __name__ == "__main__":
    main()
