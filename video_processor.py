import subprocess
import os

try:
    subprocess.run(["pip", "install", "faster-whisper==0.10.0", "--no-deps"], check=True)
    subprocess.run(["pip", "install", "torchaudio"], check=True)
    os.environ["USE_PYTORCH_AUDIO"] = "1"
except Exception as e:
    print(f"Runtime install failed: {e}")


from faster_whisper import WhisperModel
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
        model = WhisperModel("base", device="cpu", compute_type="int8")
        
        # Transcribe audio
        segments, info = model.transcribe(temp_path, language="ru")
        transcription = " ".join([segment.text for segment in segments])
        
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
        
        # First, translate the content to English
        translation_prompt = f"""
        Translate the following text to English. Keep the original meaning and context intact:
        
        {transcription}
        
        Provide only the English translation, nothing else.
        """
        
        translation_response = model.generate_content(translation_prompt)
        english_transcription = translation_response.text.strip()
        
        # Now analyze the English translation
        analysis_prompt = f"""
        You are a precise JSON generator. Analyze this English text and create a valid JSON object.
        Follow these rules strictly:
        1. Output ONLY valid JSON
        2. Use double quotes for strings
        3. Escape any special characters in strings
        4. Do not include any text before or after the JSON
        5. Ensure all arrays and objects are properly closed
        6. Do not include any comments or explanations

        Text to analyze:
        {english_transcription}
        
        Create a JSON object with this exact structure:
        {{
            "topics": ["topic1", "topic2"],
            "communication_style": "style description",
            "key_points": ["point1", "point2"],
            "emotional_tone": "tone description",
            "new_interests": ["interest1", "interest2"],
            "notable_quotes": ["quote1", "quote2"]
        }}
        
        Rules for each field:
        1. topics: List main subjects discussed
        2. communication_style: Describe how the person communicates
        3. key_points: List important information or takeaways
        4. emotional_tone: Describe the overall emotional context
        5. new_interests: List any interests or preferences mentioned
        6. notable_quotes: List significant statements
        
        Output ONLY the JSON object, nothing else.
        """
        
        # Generate analysis
        response = model.generate_content(analysis_prompt)
        
        # Clean the response text to ensure it's valid JSON
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse the response as JSON
        try:
            insights = json.loads(response_text)
            # Add transcriptions separately after successful JSON parsing
            insights["language"] = "Russian"
            insights["original_transcription"] = transcription
            insights["english_transcription"] = english_transcription
            return insights
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Raw response: {response_text}")
            # If JSON parsing fails, try to extract structured information from the text
            return {
                "error": "Failed to parse AI response as JSON",
                "raw_response": response_text,
                "topics": ["Error in parsing response"],
                "communication_style": "Unable to analyze",
                "key_points": ["Please try again"],
                "emotional_tone": "Unable to analyze",
                "new_interests": [],
                "notable_quotes": [],
                "language": "Russian",
                "original_transcription": transcription,
                "english_transcription": english_transcription
            }
            
    except Exception as e:
        print(f"Error analyzing audio content: {str(e)}")
        return {
            "error": f"Error analyzing audio content: {str(e)}",
            "topics": ["Error in analysis"],
            "communication_style": "Unable to analyze",
            "key_points": ["Please try again"],
            "emotional_tone": "Unable to analyze",
            "new_interests": [],
            "notable_quotes": [],
            "language": "Russian",
            "original_transcription": transcription,
            "english_transcription": "Translation failed"
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
