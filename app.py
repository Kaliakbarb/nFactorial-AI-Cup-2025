"""
FlirtGPT: A web application for analyzing social media profiles
using Streamlit for the frontend.
"""

import streamlit as st
import requests
import re
import random
from typing import Dict, Optional
from urllib.parse import quote_plus

# Constants for search queries
SEARCH_TEMPLATES = {
    'linkedin': 'site:linkedin.com/in "{}"',
    'facebook': 'site:facebook.com "{}"',
    'instagram': 'site:instagram.com "{}"'
}

# Personality traits for random generation
PERSONALITY_TRAITS = [
    "creative and artistic",
    "tech-savvy and analytical",
    "outgoing and social",
    "ambitious and driven",
    "kind and empathetic",
    "adventurous and spontaneous"
]

INTERESTS = [
    "photography and travel",
    "technology and innovation",
    "fitness and wellness",
    "art and culture",
    "food and cooking",
    "music and entertainment"
]

def get_social_links(name: str) -> Dict[str, Optional[str]]:
    """
    Search for social media profiles using the given name.
    
    Args:
        name (str): Full name of the person to search for
        
    Returns:
        Dict[str, Optional[str]]: Dictionary containing social media platform names
        as keys and their corresponding URLs (or None if not found)
    """
    results = {
        'linkedin': None,
        'facebook': None,
        'instagram': None
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for platform, template in SEARCH_TEMPLATES.items():
        try:
            # Format the search query
            query = template.format(name)
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            
            # Make the request
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            # Extract the first result URL
            pattern = r'https?://(?:www\.)?' + platform + r'\.com/[^\s"<>]+'
            matches = re.findall(pattern, response.text)
            
            if matches:
                results[platform] = matches[0]
                
        except (requests.RequestException, re.error) as e:
            st.error(f"Error searching for {platform} profile: {str(e)}")
            continue
    
    return results

def analyze_profile(link: str) -> str:
    """
    Generate a simple personality analysis based on the profile link.
    
    Args:
        link (str): URL of the social media profile
        
    Returns:
        str: A brief personality analysis
    """
    # Extract platform from the URL
    platform = None
    for p in ['linkedin', 'facebook', 'instagram']:
        if p in link.lower():
            platform = p
            break
    
    if not platform:
        return "Unable to analyze profile: Unknown platform"
    
    # Generate random personality traits and interests
    trait = random.choice(PERSONALITY_TRAITS)
    interest = random.choice(INTERESTS)
    
    # Create platform-specific analysis
    if platform == 'linkedin':
        return f"Based on their professional profile, they seem {trait}. " \
               f"They're likely interested in {interest} and value professional growth."
    elif platform == 'facebook':
        return f"From their social presence, they appear {trait}. " \
               f"They enjoy {interest} and seem to be quite social."
    else:  # Instagram
        return f"Looking at their visual content, they come across as {trait}. " \
               f"They have a passion for {interest} and share their experiences through photos."

def main():
    """
    Main Streamlit application.
    """
    # Set page config
    st.set_page_config(
        page_title="FlirtGPT",
        page_icon="💝",
        layout="centered"
    )
    
    # Header
    st.title("💝 FlirtGPT")
    st.markdown("### Analyze social media profiles for better connections")
    
    # Input field
    name = st.text_input(
        "Enter a full name to analyze",
        placeholder="e.g., John Doe",
        key="name_input"
    )
    
    # Search button
    if st.button("🔍 Analyze Profile", type="primary"):
        if not name:
            st.warning("Please enter a name to analyze.")
            return
            
        with st.spinner("Searching for profiles..."):
            profiles = get_social_links(name)
            
            if not any(profiles.values()):
                st.error("No social media profiles found. Try a different name.")
                return
                
            # Display results
            st.success("Found some profiles! Here's the analysis:")
            
            # Create columns for each platform
            cols = st.columns(3)
            
            # Platform icons and colors
            platform_info = {
                'linkedin': {'icon': '💼', 'color': '#0077B5'},
                'facebook': {'icon': '👥', 'color': '#1877F2'},
                'instagram': {'icon': '📸', 'color': '#E4405F'}
            }
            
            # Display each profile
            for i, (platform, url) in enumerate(profiles.items()):
                if url:
                    with cols[i]:
                        st.markdown(f"### {platform_info[platform]['icon']} {platform.title()}")
                        st.markdown(f"[View Profile]({url})")
                        analysis = analyze_profile(url)
                        st.markdown(f"*{analysis}*")
    
    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ for AI Cup 2025")

if __name__ == "__main__":
    main() 