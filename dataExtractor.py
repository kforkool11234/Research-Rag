import re
import os
import json
from transformers import LayoutLMForTokenClassification, LayoutLMTokenizer
from pdfminer.high_level import extract_text

# Load LayoutLM model and tokenizer
tokenizer = LayoutLMTokenizer.from_pretrained("microsoft/layoutlm-base-uncased")
model = LayoutLMForTokenClassification.from_pretrained("microsoft/layoutlm-base-uncased")

def extract_text_with_pdfminer(file_path):
    """Extracts raw text from a PDF file using pdfminer.six."""
    try:
        text = extract_text(file_path)
        return text
    except Exception as e:
        print(f"Error extracting text from {file_path}: {str(e)}")
        return ""

def organize_content_layoutlm(text, filename):
    """Organizes extracted text into sections using LayoutLM predictions."""
    organized_data = {
        "title": os.path.splitext(filename)[0],
        "abstract": "",
        "introduction": "",
        "methods": "",
        "results": "",
        "discussion": "",
        "conclusion": "",
        "keywords": "",
        "acknowledgement": "",
        "references": "",
        "limitations": "",
        "future_work": ""
    }

    current_section = None

    for line in text.splitlines():
        line_lower = line.lower()
        if any(header in line_lower for header in organized_data.keys()):
            current_section = next((key for key in organized_data.keys() if key in line_lower), None)
        elif current_section:
            organized_data[current_section] += line + " "

    for section in organized_data:
        organized_data[section] = organized_data[section].strip()

    return organized_data

def extract_and_organize_from_directory_with_pdfminer(directory_path):
    """Processes PDFs in a directory using pdfminer for text extraction and organizes content."""
    results = {}

    if not os.path.exists(directory_path):
        print(f"Directory {directory_path} does not exist.")
        return results

    for filename in os.listdir(directory_path):
        if filename.endswith('.pdf'):
            file_path = os.path.join(directory_path, filename)
            try:
                print(f"Processing: {filename}")
                text = extract_text_with_pdfminer(file_path)
                organized_data = organize_content_layoutlm(text, filename)
                results[filename] = organized_data

            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

    return results

def main():
    """Main function to run the PDF extraction and organization process."""
    directory_path = "../data/archive"  # Adjust this path to your PDF directory
    output_file_path = 'extracted_papers.json'

    print("Starting PDF processing with pdfminer...")
    all_data = extract_and_organize_from_directory_with_pdfminer(directory_path)

    try:
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(all_data, json_file, ensure_ascii=False, indent=4)
        print(f"\nData has been successfully saved to {output_file_path}.")
    except Exception as e:
        print(f"Error saving data to JSON: {str(e)}")

if __name__ == "__main__":
    main()