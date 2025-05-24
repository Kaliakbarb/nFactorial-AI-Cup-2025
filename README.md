# PersonaAnalyst 🔍

An AI-powered tool for analyzing people's profiles and generating insights for better communication.

## Features

- **Profile Analysis**: Search and analyze public information about a person
- **Video Analysis**: Process video recordings to extract insights
- **Chat Interface**: Ask questions about how to interact with the person

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd persona-analyst
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:
```
SERPAPI_API_KEY=your_serpapi_key
GOOGLE_API_KEY=your_google_api_key
```

5. Run the application:
```bash
streamlit run main.py
```

## Project Structure

- `main.py` - Main Streamlit application
- `serpapi_handler.py` - SerpAPI integration for web search
- `llm_profile.py` - Profile generation using Gemini API
- `video_processor.py` - Video processing and transcription
- `speaker_identifier.py` - Speaker identification
- `chat_agent.py` - Chat interface for questions
- `data/` - Directory for storing profiles and analysis results

## Dependencies

- Streamlit - Web interface
- Google Generative AI - LLM for profile generation
- SerpAPI - Web search
- Whisper - Speech recognition
- FFmpeg - Video processing
- SQLAlchemy - Database ORM

## Usage

1. **Profile Analysis**
   - Enter the person's first and last name
   - Click "Analyze Profile" to generate insights

2. **Video Analysis**
   - Upload an MP4 video file
   - The system will process the video and extract insights

3. **Chat**
   - Ask questions about how to interact with the person
   - Get AI-powered recommendations based on the analysis

## License

MIT License 