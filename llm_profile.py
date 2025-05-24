import google.generativeai as genai
import os
from typing import Dict, List
import json
from datetime import datetime

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_profile(search_results: Dict) -> Dict:
    """
    Generate a person's profile using Gemini API based on search results.
    
    Args:
        search_results (Dict): Search results from SerpAPI
        
    Returns:
        Dict: Generated profile information
    """
    # Initialize Gemini model
    model = genai.GenerativeModel('gemini-pro')
    
    # Prepare context from search results
    context = prepare_context(search_results)
    
    # Generate profile
    prompt = f"""
    Based on the following information about a person, generate a detailed profile.
    Include:
    1. Who is this person? (brief introduction)
    2. What are their main interests and communication style?
    3. How to best communicate with them?
    
    Information:
    {context}
    
    Format the response as a JSON object with the following structure:
    {{
        "introduction": "Brief introduction",
        "interests": ["List of interests"],
        "communication_style": "Description of communication style",
        "communication_tips": ["List of tips for effective communication"]
    }}
    """
    
    try:
        # Generate response
        response = model.generate_content(prompt)
        
        # Parse response
        profile_data = json.loads(response.text)
        
        # Add metadata
        profile_data["generated_at"] = datetime.now().isoformat()
        profile_data["source_data"] = {
            "search_timestamp": search_results.get("timestamp"),
            "query": search_results.get("query")
        }
        
        return profile_data
        
    except Exception as e:
        print(f"Error generating profile: {str(e)}")
        return {"error": str(e)}

def prepare_context(search_results: Dict) -> str:
    """
    Prepare context from search results for the LLM.
    
    Args:
        search_results (Dict): Search results from SerpAPI
        
    Returns:
        str: Formatted context string
    """
    context_parts = []
    
    # Add knowledge graph information
    if knowledge_graph := search_results.get("knowledge_graph"):
        context_parts.append("Knowledge Graph Information:")
        for key, value in knowledge_graph.items():
            if isinstance(value, (str, list)):
                context_parts.append(f"{key}: {value}")
    
    # Add organic results
    if organic_results := search_results.get("organic_results"):
        context_parts.append("\nSearch Results:")
        for result in organic_results[:5]:  # Limit to top 5 results
            context_parts.append(f"Title: {result.get('title', '')}")
            context_parts.append(f"Snippet: {result.get('snippet', '')}")
            context_parts.append(f"Link: {result.get('link', '')}\n")
    
    return "\n".join(context_parts)

def save_profile(first_name: str, last_name: str, profile_data: Dict) -> None:
    """
    Save generated profile to a JSON file.
    
    Args:
        first_name (str): Person's first name
        last_name (str): Person's last name
        profile_data (Dict): Generated profile data
    """
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Create filename
    filename = f"data/{first_name}_{last_name}_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Save to file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2) 