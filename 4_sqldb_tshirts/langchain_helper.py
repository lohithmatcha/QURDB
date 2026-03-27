from few_shots import few_shots
import os
from dotenv import load_dotenv
import re
from decimal import Decimal
import warnings
import time

# Suppress FutureWarning from PyTorch/transformers
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

# Newer imports
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI  # from langchain_google_genai
from langchain_experimental.sql import SQLDatabaseChain
from langchain.utilities import SQLDatabase
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings  # check version
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts import FewShotPromptTemplate, SemanticSimilarityExampleSelector

load_dotenv()

def format_database_result_with_llm(question, raw_result, db_schema=""):
    """
    Use LLM to format raw database results into user-friendly responses
    """
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Create a prompt for the LLM to format the result
            llm = ChatGoogleGenerativeAI(
                google_api_key=os.environ.get("GOOGLE_API_KEY"),
                model="models/gemini-2.5-flash",  # Using standard model name with prefix
                temperature=0.1,
                max_retries=3,
                timeout=60
            )
            
            # Convert raw result to string for LLM processing
            result_str = str(raw_result)
            
            prompt = f"""
You are a helpful assistant that converts raw database query results into user-friendly, natural language responses.

Question asked: "{question}"

Raw database result: {result_str}

Database schema context: {db_schema}

Please provide a clear, natural language answer that directly addresses the question. 
- Use proper formatting for numbers (commas, currency symbols)
- Be conversational and helpful
- Don't mention technical details like "database result" or "query"
- Make it sound like a natural response to the user's question

Examples:
- If result is [(Decimal('999'),)] and question is about count: "There are 999 items"
- If result is [(Decimal('29.99'),)] and question is about price: "The average price is $29.99"
- If result is [('Nike',)] and question is about brand: "The brand is Nike"

Response:"""
            
            response = llm.invoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            error_str = str(e).lower()
            # Check if it's a rate limit error
            if "429" in error_str or "resource exhausted" in error_str or "quota" in error_str:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed, use fallback
                    return create_user_friendly_response(question, raw_result)
            else:
                # Other errors, use fallback immediately
                return create_user_friendly_response(question, raw_result)
    
    # If all retries failed, use fallback
    return create_user_friendly_response(question, raw_result)

def create_user_friendly_response(question, raw_result):
    """
    Fallback function for basic formatting
    """
    try:
        if isinstance(raw_result, (list, tuple)) and len(raw_result) > 0:
            if isinstance(raw_result[0], (list, tuple)) and len(raw_result[0]) > 0:
                value = raw_result[0][0]
            else:
                value = raw_result[0]
            
            if isinstance(value, Decimal):
                value = float(value)
            
            return f"The result is: *{value}*"
        else:
            return f"The result is: *{str(raw_result)}*"
    except Exception as e:
        return f"Error processing result: {str(e)}"

def format_database_result(result, question=""):
    """
    Format database results into user-friendly text using LLM
    """
    # Get database schema for better context
    db_schema = """
    Database: atliq_tshirts
    Table: t_shirts
    Columns:
    - t_shirt_id (INT): Unique identifier
    - brand (VARCHAR): Brand name (Nike, Levi, Adidas, etc.)
    - color (VARCHAR): Color (White, Black, Red, Blue, etc.)
    - size (VARCHAR): Size (XS, S, M, L, XL, XXL)
    - price (DECIMAL): Price in dollars
    - stock_quantity (INT): Number of items in stock
    """
    
    return format_database_result_with_llm(question, result, db_schema)

def get_few_shot_db_chain():
    # Database credentials
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASS", "9030")
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "atliq_tshirts")

    # Create SQLDatabase
    db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}",
                              sample_rows_in_table_info=3)

    # Use new LLM / Chat model with proper error handling
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
    
    llm = ChatGoogleGenerativeAI(
        google_api_key=google_api_key,
        model="models/gemini-2.5-flash",  # Using standard model name with prefix
        temperature=0.1,
        max_retries=3,
        timeout=60
    )

    # Build embeddings & example selector (for few shot)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # Prepare your few_shots (list of dicts with keys matching the example prompt)
    from few_shots import few_shots  

    to_vectorize = [" ".join(example.values()) for example in few_shots]
    vectorstore = Chroma.from_texts(to_vectorize, embeddings, metadatas=few_shots)

    example_selector = SemanticSimilarityExampleSelector(
        vectorstore=vectorstore,
        k=2
    )

    # Custom prompt templates
    mysql_prompt = """You are a MySQL expert. Given an input question, create a syntactically correct MySQL query to run.

Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. You can order the results to return the most informative data in the database.
Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use CURDATE() function to get the current date, if the question involves "today".

IMPORTANT: Return ONLY the SQL query without any markdown formatting, code blocks, or backticks. Just the raw SQL query.

Use the following format:

Question: {input}
SQLQuery: <your query here>
SQLResult: <result>
Answer: <final answer here>

IMPORTANT: Return only the SQL query part.
"""

    example_prompt = PromptTemplate(
        input_variables=["Question", "SQLQuery", "SQLResult", "Answer"],
        template="\nQuestion: {Question}\nSQLQuery: {SQLQuery}\nSQLResult: {SQLResult}\nAnswer: {Answer}"
    )

    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix=mysql_prompt,
        suffix="{input}\n\nHere are the tables:\n{table_info}\n\nRespond as above.\n",
        input_variables=["input", "table_info", "top_k"]
    )

    # Build the chain
    chain = SQLDatabaseChain.from_llm(
        llm=llm,
        db=db,
        prompt=few_shot_prompt,
        return_direct=True,  # Return direct database results
        verbose=True
    )

    return chain