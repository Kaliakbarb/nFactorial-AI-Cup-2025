# PersonaAnalyst

PersonaAnalyst is a multimodal AI assistant that helps analyze and understand people through various data sources, including social media profiles, articles, and meeting recordings.

## Features

- 🔍 Automated profile creation from public data
- 🎥 Meeting analysis with speaker identification
- 💬 Smart chat interface for personalized recommendations
- 📊 Comprehensive personality and behavioral analysis
- 🔒 Privacy-focused with local data processing

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/persona-analyst.git
cd persona-analyst
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment template and fill in your API keys:
```bash
cp .env.example .env
```

5. Run the application:
```bash
# Backend
uvicorn app.main:app --reload

# Frontend (Streamlit)
streamlit run frontend/app.py
```

## Project Structure

```
persona-analyst/
├── app/
│   ├── modules/
│   │   ├── search_module.py
│   │   ├── profile_writer.py
│   │   ├── video_processor.py
│   │   ├── speaker_id.py
│   │   ├── meeting_analyzer.py
│   │   └── chat_agent.py
│   ├── orchestrator.py
│   └── main.py
├── frontend/
│   └── app.py
├── data/
│   ├── uploads/
│   └── profiles/
├── tests/
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

## API Keys Required

- SerpAPI (for web search)
- Google API (for Gemini)
- OpenAI API (for Whisper)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details 