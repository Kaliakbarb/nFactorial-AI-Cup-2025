import google.generativeai as genai
import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=api_key)

def get_chat_response(profile: Dict, user_message: str) -> str:
    """
    Generate a response based on the person's profile and user message.
    
    Args:
        profile (Dict): Person's profile data
        user_message (str): User's message
        
    Returns:
        str: AI's response
    """
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Prepare context from profile
        context = prepare_profile_context(profile)
        
        # Generate response
        prompt = f"""
        You are an AI assistant helping someone communicate with {profile['person']['full_name']}.
        Use the following profile information to provide personalized advice and responses:
        
        {context}
        
        User message: {user_message}
        
        Provide a helpful response that:
        1. Is tailored to {profile['person']['full_name']}'s communication style and interests
        2. Offers specific suggestions based on their profile
        3. Maintains a professional and respectful tone
        4. Is concise and actionable
        
        Format your response in a conversational way, as if you're giving advice to a friend.
        """
        
        # Generate response
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error generating chat response: {str(e)}")
        return f"I apologize, but I encountered an error while processing your request. Please try again."

def prepare_profile_context(profile: Dict) -> str:
    """
    Prepare context from profile data for the LLM.
    
    Args:
        profile (Dict): Person's profile data
        
    Returns:
        str: Formatted context string
    """
    context_parts = []
    
    # Add basic information
    context_parts.append(f"Name: {profile['person']['full_name']}")
    context_parts.append(f"\nIntroduction: {profile['introduction']}")
    
    # Add interests
    context_parts.append("\nInterests:")
    for interest in profile['interests']:
        context_parts.append(f"- {interest}")
    
    # Add communication style
    context_parts.append(f"\nCommunication Style: {profile['communication_style']}")
    
    # Add communication tips
    context_parts.append("\nCommunication Tips:")
    for tip in profile['communication_tips']:
        context_parts.append(f"- {tip}")
    
    return "\n".join(context_parts) 