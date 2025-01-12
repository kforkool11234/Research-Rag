from snowflake.snowpark import Session 
from snowflake.core import Root
from mistralai import Mistral
import json
import os
from dotenv import load_dotenv
import re
load_dotenv()
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
DB = os.getenv('DB')
SCHEMA = os.getenv('SCHEMA')
SERVICE = os.getenv('SERVICE')

def create_session():
    connection_parameters = {
        "user": os.getenv('user'),
        "password": os.getenv('password'),
        "account": os.getenv('account'),
        "warehouse": 'COMPUTE_WH',
        "database": DB,
        "schema": SCHEMA
    }
    return Session.builder.configs(connection_parameters).create()
def analyze_query_and_decide(query):
    """
    Analyzes the query to:
    1. Extract needs and details provided.
    2. Decide if a full research paper or concise answer is required.
    """
    client = Mistral(api_key=MISTRAL_API_KEY)

    # Create a single prompt to analyze the query and decide the task type
    prompt = f"""
    You are a research assistant. Analyze the query provided below:
    
    1. Identify the "needs" (what the user is requesting, such as generating a research paper or a concise answer).
    2. Identify any "details provided" (information or context explicitly mentioned in the query).
    3. Based on the analysis, decide whether the user wants a "full research paper" or a "concise answer."
    4. Clearly return your analysis in the following JSON format such that json.:
       {{
           "needs": "<Extracted needs>",
           "details_provided": "<Details provided>",
           "task_type": "<full_paper or concise_answer>"
       }}
    
    Query: {query}
    """

    response = client.chat.complete(
        messages=[
            {"role": "system", "content": "You are a research assistant. Analyze the query as instructed."},
            {"role": "user", "content": prompt}
        ],
        model="open-mixtral-8x22b",
        temperature=0.3,
        max_tokens=500
    )

    # Parse and return the LLM's response
    response_text = response.choices[0].message.content.strip()
    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    json_text = json_match.group(0)  # Extract the matched JSON string
    print(json_text)
    return json.loads(json_text)
def get_relevant_context(session, query, limit=5):
    cortex_search_service = (
        Root(session)
        .databases[DB]
        .schemas[SCHEMA]
        .cortex_search_services[SERVICE]
    )

    # Perform the search and fetch all specified columns
    results = cortex_search_service.search(
        query,
        columns=["title", "abstract", "introduction", "methods", "results", 
                 "conclusion", "keywords", "limitations", "future_work"],  # Fetch specific columns
        limit=limit
    )

    context = []
    for result in results.results:
        result_dict = dict(result)  # Convert result to dictionary
        context.append(result_dict)  # Append the entire row as a dictionary

    
    return context
def extract_query_key_points(query):
    """Asks the LLM to extract key points and needs from the query."""
    client = Mistral(api_key=MISTRAL_API_KEY)

    # Create a prompt to extract key points and needs
    prompt = f"""
    You are a research assistant. Analyze the query and extract its key points and requirements. 
    Focus on summarizing the intent in concise terms, whether it is code or text.
    Query: {query}
    """
    response = client.chat.complete(
        messages=[
            {"role": "system", "content": "You are a research assistant. Extract key points and needs from the query."},
            {"role": "user", "content": prompt}
        ],
        model="open-mixtral-8x22b",
        temperature=0.3,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()
def query_with_chunked_rag(needs,details, context, chunk_size=2):
    """Process context in chunks and accumulate knowledge."""
    client = Mistral(api_key=MISTRAL_API_KEY)
    accumulated_knowledge = ""

    # Process context in chunks
    for i in range(0, len(context), chunk_size):
        chunk = context[i:i + chunk_size]

        # Format current chunk
        for doc in chunk:
            formatted_chunk=f"title:{doc['title']}\nabstract:{doc['abstract']}\nconclusion:{doc['conclusion']}\nintroduction{doc['introduction']}\nmethodology:{doc['methods']}\nresult:{doc['results']}\nlimitation{doc['limitations']}"

        # Create prompt based on whether this is the first chunk or not
        if i == 0:
            system_prompt = f"""You are a research assistant. now first understant what the user means and need by the query and what data and knowledge you can extract from the provided research paper to fulfil that so  acumulate all the knowledge and data that can help you give a proper response to the query."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {needs}+{details}\n\n set of papers:\n{formatted_chunk}"}
            ]
        else:
            system_prompt = f"""You are a research assistant. You have accumulated the following knowledge about the query:
            {accumulated_knowledge}
            
            Now analyze these additional papers and expand your knowledge. Integrate new information with what you already know."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Additional papers:\n{formatted_chunk}"}
            ]

        # Get response for this chunk
        response = client.chat.complete(
            messages=messages,
            model="open-mixtral-8x22b",
            temperature=0.3,
            max_tokens=500
        )

        # Accumulate knowledge
        accumulated_knowledge += response.choices[0].message.content + "\n"  # Append new knowledge

    # Final synthesis
    final_prompt = f"""Based on all the research papers analyzed, provide a comprehensive answer to the original query: {needs}+{details}
    
    Your accumulated knowledge:
    {accumulated_knowledge}
    
    Synthesize a complete answer that cites specific papers and covers all key findings and satiesfies the query."""

    final_response = client.chat.complete(
        messages=[
            {"role": "system", "content": "You are a research assistant. Provide a comprehensive final answer."},
            {"role": "user", "content": final_prompt}
        ],
        model="open-mixtral-8x22b",
        temperature=0.3,
        max_tokens=1000
    )

    return final_response.choices[0].message.content
