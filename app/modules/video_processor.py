import os
import tempfile
from typing import Dict, List, Tuple
import ffmpeg
import whisper
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class VideoProcessor:
    def __init__(self):
        self.upload_folder = os.getenv("UPLOAD_FOLDER", "./data/uploads")
        self.max_content_length = int(os.getenv("MAX_CONTENT_LENGTH", 500000000))  # 500MB default
        self.whisper_model = None
        self._ensure_upload_folder()

    def _ensure_upload_folder(self):
        """Ensure the upload folder exists."""
        Path(self.upload_folder).mkdir(parents=True, exist_ok=True)

    async def process_video(self, video_path: str) -> Dict:
        """
        Process a video file: extract audio and perform speech recognition.
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            Dict: Dictionary containing:
                - audio_path: Path to extracted audio file
                - transcript: List of transcript segments
                - duration: Video duration in seconds
                - metadata: Video metadata
        """
        try:
            # Validate video file
            if not self._validate_video(video_path):
                raise ValueError("Invalid video file")

            # Extract metadata
            metadata = self._extract_metadata(video_path)
            
            # Extract audio
            audio_path = await self._extract_audio(video_path)
            
            # Perform speech recognition
            transcript = await self._transcribe_audio(audio_path)
            
            return {
                "audio_path": audio_path,
                "transcript": transcript,
                "duration": metadata.get("duration", 0),
                "metadata": metadata
            }

        except Exception as e:
            raise Exception(f"Error in process_video: {str(e)}")

    def _validate_video(self, video_path: str) -> bool:
        """Validate video file format and size."""
        try:
            # Check if file exists
            if not os.path.exists(video_path):
                return False
            
            # Check file size
            if os.path.getsize(video_path) > self.max_content_length:
                return False
            
            # Check if file is a valid video
            probe = ffmpeg.probe(video_path)
            if 'streams' not in probe:
                return False
            
            # Check if video stream exists
            has_video = any(stream['codec_type'] == 'video' for stream in probe['streams'])
            if not has_video:
                return False
            
            return True

        except Exception:
            return False

    def _extract_metadata(self, video_path: str) -> Dict:
        """Extract video metadata using ffmpeg."""
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next((stream for stream in probe['streams'] 
                               if stream['codec_type'] == 'video'), None)
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            return {
                "duration": float(probe['format'].get('duration', 0)),
                "width": int(video_stream.get('width', 0)),
                "height": int(video_stream.get('height', 0)),
                "codec": video_stream.get('codec_name', ''),
                "bitrate": int(probe['format'].get('bit_rate', 0)),
                "format": probe['format'].get('format_name', '')
            }

        except Exception as e:
            raise Exception(f"Error extracting metadata: {str(e)}")

    async def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video file using ffmpeg."""
        try:
            # Create temporary file for audio
            temp_dir = os.path.join(self.upload_folder, "temp")
            Path(temp_dir).mkdir(parents=True, exist_ok=True)
            
            audio_path = os.path.join(temp_dir, f"{Path(video_path).stem}_audio.wav")
            
            # Extract audio using ffmpeg
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, audio_path, acodec='pcm_s16le', ac=1, ar='16k')
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            return audio_path

        except Exception as e:
            raise Exception(f"Error extracting audio: {str(e)}")

    async def _transcribe_audio(self, audio_path: str) -> List[Dict]:
        """
        Transcribe audio using Whisper.
        
        Returns:
            List[Dict]: List of transcript segments with:
                - start: Start time in seconds
                - end: End time in seconds
                - text: Transcribed text
                - speaker: Speaker ID (to be filled by speaker identification)
        """
        try:
            # Load Whisper model if not loaded
            if self.whisper_model is None:
                self.whisper_model = whisper.load_model("base")
            
            # Transcribe audio
            result = self.whisper_model.transcribe(
                audio_path,
                language="en",  # Can be made configurable
                task="transcribe",
                verbose=False
            )
            
            # Format segments
            segments = []
            for segment in result["segments"]:
                segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "speaker": None  # To be filled by speaker identification
                })
            
            return segments

        except Exception as e:
            raise Exception(f"Error transcribing audio: {str(e)}")

    def cleanup(self, file_path: str):
        """Clean up temporary files."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up file {file_path}: {str(e)}") 