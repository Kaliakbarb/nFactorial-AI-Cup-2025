from serpapi import GoogleSearch
import os
from typing import Dict, List
import json
from datetime import datetime

def search_person(first_name: str, last_name: str) -> Dict:
    """
    Search for information about a person using SerpAPI.
    
    Args:
        first_name (str): Person's first name
        last_name (str): Person's last name
        
    Returns:
        Dict: Dictionary containing search results
    """
    # Construct search query
    query = f"{first_name} {last_name}"
    
    # Initialize search parameters
    params = {
        "engine": "google",
        "q": query,
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "num": 10,  # Number of results
        "gl": "us",  # Country to search from
        "hl": "en"   # Language
    }
    
    try:
        # Perform the search
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Extract relevant information
        search_data = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "organic_results": results.get("organic_results", []),
            "knowledge_graph": results.get("knowledge_graph", {}),
            "related_searches": results.get("related_searches", []),
            "related_questions": results.get("related_questions", [])
        }
        
        # Save results to file
        save_search_results(first_name, last_name, search_data)
        
        return search_data
        
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return {"error": str(e)}

def save_search_results(first_name: str, last_name: str, data: Dict) -> None:
    """
    Save search results to a JSON file.
    
    Args:
        first_name (str): Person's first name
        last_name (str): Person's last name
        data (Dict): Search results data
    """
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Create filename
    filename = f"data/{first_name}_{last_name}_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Save to file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_social_profiles(results: Dict) -> List[Dict]:
    """
    Extract social media profiles from search results.
    
    Args:
        results (Dict): Search results from SerpAPI
        
    Returns:
        List[Dict]: List of social media profiles
    """
    social_profiles = []
    
    # Common social media domains
    social_domains = {
        "linkedin.com": "LinkedIn",
        "twitter.com": "Twitter",
        "facebook.com": "Facebook",
        "instagram.com": "Instagram",
        "github.com": "GitHub"
    }
    
    # Check organic results
    for result in results.get("organic_results", []):
        link = result.get("link", "")
        for domain, platform in social_domains.items():
            if domain in link:
                social_profiles.append({
                    "platform": platform,
                    "url": link,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", "")
                })
    
    return social_profiles 