def detect_research_paper_request(query):
    """Detects if the user wants a full research paper."""
    keywords = ["research paper", "write a paper", "full paper", "detailed study"]
    return any(keyword in query.lower() for keyword in keywords)

def generate_research_paper(needs, details, context, chunk_size=1):
    """Generates a research paper in multiple parts."""
    client = Mistral(api_key=MISTRAL_API_KEY)
    accumulated_knowledge = (
        "Golden rules:\n"
        "1) Try to keep abstract short, informative, and concise (max 2 paragraphs per section).\n"
        "2) The introduction should provide an overview of the entire paper (4-5 paragraphs).\n"
    )

    for i in range(0, len(context) - 2, chunk_size):
        chunk = context[i:i + chunk_size]

        # Format current chunk
        formatted_chunk = ""
        for doc in chunk:
            formatted_chunk += (
                f"title: {doc['title']}\n"
                f"abstract: {doc['abstract']}\n"
                f"conclusion: {doc['conclusion']}\n"
                f"introduction: {doc['introduction']}\n"
                f"methodology: {doc['methods']}\n"
                f"result: {doc['results']}\n"
                f"limitation: {doc['limitations']}\n"
            )

        # Create prompt based on whether this is the first chunk or not
        if i == 0:
            system_prompt = (
                "You are a research assistant. You have to write a research paper according to the user's needs. "
                "Take these papers as reference and note down the key points that each section should have to generate a good research paper."
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {needs} + {details}\n\nSet of papers:\n{formatted_chunk}"}
            ]
        else:
            system_prompt = (
                f"You are a research assistant. You have noted these points:\n{accumulated_knowledge}\n"
                "Analyze further papers and make changes to these points if needed."
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Additional papers:\n{formatted_chunk}"}
            ]

        # Debug: Log the first few words of the prompt
        print("\n[DEBUG] Sending prompt to Mistral API (Chunked Accumulation):")
        for msg in messages:
            print(f"{msg['role'].capitalize()}: {msg['content']}")  # Show the first 100 characters

        # Get response for this chunk
        response = client.chat.complete(
            messages=messages,
            model="open-mixtral-8x22b",
            temperature=0.3,
            max_tokens=500
        )

        # Accumulate knowledge
        accumulated_knowledge += response.choices[0].message.content + "\n"  # Append new knowledge

    sections = [
        "Title & Abstract", "Introduction", "Literature Review", 
        "Methods", "Results", "Discussion", "Conclusion"
    ]
    paper_content = {}

    for section in sections:
        # Prepare prompt for each section
        prompt = (
            f"You are a research assistant. Write a research paper based on the user's query and data.\n\n"
            f"Accumulated knowledge:\n{accumulated_knowledge}\n\n"
            f"Write the {section} of the research paper using the details: {details}.\n"
            f"Fill in any missing points from the notes or your own expertise and mention them as 'Added Points' below and keep the added point short.\n"
        )

        # Debug: Log the first few words of the section prompt
        print(f"\n[DEBUG] Sending prompt to Mistral API (Section: {section}):")
        print(f"Prompt: {prompt[:100]}...")  # Show the first 100 characters

        # Get response for the section
        response = client.chat.complete(
            messages=[
                {"role": "system", "content": "You are a research assistant. Generate the requested section of the paper."},
                {"role": "user", "content": prompt}
            ],
            model="open-mixtral-8x22b",
            temperature=0.3,
            max_tokens=1000
        )

        # Save the generated content for this section
        paper_content[section] = response.choices[0].message.content
        print(f"\nGenerated {section}:\n{response.choices[0].message.content[:100]}...")  # Show first 100 characters

    return paper_content

def main(query):
    try:
        # Create a Snowflake session
        session = create_session()
        
        # Analyze the query and decide the task type
        analysis = analyze_query_and_decide(query)
        print(analysis)
        needs = analysis["needs"]
        details_provided = analysis["details_provided"]
        task_type = analysis["task_type"]

        print("Query Analysis:")
        print(f"Needs: {needs}")
        print(f"Details Provided: {details_provided}")
        print(f"Task Type: {task_type}")

        # Fetch relevant data from Snowflake
        context = get_relevant_context(session, query)

        if task_type == "full_paper":
            print("Generating a full research paper...")
            paper = generate_research_paper(needs,details_provided,context, chunk_size=1)
            print("\nFinal Research Paper:")
            return paper
        else:
            print("Generating a concise answer...")
            answer = query_with_chunked_rag(needs, details_provided,context, chunk_size=2)
            print(f"\nQuery: {query}")
            print("\nGenerated Answer:")
            return answer

    except Exception as e:
        print(f"Error: {str(e)}")