import os
from typing import Dict, List
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class ProfileWriter:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    async def generate_profile(self, search_data: Dict, full_name: str) -> Dict:
        """
        Generate a comprehensive personality profile using Gemini.
        
        Args:
            search_data (Dict): Data from search module
            full_name (str): Full name of the person
            
        Returns:
            Dict: Generated personality profile including:
                - personality_traits
                - communication_style
                - interests
                - professional_background
                - recommendations
        """
        try:
            # Prepare context for the model
            context = self._prepare_context(search_data, full_name)
            
            # Generate profile using Gemini
            prompt = self._create_prompt(context, full_name)
            response = await self._generate_with_gemini(prompt)
            
            # Parse and structure the response
            profile = self._parse_profile_response(response)
            
            return profile

        except Exception as e:
            raise Exception(f"Error in generate_profile: {str(e)}")

    def _prepare_context(self, search_data: Dict, full_name: str) -> str:
        """Prepare context from search data for the model."""
        context = f"Information about {full_name}:\n\n"
        
        # Add social profiles
        if search_data.get("social_profiles"):
            context += "Social Media Profiles:\n"
            for profile in search_data["social_profiles"]:
                context += f"- {profile['platform']}: {profile['snippet']}\n"
        
        # Add professional info
        if search_data.get("professional_info"):
            prof_info = search_data["professional_info"]
            context += "\nProfessional Information:\n"
            if prof_info.get("current_position"):
                context += f"- Current Position: {prof_info['current_position']}\n"
            if prof_info.get("company"):
                context += f"- Company: {prof_info['company']}\n"
        
        # Add news articles
        if search_data.get("news_articles"):
            context += "\nRecent News:\n"
            for article in search_data["news_articles"][:3]:  # Limit to 3 most recent
                context += f"- {article['title']}: {article['snippet']}\n"
        
        return context

    def _create_prompt(self, context: str, full_name: str) -> str:
        """Create a prompt for Gemini to generate the profile."""
        return f"""Based on the following information about {full_name}, generate a comprehensive personality and behavioral profile. 
        Focus on identifying key personality traits, communication style, interests, and professional background.
        Also provide specific recommendations for how to interact with this person effectively.

        Information:
        {context}

        Please structure your response in the following format:
        1. Personality Traits:
        2. Communication Style:
        3. Key Interests:
        4. Professional Background:
        5. Interaction Recommendations:
        6. Topics to Avoid:
        7. Conversation Starters:

        Be specific and actionable in your recommendations. If certain information is not available, indicate that in your response."""

    async def _generate_with_gemini(self, prompt: str) -> str:
        """Generate response using Gemini."""
        response = self.model.generate_content(prompt)
        return response.text

    def _parse_profile_response(self, response: str) -> Dict:
        """Parse the Gemini response into a structured profile."""
        sections = response.split('\n\n')
        profile = {
            "personality_traits": [],
            "communication_style": "",
            "interests": [],
            "professional_background": "",
            "recommendations": {
                "interaction_tips": [],
                "topics_to_avoid": [],
                "conversation_starters": []
            }
        }
        
        current_section = None
        for section in sections:
            if "Personality Traits:" in section:
                current_section = "personality_traits"
                traits = section.replace("Personality Traits:", "").strip().split('\n')
                profile["personality_traits"] = [t.strip('- ') for t in traits if t.strip()]
            
            elif "Communication Style:" in section:
                current_section = "communication_style"
                profile["communication_style"] = section.replace("Communication Style:", "").strip()
            
            elif "Key Interests:" in section:
                current_section = "interests"
                interests = section.replace("Key Interests:", "").strip().split('\n')
                profile["interests"] = [i.strip('- ') for i in interests if i.strip()]
            
            elif "Professional Background:" in section:
                current_section = "professional_background"
                profile["professional_background"] = section.replace("Professional Background:", "").strip()
            
            elif "Interaction Recommendations:" in section:
                current_section = "recommendations.interaction_tips"
                tips = section.replace("Interaction Recommendations:", "").strip().split('\n')
                profile["recommendations"]["interaction_tips"] = [t.strip('- ') for t in tips if t.strip()]
            
            elif "Topics to Avoid:" in section:
                current_section = "recommendations.topics_to_avoid"
                topics = section.replace("Topics to Avoid:", "").strip().split('\n')
                profile["recommendations"]["topics_to_avoid"] = [t.strip('- ') for t in topics if t.strip()]
            
            elif "Conversation Starters:" in section:
                current_section = "recommendations.conversation_starters"
                starters = section.replace("Conversation Starters:", "").strip().split('\n')
                profile["recommendations"]["conversation_starters"] = [s.strip('- ') for s in starters if s.strip()]
        
        return profile 