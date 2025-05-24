import os
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from pathlib import Path

from app.modules.search_module import SearchModule
from app.modules.profile_writer import ProfileWriter
from app.modules.video_processor import VideoProcessor
from app.modules.speaker_id import SpeakerIdentifier
from app.modules.meeting_analyzer import MeetingAnalyzer
from app.modules.chat_agent import ChatAgent

class Orchestrator:
    def __init__(self):
        # Initialize all modules
        self.search_module = SearchModule()
        self.profile_writer = ProfileWriter()
        self.video_processor = VideoProcessor()
        self.speaker_identifier = SpeakerIdentifier()
        self.meeting_analyzer = MeetingAnalyzer()
        self.chat_agent = ChatAgent()
        
        # Initialize data storage
        self.profiles_dir = Path("./data/profiles")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Active sessions
        self.active_sessions = {}

    async def create_profile(self, full_name: str) -> Dict:
        """
        Create a new profile for a person.
        
        Args:
            full_name (str): Full name of the person
            
        Returns:
            Dict: Created profile data
        """
        try:
            # Search for information
            search_data = await self.search_module.search_person(full_name)
            
            # Generate profile
            profile_data = await self.profile_writer.generate_profile(search_data, full_name)
            
            # Save profile
            profile_id = str(uuid.uuid4())
            profile_path = self.profiles_dir / f"{profile_id}.json"
            
            profile = {
                "id": profile_id,
                "full_name": full_name,
                "created_at": datetime.now().isoformat(),
                "profile_data": profile_data,
                "meetings": []
            }
            
            # Save to file
            import json
            with open(profile_path, 'w') as f:
                json.dump(profile, f, indent=2)
            
            return profile

        except Exception as e:
            raise Exception(f"Error creating profile: {str(e)}")

    async def process_meeting(
        self, 
        profile_id: str, 
        video_path: str
    ) -> Dict:
        """
        Process a meeting video and add it to a person's profile.
        
        Args:
            profile_id (str): ID of the person's profile
            video_path (str): Path to the meeting video file
            
        Returns:
            Dict: Meeting analysis data
        """
        try:
            # Load profile
            profile = self._load_profile(profile_id)
            if not profile:
                raise ValueError(f"Profile not found: {profile_id}")
            
            # Process video
            video_data = await self.video_processor.process_video(video_path)
            
            # Identify speakers
            transcript = await self.speaker_identifier.identify_speakers(
                video_data["audio_path"],
                video_data["transcript"]
            )
            
            # Get speaker summary
            speaker_summary = self.speaker_identifier.get_speaker_summary(transcript)
            
            # Analyze meeting
            meeting_analysis = await self.meeting_analyzer.analyze_meeting(
                transcript,
                speaker_summary
            )
            
            # Create meeting record
            meeting_id = str(uuid.uuid4())
            meeting = {
                "id": meeting_id,
                "date": datetime.now().isoformat(),
                "video_path": video_path,
                "transcript": transcript,
                "speaker_summary": speaker_summary,
                "analysis": meeting_analysis
            }
            
            # Add meeting to profile
            profile["meetings"].append(meeting)
            
            # Save updated profile
            self._save_profile(profile)
            
            # Cleanup temporary files
            self.video_processor.cleanup(video_data["audio_path"])
            
            return meeting

        except Exception as e:
            raise Exception(f"Error processing meeting: {str(e)}")

    async def chat(
        self, 
        profile_id: str, 
        query: str, 
        conversation_id: Optional[str] = None
    ) -> Dict:
        """
        Process a chat query about a person's profile.
        
        Args:
            profile_id (str): ID of the person's profile
            query (str): User's question
            conversation_id (Optional[str]): Conversation identifier
            
        Returns:
            Dict: Chat response
        """
        try:
            # Load profile
            profile = self._load_profile(profile_id)
            if not profile:
                raise ValueError(f"Profile not found: {profile_id}")
            
            # Get latest meeting data if available
            meeting_data = None
            if profile["meetings"]:
                latest_meeting = profile["meetings"][-1]
                meeting_data = latest_meeting["analysis"]
            
            # Process query
            response = await self.chat_agent.process_query(
                query,
                profile["profile_data"],
                meeting_data,
                conversation_id
            )
            
            return response

        except Exception as e:
            raise Exception(f"Error processing chat query: {str(e)}")

    def _load_profile(self, profile_id: str) -> Optional[Dict]:
        """Load profile data from file."""
        try:
            profile_path = self.profiles_dir / f"{profile_id}.json"
            if not profile_path.exists():
                return None
            
            import json
            with open(profile_path, 'r') as f:
                return json.load(f)
        
        except Exception as e:
            print(f"Error loading profile: {str(e)}")
            return None

    def _save_profile(self, profile: Dict):
        """Save profile data to file."""
        try:
            profile_path = self.profiles_dir / f"{profile['id']}.json"
            import json
            with open(profile_path, 'w') as f:
                json.dump(profile, f, indent=2)
        
        except Exception as e:
            raise Exception(f"Error saving profile: {str(e)}")

    def get_profile(self, profile_id: str) -> Optional[Dict]:
        """Get profile data by ID."""
        return self._load_profile(profile_id)

    def list_profiles(self) -> List[Dict]:
        """List all available profiles."""
        profiles = []
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                import json
                with open(profile_file, 'r') as f:
                    profile = json.load(f)
                    # Include only basic info in list
                    profiles.append({
                        "id": profile["id"],
                        "full_name": profile["full_name"],
                        "created_at": profile["created_at"],
                        "meetings_count": len(profile["meetings"])
                    })
            except Exception as e:
                print(f"Error reading profile {profile_file}: {str(e)}")
        
        return profiles

    def delete_profile(self, profile_id: str):
        """Delete a profile and all associated data."""
        try:
            profile_path = self.profiles_dir / f"{profile_id}.json"
            if profile_path.exists():
                # Load profile to get meeting video paths
                profile = self._load_profile(profile_id)
                if profile:
                    # Delete meeting videos
                    for meeting in profile["meetings"]:
                        video_path = meeting.get("video_path")
                        if video_path and os.path.exists(video_path):
                            os.remove(video_path)
                
                # Delete profile file
                os.remove(profile_path)
        
        except Exception as e:
            raise Exception(f"Error deleting profile: {str(e)}") 