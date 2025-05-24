import os
import whisper
import tempfile
from typing import Dict, Optional
import json
from datetime import datetime
import ssl
import certifi
import urllib.request
import google.generativeai as genai
from dotenv import load_dotenv
import librosa
import soundfile as sf

# Load environment variables
load_dotenv()

# Configure SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())
urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context)))

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=api_key)

def process_audio(audio_file_path: str, person_id: str) -> Dict:
    """
    Process audio file and generate transcription.
    
    Args:
        audio_file_path (str): Path to the audio file
        person_id (str): ID of the person whose audio is being processed
        
    Returns:
        Dict: Dictionary containing transcription and analysis results
    """
    try:
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
            
        # Load and process audio
        y, sr = librosa.load(audio_file_path)
        sf.write(temp_path, y, sr)
        
        # Load Whisper model
        model = whisper.load_model("base")
        
        # Transcribe audio
        result = model.transcribe(temp_path)
        transcription = result["text"]
        
        # Analyze the transcription
        insights = analyze_audio_content(transcription)
        
        # Save transcription and insights
        output = {
            "transcription": transcription,
            "insights": insights,
            "person_id": person_id
        }
        
        # Save to JSON file
        output_path = os.path.join("data", "transcriptions", f"{person_id}_transcription.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return output
        
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return {
            "error": f"Error processing audio: {str(e)}"
        }

def analyze_audio_content(transcription: str) -> Dict:
    """
    Analyze audio content using Gemini to extract insights.
    
    Args:
        transcription (str): The transcribed text from audio
        
    Returns:
        Dict: Structured data containing insights from the audio
    """
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Create prompt for analysis
        prompt = f"""
        Analyze the following transcribed audio content and extract key insights:
        
        {transcription}
        
        Provide a structured analysis including:
        1. Main topics discussed
        2. Communication style and patterns
        3. Key points or important information
        4. Emotional tone and sentiment
        5. New interests or preferences mentioned
        6. Any notable quotes or statements
        
        Format the response as a JSON object with the following structure:
        {{
            "topics": ["topic1", "topic2", ...],
            "communication_style": "description of communication style",
            "key_points": ["point1", "point2", ...],
            "emotional_tone": "description of emotional tone",
            "new_interests": ["interest1", "interest2", ...],
            "notable_quotes": ["quote1", "quote2", ...]
        }}
        """
        
        # Generate analysis
        response = model.generate_content(prompt)
        
        # Parse the response as JSON
        try:
            insights = json.loads(response.text)
            return insights
        except json.JSONDecodeError:
            # If JSON parsing fails, return a structured error
            return {
                "error": "Failed to parse AI response",
                "raw_response": response.text
            }
            
    except Exception as e:
        print(f"Error analyzing audio content: {str(e)}")
        return {
            "error": f"Error analyzing audio content: {str(e)}"
        }

def save_transcription(transcription_data: Dict) -> str:
    """
    Save transcription to a JSON file.
    
    Args:
        transcription_data (Dict): Transcription data to save
        
    Returns:
        str: Path to the saved transcription file
    """
    try:
        # Create transcriptions directory if it doesn't exist
        transcriptions_dir = os.path.join("data", "transcriptions")
        os.makedirs(transcriptions_dir, exist_ok=True)
        
        # Create filename
        profile_id = transcription_data["profile_id"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{profile_id}_transcription_{timestamp}.json"
        filepath = os.path.join(transcriptions_dir, filename)
        
        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(transcription_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    except Exception as e:
        print(f"Error saving transcription: {str(e)}")
        raise

def get_transcriptions(profile_id: str) -> list:
    """
    Get all transcriptions for a specific profile.
    
    Args:
        profile_id (str): Profile ID to get transcriptions for
        
    Returns:
        list: List of transcription data
    """
    transcriptions = []
    transcriptions_dir = os.path.join("data", "transcriptions")
    
    if not os.path.exists(transcriptions_dir):
        return transcriptions
    
    for filename in os.listdir(transcriptions_dir):
        if filename.startswith(f"{profile_id}_transcription_"):
            filepath = os.path.join(transcriptions_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    transcription_data = json.load(f)
                    transcriptions.append(transcription_data)
            except Exception as e:
                print(f"Error reading transcription {filename}: {str(e)}")
    
    return transcriptions

def get_transcription(person_id: str) -> Optional[Dict]:
    """
    Get transcription and insights for a specific person.
    
    Args:
        person_id (str): ID of the person
        
    Returns:
        Optional[Dict]: Dictionary containing transcription and insights, or None if not found
    """
    try:
        file_path = os.path.join("data", "transcriptions", f"{person_id}_transcription.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Error getting transcription: {str(e)}")
        return None 