import streamlit as st
import os
from dotenv import load_dotenv
from serpapi_handler import search_person, get_social_profiles
from llm_profile import generate_profile, save_profile, get_all_profiles, get_profile_by_id, update_profile_with_audio
from video_processor import process_audio, get_transcriptions
from chat_agent import get_chat_response
# TODO: Implement these modules
# from speaker_identifier import identify_speaker

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="PersonaAnalyst",
    page_icon="🔍",
    layout="wide"
)

# Main title
st.title("PersonaAnalyst 🔍")
st.subheader("AI-powered Person Analysis Tool")

# Initialize session state for selected profile
if "selected_profile" not in st.session_state:
    st.session_state.selected_profile = None

# Sidebar for navigation
page = st.sidebar.selectbox(
    "Choose a page",
    ["Profile Analysis", "Video Analysis", "Chat"]
)

# Profile selection in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Saved Profiles")

# Get all saved profiles
profiles = get_all_profiles()
if profiles:
    profile_names = [f"{p['person']['first_name']} {p['person']['last_name']}" for p in profiles]
    selected_name = st.sidebar.selectbox("Select a profile", profile_names)
    
    if selected_name:
        selected_profile = next((p for p in profiles if f"{p['person']['first_name']} {p['person']['last_name']}" == selected_name), None)
        st.session_state.selected_profile = selected_profile
else:
    st.sidebar.info("No profiles saved yet. Create a profile in the Profile Analysis page.")

def main():
    if page == "Profile Analysis":
        show_profile_analysis()
    elif page == "Video Analysis":
        show_video_analysis()
    else:
        show_chat_assistant()

def show_profile_analysis():
    st.header("Profile Analysis")
    
    # Input fields
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    
    if st.button("Analyze Profile"):
        if first_name and last_name:
            with st.spinner("Searching for information..."):
                # Search for person
                search_results = search_person(first_name, last_name)
                
                if "error" in search_results:
                    st.error(f"Error during search: {search_results['error']}")
                else:
                    # Display social profiles
                    social_profiles = get_social_profiles(search_results)
                    if social_profiles:
                        st.subheader("Social Media Profiles")
                        for profile in social_profiles:
                            st.markdown(f"**{profile['platform']}**: [{profile['title']}]({profile['url']})")
                            st.markdown(f"_{profile['snippet']}_")
                    
                    # Generate profile
                    with st.spinner("Generating profile..."):
                        profile_data = generate_profile(search_results)
                        
                        if "error" in profile_data:
                            st.error(f"Error generating profile: {profile_data['error']}")
                        else:
                            # Display profile information
                            st.subheader("Profile Analysis")
                            
                            st.markdown("### Introduction")
                            st.write(profile_data["introduction"])
                            
                            st.markdown("### Interests")
                            for interest in profile_data["interests"]:
                                st.markdown(f"- {interest}")
                            
                            st.markdown("### Communication Style")
                            st.write(profile_data["communication_style"])
                            
                            st.markdown("### Communication Tips")
                            for tip in profile_data["communication_tips"]:
                                st.markdown(f"- {tip}")
                            
                            # Save profile
                            filepath = save_profile(first_name, last_name, profile_data)
                            st.success(f"Profile saved successfully to {filepath}")
                            
                            # Update the sidebar
                            st.experimental_rerun()
        else:
            st.error("Please enter both first and last name")

def show_video_analysis():
    st.header("Video Analysis")
    
    # Get all profiles
    profiles = get_all_profiles()
    
    if not profiles:
        st.warning("No profiles available. Please generate a profile first.")
        return
    
    # Profile selection
    profile_options = {f"{p['person']['full_name']}": p for p in profiles}
    selected_name = st.selectbox(
        "Select a person to analyze audio for",
        options=list(profile_options.keys())
    )
    
    selected_profile = profile_options[selected_name]
    
    # Display current profile information
    with st.expander("Current Profile Information"):
        st.write(f"**Introduction:** {selected_profile['introduction']}")
        st.write("**Interests:**")
        for interest in selected_profile['interests']:
            st.write(f"- {interest}")
        st.write(f"**Communication Style:** {selected_profile['communication_style']}")
    
    # Audio file upload
    uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"])
    
    if uploaded_file:
        # Process audio
        with st.spinner("Processing audio..."):
            result = process_audio(uploaded_file, selected_profile['person']['id'])
            
            if "error" in result:
                st.error(result["error"])
            else:
                # Display transcription
                st.subheader("Transcription")
                st.write(result["transcription"])
                
                # Display insights
                st.subheader("Audio Analysis Insights")
                insights = result["insights"]
                
                if "error" in insights:
                    st.error(insights["error"])
                else:
                    # Display topics
                    st.write("**Topics Discussed:**")
                    for topic in insights["topics"]:
                        st.write(f"- {topic}")
                    
                    # Display communication style
                    st.write(f"**Communication Style:** {insights['communication_style']}")
                    
                    # Display key points
                    st.write("**Key Points:**")
                    for point in insights["key_points"]:
                        st.write(f"- {point}")
                    
                    # Display emotional tone
                    st.write(f"**Emotional Tone:** {insights['emotional_tone']}")
                    
                    # Display new interests
                    if insights["new_interests"]:
                        st.write("**New Interests Identified:**")
                        for interest in insights["new_interests"]:
                            st.write(f"- {interest}")
                    
                    # Display notable quotes
                    if insights["notable_quotes"]:
                        st.write("**Notable Quotes:**")
                        for quote in insights["notable_quotes"]:
                            st.write(f"- {quote}")
                    
                    # Automatically update profile with insights
                    try:
                        updated_profile = update_profile_with_audio(
                            selected_profile['person']['id'],
                            insights
                        )
                        st.success("Profile updated successfully with new insights!")
                        
                        # Show updated profile
                        with st.expander("View Updated Profile"):
                            st.write(f"**Introduction:** {updated_profile['introduction']}")
                            st.write("**Interests:**")
                            for interest in updated_profile['interests']:
                                st.write(f"- {interest}")
                            st.write(f"**Communication Style:** {updated_profile['communication_style']}")
                            
                    except Exception as e:
                        st.error(f"Error updating profile: {str(e)}")

def show_chat_assistant():
    st.header("Chat Assistant")
    
    # Get all profiles
    profiles = get_all_profiles()
    
    if not profiles:
        st.warning("No profiles available. Please generate a profile first.")
        return
    
    # Profile selection
    profile_options = {f"{p['person']['full_name']}": p for p in profiles}
    selected_name = st.selectbox(
        "Select a person to chat about",
        options=list(profile_options.keys())
    )
    
    selected_profile = profile_options[selected_name]
    
    # Display profile summary
    with st.expander("View Profile Summary"):
        st.write(f"**Introduction:** {selected_profile['introduction']}")
        st.write("**Interests:**")
        for interest in selected_profile['interests']:
            st.write(f"- {interest}")
        st.write(f"**Communication Style:** {selected_profile['communication_style']}")
    
    # Chat interface
    st.subheader("Chat with AI Assistant")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about how to communicate with this person..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_chat_response(selected_profile, prompt)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

main() 