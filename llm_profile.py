import google.generativeai as genai
import os
from typing import Dict, List
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API with API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Try to read from .env file directly as fallback
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('GOOGLE_API_KEY='):
                    api_key = line.split('=')[1].strip()
                    break
    except Exception as e:
        print(f"Error reading .env file: {str(e)}")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables or .env file")

genai.configure(api_key=api_key)

def generate_profile(search_results: Dict) -> Dict:
    """
    Generate a person's profile using Gemini API based on search results.
    
    Args:
        search_results (Dict): Search results from SerpAPI
        
    Returns:
        Dict: Generated profile information
    """
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
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
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Parse response
        try:
            profile_data = json.loads(response.text)
        except json.JSONDecodeError:
            # If response is not valid JSON, try to extract JSON from the text
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                profile_data = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse response as JSON")
        
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

def save_profile(first_name: str, last_name: str, profile_data: Dict) -> str:
    """
    Save generated profile to a JSON file in the people directory.
    
    Args:
        first_name (str): Person's first name
        last_name (str): Person's last name
        profile_data (Dict): Generated profile data
        
    Returns:
        str: Path to the saved profile file
    """
    # Create people directory if it doesn't exist
    people_dir = os.path.join("data", "people")
    os.makedirs(people_dir, exist_ok=True)
    
    # Create a unique identifier for the person
    person_id = f"{first_name.lower()}_{last_name.lower()}"
    
    # Create filename
    filename = f"{person_id}_profile.json"
    filepath = os.path.join(people_dir, filename)
    
    # Add person metadata
    profile_data["person"] = {
        "id": person_id,
        "first_name": first_name,
        "last_name": last_name,
        "full_name": f"{first_name} {last_name}"
    }
    
    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)
    
    return filepath

def get_all_profiles() -> List[Dict]:
    """
    Get a list of all saved profiles.
    
    Returns:
        List[Dict]: List of profile data
    """
    profiles = []
    people_dir = os.path.join("data", "people")
    
    if not os.path.exists(people_dir):
        return profiles
    
    for filename in os.listdir(people_dir):
        if filename.endswith("_profile.json"):
            filepath = os.path.join(people_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
                    profiles.append(profile_data)
            except Exception as e:
                print(f"Error reading profile {filename}: {str(e)}")
    
    return profiles

def get_profile_by_id(person_id: str) -> Dict:
    """
    Get a specific profile by person ID.
    
    Args:
        person_id (str): Person's unique identifier
        
    Returns:
        Dict: Profile data or empty dict if not found
    """
    filepath = os.path.join("data", "people", f"{person_id}_profile.json")
    
    if not os.path.exists(filepath):
        return {}
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading profile {person_id}: {str(e)}")
        return {}

def update_profile_with_audio(person_id: str, audio_insights: Dict) -> Dict:
    """
    Update existing profile with insights from audio analysis.
    
    Args:
        person_id (str): ID of the person
        audio_insights (Dict): Insights extracted from audio analysis
        
    Returns:
        Dict: Updated profile data
    """
    try:
        # Get existing profile
        profile = get_profile_by_id(person_id)
        if not profile:
            raise ValueError(f"Profile not found for person_id: {person_id}")
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Prepare context for profile update
        context = f"""
        Current profile:
        {json.dumps(profile, indent=2)}
        
        New audio insights:
        {json.dumps(audio_insights, indent=2)}
        
        Update the profile by:
        1. Adding new interests from audio_insights['new_interests']
        2. Updating communication style based on audio_insights['communication_style']
        3. Adding new key points to the profile
        4. Incorporating any new information while maintaining existing data
        
        Return the complete updated profile as a JSON object.
        """
        
        # Generate updated profile
        response = model.generate_content(context)
        
        try:
            updated_profile = json.loads(response.text)
            
            # Save updated profile
            save_profile(
                updated_profile['person']['first_name'],
                updated_profile['person']['last_name'],
                updated_profile
            )
            
            return updated_profile
            
        except json.JSONDecodeError:
            raise ValueError("Failed to parse updated profile from AI response")
            
    except Exception as e:
        print(f"Error updating profile with audio insights: {str(e)}")
        raise 