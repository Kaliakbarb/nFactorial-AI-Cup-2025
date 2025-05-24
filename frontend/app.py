import streamlit as st
import requests
import json
from datetime import datetime
import uuid
from typing import Dict, List, Optional
import os
import time

# API configuration
API_URL = os.getenv("API_URL", "http://localhost:8001")  # Get from environment or use default
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Page configuration
st.set_page_config(
    page_title="PersonaAnalyst",
    page_icon="👤",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #2b313e;
    }
    .chat-message.assistant {
        background-color: #262730;
    }
    .chat-message .content {
        display: flex;
    }
    </style>
""", unsafe_allow_html=True)

# Session state initialization
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if "selected_profile" not in st.session_state:
    st.session_state.selected_profile = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def make_request(method: str, endpoint: str, **kwargs) -> Optional[Dict]:
    """Make an HTTP request with retries."""
    url = f"{API_URL}{endpoint}"
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:  # Last attempt
                st.error(f"Error connecting to backend: {str(e)}")
                st.error("Please make sure the backend server is running at " + API_URL)
                return None
            time.sleep(RETRY_DELAY)
    return None

def create_profile(full_name: str) -> Optional[Dict]:
    """Create a new profile."""
    return make_request("POST", "/profiles", json={"full_name": full_name})

def list_profiles() -> List[Dict]:
    """List all profiles."""
    result = make_request("GET", "/profiles")
    return result if result is not None else []

def get_profile(profile_id: str) -> Optional[Dict]:
    """Get detailed profile information."""
    return make_request("GET", f"/profiles/{profile_id}")

def delete_profile(profile_id: str) -> bool:
    """Delete a profile."""
    result = make_request("DELETE", f"/profiles/{profile_id}")
    return result is not None

def process_meeting(profile_id: str, video_file) -> Optional[Dict]:
    """Process a meeting video."""
    return make_request("POST", f"/profiles/{profile_id}/meetings", files={"video": video_file})

def chat(profile_id: str, query: str, conversation_id: str) -> Optional[Dict]:
    """Send a chat query."""
    return make_request("POST", f"/profiles/{profile_id}/chat", 
                       json={"query": query, "conversation_id": conversation_id})

# Sidebar
with st.sidebar:
    st.title("PersonaAnalyst")
    
    # Create new profile
    st.subheader("Create New Profile")
    new_name = st.text_input("Full Name")
    if st.button("Create Profile"):
        if new_name:
            profile = create_profile(new_name)
            if profile:
                st.success(f"Profile created for {new_name}")
                st.rerun()
        else:
            st.warning("Please enter a name")
    
    # Profile selection
    st.subheader("Select Profile")
    profiles = list_profiles()
    if profiles:
        selected = st.selectbox(
            "Choose a profile",
            options=profiles,
            format_func=lambda x: x["full_name"]
        )
        if selected:
            st.session_state.selected_profile = selected["id"]
    else:
        st.info("No profiles available. Create one to get started!")

# Main content
if st.session_state.selected_profile:
    profile = get_profile(st.session_state.selected_profile)
    if profile:
        # Profile header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title(f"Profile: {profile['full_name']}")
        with col2:
            if st.button("Delete Profile", type="secondary"):
                if delete_profile(profile["id"]):
                    st.session_state.selected_profile = None
                    st.rerun()
        
        # Tabs for different sections
        tab1, tab2, tab3 = st.tabs(["Profile", "Meetings", "Chat"])
        
        # Profile tab
        with tab1:
            st.subheader("Profile Information")
            if "profile_data" in profile:
                data = profile["profile_data"]
                
                # Personality traits
                if "personality_traits" in data:
                    st.write("### Personality Traits")
                    for trait in data["personality_traits"]:
                        st.write(f"- {trait}")
                
                # Communication style
                if "communication_style" in data:
                    st.write("### Communication Style")
                    st.write(data["communication_style"])
                
                # Interests
                if "interests" in data:
                    st.write("### Interests")
                    for interest in data["interests"]:
                        st.write(f"- {interest}")
                
                # Recommendations
                if "recommendations" in data:
                    st.write("### Recommendations")
                    for key, value in data["recommendations"].items():
                        st.write(f"#### {key.replace('_', ' ').title()}")
                        if isinstance(value, list):
                            for item in value:
                                st.write(f"- {item}")
                        else:
                            st.write(value)
        
        # Meetings tab
        with tab2:
            st.subheader("Meetings")
            
            # Upload new meeting
            uploaded_file = st.file_uploader(
                "Upload Meeting Video",
                type=["mp4"],
                help="Upload a Google Meet recording (MP4 format)"
            )
            if uploaded_file:
                if st.button("Process Meeting"):
                    with st.spinner("Processing meeting..."):
                        result = process_meeting(profile["id"], uploaded_file)
                        if result:
                            st.success("Meeting processed successfully!")
                            st.rerun()
            
            # Display meetings
            if "meetings" in profile and profile["meetings"]:
                for meeting in reversed(profile["meetings"]):
                    with st.expander(f"Meeting on {meeting['date']}"):
                        # Meeting summary
                        if "analysis" in meeting:
                            analysis = meeting["analysis"]
                            
                            # Topics
                            if "topics" in analysis:
                                st.write("### Topics Discussed")
                                for topic in analysis["topics"]:
                                    st.write(f"- {topic}")
                            
                            # Action items
                            if "action_items" in analysis:
                                st.write("### Action Items")
                                for item in analysis["action_items"]:
                                    st.write(f"- {item}")
                            
                            # Key points
                            if "key_points" in analysis:
                                st.write("### Key Points")
                                for point in analysis["key_points"]:
                                    st.write(f"- {point}")
                            
                            # Sentiment
                            if "sentiment" in analysis:
                                st.write("### Meeting Sentiment")
                                st.write(analysis["sentiment"])
                            
                            # Summary
                            if "summary" in analysis:
                                st.write("### Summary")
                                st.write(analysis["summary"])
            else:
                st.info("No meetings available. Upload a meeting recording to get started!")
        
        # Chat tab
        with tab3:
            st.subheader("Chat with AI Assistant")
            
            # Display chat history
            for message in st.session_state.chat_history:
                with st.container():
                    st.markdown(f"""
                        <div class="chat-message {message['role']}">
                            <div class="content">
                                <div>
                                    <strong>{message['role'].title()}:</strong>
                                    <p>{message['content']}</p>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            
            # Chat input
            query = st.text_input("Ask a question about this person")
            if st.button("Send"):
                if query:
                    # Add user message to history
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": query
                    })
                    
                    # Get AI response
                    response = chat(
                        profile["id"],
                        query,
                        st.session_state.conversation_id
                    )
                    
                    if response:
                        # Add AI response to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response["answer"]
                        })
                        
                        # Display suggestions if available
                        if "suggestions" in response and response["suggestions"]:
                            st.write("### Related Questions")
                            for suggestion in response["suggestions"]:
                                if st.button(suggestion, key=suggestion):
                                    st.session_state.chat_history.append({
                                        "role": "user",
                                        "content": suggestion
                                    })
                                    new_response = chat(
                                        profile["id"],
                                        suggestion,
                                        st.session_state.conversation_id
                                    )
                                    if new_response:
                                        st.session_state.chat_history.append({
                                            "role": "assistant",
                                            "content": new_response["answer"]
                                        })
                                    st.rerun()
                    st.rerun()
else:
    st.info("Select a profile from the sidebar to get started!") 