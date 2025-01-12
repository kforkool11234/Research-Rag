import os
import json
import snowflake.connector
from sentence_transformers import SentenceTransformer

# Initialize the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

def connect_to_snowflake():
    """Function to establish connection to Snowflake"""
    conn = snowflake.connector.connect(
        user='kaushal',
        password='RG4GdkVKHfHFkJ8',
        account='ZI02358.ap-south-1',
        warehouse='COMPUTE_WH',
        database='RAG_SYSTEM',
        schema='PUBLIC'
    )
    return conn

def vector_to_array_literal(vector):
    """Convert a vector to a Snowflake array literal string"""
    return f"ARRAY_CONSTRUCT({','.join(str(x) for x in vector)})"

def process_json_to_insert_data(json_data):
    """Process JSON data into a format suitable for insertion into Snowflake"""
    processed_data = []

    def get_vector_or_null(text):
        """Helper function to return NULL for empty text or encode the text"""
        return "NULL" if not text.strip() else vector_to_array_literal(model.encode(text).tolist())

    def get_text_or_null(text):
        """Helper function to return NULL for empty text or the text itself"""
        return "NULL" if not text.strip() else text

    for filename, paper in json_data.items():
        processed_data.append({
            "title": paper.get("title", ""),
            "abstract": get_text_or_null(paper.get("abstract", "")),
            "title_vector": get_vector_or_null(paper.get("title", "")),
            "abstract_vector": get_vector_or_null(paper.get("abstract", "")),
            "introduction": get_text_or_null(paper.get("introduction", "")),
            "methods": get_text_or_null(paper.get("methodology", "")),
            "results": get_text_or_null(paper.get("results", "")),
            "conclusion": get_text_or_null(paper.get("conclusion", "")),
            "keywords": get_text_or_null(paper.get("keywords", "")),
            "limitations": get_text_or_null(paper.get("limitations", "")),
            "future_work": get_text_or_null(paper.get("future_work", ""))
        })
    return processed_data

def insert_data(conn, data):
    cursor = conn.cursor()
    
    # Insert query including raw text fields and only vectors for title and abstract
    insert_query = """
    INSERT INTO detailed_research_papers (
        title, 
        abstract, 
        title_vector, 
        abstract_vector, 
        introduction, 
        methods, 
        results, 
        conclusion, 
        keywords, 
        limitations, 
        future_work
    )
    SELECT 
        %s, 
        %s, 
        {title_vector}, 
        {abstract_vector}, 
        %s, 
        %s, 
        %s, 
        %s, 
        %s, 
        %s, 
        %s
    """
    
    try:
        for item in data:
            formatted_query = insert_query.format(
                title_vector=item['title_vector'],
                abstract_vector=item['abstract_vector']
            )
            cursor.execute(formatted_query, (
                item['title'], 
                item['abstract'], 
                item['introduction'], 
                item['methods'], 
                item['results'], 
                item['conclusion'], 
                item['keywords'], 
                item['limitations'], 
                item['future_work']
            ))
        
        conn.commit()
        print(f"Inserted {len(data)} records successfully.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()

def main():
    """Main function to handle the process flow"""
    conn = connect_to_snowflake()
    
    # Load the JSON file containing multiple paper data
    with open('extracted_papers.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    processed_data = process_json_to_insert_data(json_data)
    insert_data(conn, processed_data)
    conn.close()

if __name__ == "__main__":
    main()
