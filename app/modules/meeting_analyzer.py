import os
from typing import Dict, List, Optional
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MeetingAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    async def analyze_meeting(self, transcript: List[Dict], speaker_summary: Dict) -> Dict:
        """
        Analyze meeting transcript and generate comprehensive summary.
        
        Args:
            transcript (List[Dict]): List of transcript segments with speaker IDs
            speaker_summary (Dict): Summary of speaker participation
            
        Returns:
            Dict: Meeting analysis including:
                - topics: List of discussed topics
                - action_items: List of action items and deadlines
                - key_points: List of key discussion points
                - sentiment: Overall meeting sentiment
                - summary: Meeting summary
        """
        try:
            # Prepare context for analysis
            context = self._prepare_context(transcript, speaker_summary)
            
            # Generate analysis using Gemini
            analysis = await self._generate_analysis(context)
            
            # Extract structured information
            structured_analysis = self._extract_structured_info(analysis)
            
            # Add speaker-specific insights
            structured_analysis["speaker_insights"] = self._analyze_speaker_contributions(
                transcript, 
                speaker_summary
            )
            
            return structured_analysis

        except Exception as e:
            raise Exception(f"Error in analyze_meeting: {str(e)}")

    def _prepare_context(self, transcript: List[Dict], speaker_summary: Dict) -> str:
        """Prepare context from transcript and speaker summary for analysis."""
        context = "Meeting Transcript:\n\n"
        
        # Add transcript with speaker information
        for segment in transcript:
            context += f"[{segment['speaker']}] ({segment['start']:.1f}s - {segment['end']:.1f}s): {segment['text']}\n"
        
        # Add speaker participation summary
        context += "\nSpeaker Participation Summary:\n"
        for speaker, stats in speaker_summary["speaker_stats"].items():
            context += f"- {speaker}: {stats['percentage']:.1f}% of meeting time, {stats['total_words']} words\n"
        
        return context

    async def _generate_analysis(self, context: str) -> str:
        """Generate meeting analysis using Gemini."""
        prompt = f"""Analyze the following meeting transcript and provide a comprehensive analysis.
        Focus on identifying key topics, action items, deadlines, and overall sentiment.

        {context}

        Please structure your response in the following format:

        1. Key Topics:
        - List the main topics discussed
        - Include brief context for each topic

        2. Action Items:
        - List all action items mentioned
        - Include who is responsible and any deadlines
        - Note any commitments made

        3. Key Discussion Points:
        - List the most important points discussed
        - Include any decisions made
        - Note any areas of agreement or disagreement

        4. Meeting Sentiment:
        - Overall tone of the meeting
        - Any notable emotional moments
        - Level of engagement

        5. Summary:
        - Brief overview of the meeting
        - Main outcomes
        - Next steps

        Be specific and actionable in your analysis. If certain information is not available, indicate that in your response."""

        response = self.model.generate_content(prompt)
        return response.text

    def _extract_structured_info(self, analysis: str) -> Dict:
        """Extract structured information from the analysis text."""
        sections = analysis.split('\n\n')
        structured_info = {
            "topics": [],
            "action_items": [],
            "key_points": [],
            "sentiment": "",
            "summary": ""
        }
        
        current_section = None
        for section in sections:
            if "Key Topics:" in section:
                current_section = "topics"
                topics = section.replace("Key Topics:", "").strip().split('\n')
                structured_info["topics"] = [t.strip('- ') for t in topics if t.strip()]
            
            elif "Action Items:" in section:
                current_section = "action_items"
                items = section.replace("Action Items:", "").strip().split('\n')
                structured_info["action_items"] = [i.strip('- ') for i in items if i.strip()]
            
            elif "Key Discussion Points:" in section:
                current_section = "key_points"
                points = section.replace("Key Discussion Points:", "").strip().split('\n')
                structured_info["key_points"] = [p.strip('- ') for p in points if p.strip()]
            
            elif "Meeting Sentiment:" in section:
                current_section = "sentiment"
                structured_info["sentiment"] = section.replace("Meeting Sentiment:", "").strip()
            
            elif "Summary:" in section:
                current_section = "summary"
                structured_info["summary"] = section.replace("Summary:", "").strip()
        
        return structured_info

    def _analyze_speaker_contributions(
        self, 
        transcript: List[Dict], 
        speaker_summary: Dict
    ) -> Dict:
        """Analyze individual speaker contributions and patterns."""
        speaker_insights = {}
        
        for speaker, stats in speaker_summary["speaker_stats"].items():
            # Get all segments for this speaker
            speaker_segments = [
                segment for segment in transcript 
                if segment["speaker"] == speaker
            ]
            
            # Analyze speaking patterns
            insights = {
                "total_contributions": len(speaker_segments),
                "average_segment_length": stats["total_words"] / len(speaker_segments) if speaker_segments else 0,
                "participation_percentage": stats["percentage"],
                "key_contributions": self._extract_key_contributions(speaker_segments),
                "interaction_patterns": self._analyze_interactions(speaker_segments, transcript)
            }
            
            speaker_insights[speaker] = insights
        
        return speaker_insights

    def _extract_key_contributions(self, segments: List[Dict]) -> List[str]:
        """Extract key contributions from speaker segments."""
        # Simple heuristic: longer segments might be more significant
        sorted_segments = sorted(segments, key=lambda x: len(x["text"].split()), reverse=True)
        return [segment["text"] for segment in sorted_segments[:3]]  # Top 3 contributions

    def _analyze_interactions(
        self, 
        speaker_segments: List[Dict], 
        full_transcript: List[Dict]
    ) -> Dict:
        """Analyze speaker's interaction patterns with others."""
        interactions = {
            "responds_to": {},
            "interrupted_by": {},
            "interrupts": {}
        }
        
        for i, segment in enumerate(speaker_segments):
            # Find previous speaker
            if i > 0:
                prev_segment = speaker_segments[i-1]
                if prev_segment["speaker"] != segment["speaker"]:
                    interactions["responds_to"][prev_segment["speaker"]] = \
                        interactions["responds_to"].get(prev_segment["speaker"], 0) + 1
            
            # Check for interruptions
            for other_segment in full_transcript:
                if other_segment["speaker"] != segment["speaker"]:
                    if self._is_interruption(segment, other_segment):
                        if other_segment["start"] < segment["start"]:
                            interactions["interrupted_by"][other_segment["speaker"]] = \
                                interactions["interrupted_by"].get(other_segment["speaker"], 0) + 1
                        else:
                            interactions["interrupts"][other_segment["speaker"]] = \
                                interactions["interrupts"].get(other_segment["speaker"], 0) + 1
        
        return interactions

    def _is_interruption(self, segment1: Dict, segment2: Dict) -> bool:
        """Check if two segments represent an interruption."""
        # Consider it an interruption if segments overlap significantly
        overlap = min(segment1["end"], segment2["end"]) - max(segment1["start"], segment2["start"])
        return overlap > 0.5  # More than 0.5 seconds overlap 