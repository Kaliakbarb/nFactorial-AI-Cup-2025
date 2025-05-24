import os
from typing import Dict, List, Optional
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class ChatAgent:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Initialize conversation history
        self.conversation_history = {}

    async def process_query(
        self, 
        query: str, 
        profile_data: Optional[Dict] = None,
        meeting_data: Optional[Dict] = None,
        conversation_id: Optional[str] = None
    ) -> Dict:
        """
        Process user query and generate response based on available data.
        
        Args:
            query (str): User's question or request
            profile_data (Optional[Dict]): Person's profile data
            meeting_data (Optional[Dict]): Meeting analysis data
            conversation_id (Optional[str]): Unique conversation identifier
            
        Returns:
            Dict: Response containing:
                - answer: Main response to the query
                - suggestions: Related suggestions or follow-up questions
                - confidence: Confidence level in the response
        """
        try:
            # Initialize or retrieve conversation history
            if conversation_id:
                if conversation_id not in self.conversation_history:
                    self.conversation_history[conversation_id] = []
                history = self.conversation_history[conversation_id]
            else:
                history = []

            # Prepare context for the model
            context = self._prepare_context(query, profile_data, meeting_data, history)
            
            # Generate response using Gemini
            response = await self._generate_response(context)
            
            # Update conversation history
            if conversation_id:
                self.conversation_history[conversation_id].append({
                    "query": query,
                    "response": response["answer"],
                    "timestamp": datetime.now().isoformat()
                })
            
            return response

        except Exception as e:
            raise Exception(f"Error in process_query: {str(e)}")

    def _prepare_context(
        self, 
        query: str, 
        profile_data: Optional[Dict],
        meeting_data: Optional[Dict],
        history: List[Dict]
    ) -> str:
        """Prepare context for the model based on available data."""
        context = "User Query:\n"
        context += f"{query}\n\n"
        
        # Add profile data if available
        if profile_data:
            context += "Profile Information:\n"
            if "personality_traits" in profile_data:
                context += f"Personality Traits: {', '.join(profile_data['personality_traits'])}\n"
            if "communication_style" in profile_data:
                context += f"Communication Style: {profile_data['communication_style']}\n"
            if "interests" in profile_data:
                context += f"Interests: {', '.join(profile_data['interests'])}\n"
            if "recommendations" in profile_data:
                context += "Recommendations:\n"
                for key, value in profile_data["recommendations"].items():
                    if isinstance(value, list):
                        context += f"- {key}: {', '.join(value)}\n"
                    else:
                        context += f"- {key}: {value}\n"
        
        # Add meeting data if available
        if meeting_data:
            context += "\nMeeting Information:\n"
            if "topics" in meeting_data:
                context += f"Topics Discussed: {', '.join(meeting_data['topics'])}\n"
            if "action_items" in meeting_data:
                context += "Action Items:\n"
                for item in meeting_data["action_items"]:
                    context += f"- {item}\n"
            if "sentiment" in meeting_data:
                context += f"Meeting Sentiment: {meeting_data['sentiment']}\n"
        
        # Add conversation history if available
        if history:
            context += "\nPrevious Conversation:\n"
            for entry in history[-3:]:  # Include last 3 exchanges
                context += f"User: {entry['query']}\n"
                context += f"Assistant: {entry['response']}\n"
        
        return context

    async def _generate_response(self, context: str) -> Dict:
        """Generate response using Gemini."""
        prompt = f"""Based on the following context, provide a helpful and personalized response.
        Focus on being specific, actionable, and considerate of the person's communication style and preferences.

        {context}

        Please structure your response in the following format:

        1. Main Answer:
        - Direct response to the query
        - Specific recommendations or insights
        - Any relevant warnings or considerations

        2. Related Suggestions:
        - Additional topics to consider
        - Follow-up questions that might be helpful
        - Alternative approaches if applicable

        3. Confidence Level:
        - High: Very confident in the response
        - Medium: Some uncertainty but reasonable confidence
        - Low: Limited information available

        Be honest about the confidence level and any limitations in the available information."""

        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)

    def _parse_response(self, response: str) -> Dict:
        """Parse the model's response into structured format."""
        sections = response.split('\n\n')
        parsed_response = {
            "answer": "",
            "suggestions": [],
            "confidence": "Medium"  # Default confidence
        }
        
        current_section = None
        for section in sections:
            if "Main Answer:" in section:
                current_section = "answer"
                parsed_response["answer"] = section.replace("Main Answer:", "").strip()
            
            elif "Related Suggestions:" in section:
                current_section = "suggestions"
                suggestions = section.replace("Related Suggestions:", "").strip().split('\n')
                parsed_response["suggestions"] = [s.strip('- ') for s in suggestions if s.strip()]
            
            elif "Confidence Level:" in section:
                current_section = "confidence"
                confidence = section.replace("Confidence Level:", "").strip()
                if confidence in ["High", "Medium", "Low"]:
                    parsed_response["confidence"] = confidence
        
        return parsed_response

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Retrieve conversation history for a specific conversation."""
        return self.conversation_history.get(conversation_id, [])

    def clear_conversation_history(self, conversation_id: str):
        """Clear conversation history for a specific conversation."""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id] 