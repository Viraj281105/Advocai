# tools/pubmed_search.py

import os
import requests
from typing import List, Dict
from dotenv import load_dotenv

# Load .env file explicitly if not done in main
load_dotenv() 

PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PUBMED_API_KEY = os.getenv("PUBMED_API_KEY")

def pubmed_search(query: str, max_results: int = 3) -> List[Dict]:
    """
    Performs a search on PubMed for medical and clinical articles. 
    This tool is used by the Clinician Agent.

    Args:
        query: The search term (e.g., "efficacy of treatment X for denial code Y").
        max_results: The maximum number of relevant article summaries to return.
        
    Returns:
        A list of dictionaries containing article titles and raw abstracts.
    """
    if not PUBMED_API_KEY:
        # Proceed with limited use if key is missing, but warn the user
        print("Warning: PUBMED_API_KEY not found. Using rate-limited access.")
        
    # --- 1. Search for article IDs (ESearch) ---
    search_params = {
        'db': 'pubmed',
        'term': query,
        'retmode': 'json',
        'retmax': max_results,
        'tool': 'AdvocaiAgent', # Best practice to identify your application
        'api_key': PUBMED_API_KEY # Automatically adds key if available
    }
    
    search_response = requests.get(f"{PUBMED_BASE_URL}esearch.fcgi", params=search_params)
    search_data = search_response.json()
    
    id_list = search_data.get('esearchresult', {}).get('idlist', [])
    
    if not id_list:
        return [{"error": "No relevant medical articles found for the query."}]

    # --- 2. Retrieve detailed summaries (EFetch) ---
    retrieve_params = {
        'db': 'pubmed',
        'id': ','.join(id_list),
        'retmode': 'text',
        'rettype': 'abstract',
        'tool': 'AdvocaiAgent',
        'api_key': PUBMED_API_KEY
    }

    retrieve_response = requests.get(f"{PUBMED_BASE_URL}efetch.fcgi", params=retrieve_params)
    
    return [{"query": query, "raw_abstracts": retrieve_response.text}]