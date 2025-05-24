import os
from typing import Dict, List, Optional
import torch
from pyannote.audio import Pipeline
from dotenv import load_dotenv

load_dotenv()

class SpeakerIdentifier:
    def __init__(self):
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not self.hf_token:
            raise ValueError("HUGGINGFACE_TOKEN not found in environment variables")
        
        # Initialize pyannote pipeline
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=self.hf_token
        )
        
        # Move to GPU if available
        if torch.cuda.is_available():
            self.pipeline = self.pipeline.to(torch.device("cuda"))

    async def identify_speakers(self, audio_path: str, transcript: List[Dict]) -> List[Dict]:
        """
        Identify speakers in the audio and assign them to transcript segments.
        
        Args:
            audio_path (str): Path to the audio file
            transcript (List[Dict]): List of transcript segments from Whisper
            
        Returns:
            List[Dict]: Updated transcript segments with speaker IDs
        """
        try:
            # Perform speaker diarization
            diarization = self.pipeline(audio_path)
            
            # Convert diarization to segments
            diarization_segments = self._convert_diarization_to_segments(diarization)
            
            # Match transcript segments with speaker segments
            updated_transcript = self._match_speakers_with_transcript(
                transcript, 
                diarization_segments
            )
            
            return updated_transcript

        except Exception as e:
            raise Exception(f"Error in identify_speakers: {str(e)}")

    def _convert_diarization_to_segments(self, diarization) -> List[Dict]:
        """Convert pyannote diarization output to list of segments."""
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })
        return segments

    def _match_speakers_with_transcript(
        self, 
        transcript: List[Dict], 
        diarization_segments: List[Dict]
    ) -> List[Dict]:
        """
        Match transcript segments with speaker segments based on timing.
        
        Args:
            transcript: List of transcript segments from Whisper
            diarization_segments: List of speaker segments from pyannote
            
        Returns:
            List[Dict]: Updated transcript segments with speaker IDs
        """
        updated_transcript = []
        
        for segment in transcript:
            # Find overlapping speaker segments
            overlapping_speakers = []
            for speaker_segment in diarization_segments:
                if self._segments_overlap(segment, speaker_segment):
                    overlapping_speakers.append(speaker_segment)
            
            # Assign the most dominant speaker
            if overlapping_speakers:
                # Calculate overlap duration for each speaker
                speaker_durations = {}
                for speaker_segment in overlapping_speakers:
                    overlap_duration = self._calculate_overlap_duration(
                        segment, 
                        speaker_segment
                    )
                    speaker = speaker_segment["speaker"]
                    speaker_durations[speaker] = speaker_durations.get(speaker, 0) + overlap_duration
                
                # Get the speaker with maximum overlap
                dominant_speaker = max(
                    speaker_durations.items(), 
                    key=lambda x: x[1]
                )[0]
                
                segment["speaker"] = dominant_speaker
            else:
                segment["speaker"] = "UNKNOWN"
            
            updated_transcript.append(segment)
        
        return updated_transcript

    def _segments_overlap(self, segment1: Dict, segment2: Dict) -> bool:
        """Check if two segments overlap in time."""
        return not (segment1["end"] <= segment2["start"] or 
                   segment2["end"] <= segment1["start"])

    def _calculate_overlap_duration(self, segment1: Dict, segment2: Dict) -> float:
        """Calculate the duration of overlap between two segments."""
        overlap_start = max(segment1["start"], segment2["start"])
        overlap_end = min(segment1["end"], segment2["end"])
        return max(0, overlap_end - overlap_start)

    def get_speaker_summary(self, transcript: List[Dict]) -> Dict:
        """
        Generate a summary of speaker participation.
        
        Args:
            transcript: List of transcript segments with speaker IDs
            
        Returns:
            Dict: Summary of speaker participation including:
                - total_duration: Total duration of the meeting
                - speaker_stats: Dictionary with speaker statistics
        """
        speaker_stats = {}
        total_duration = 0
        
        for segment in transcript:
            speaker = segment["speaker"]
            duration = segment["end"] - segment["start"]
            
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    "total_duration": 0,
                    "segment_count": 0,
                    "total_words": len(segment["text"].split())
                }
            else:
                speaker_stats[speaker]["total_duration"] += duration
                speaker_stats[speaker]["segment_count"] += 1
                speaker_stats[speaker]["total_words"] += len(segment["text"].split())
            
            total_duration = max(total_duration, segment["end"])
        
        # Calculate percentages
        for speaker in speaker_stats:
            speaker_stats[speaker]["percentage"] = (
                speaker_stats[speaker]["total_duration"] / total_duration * 100
            )
        
        return {
            "total_duration": total_duration,
            "speaker_stats": speaker_stats
        } 