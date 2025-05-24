import os
from typing import Dict, List, Optional
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()

class SearchModule:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY not found in environment variables")

    async def search_person(self, full_name: str) -> Dict:
        """
        Search for information about a person using SerpAPI.
        
        Args:
            full_name (str): Full name of the person to search for
            
        Returns:
            Dict: Dictionary containing search results including:
                - social_profiles: List of social media profiles
                - news_articles: List of news articles
                - professional_info: Professional information
                - other_references: Other relevant information
        """
        try:
            # Search for social profiles
            social_search = GoogleSearch({
                "q": f"{full_name} site:linkedin.com OR site:twitter.com OR site:facebook.com",
                "api_key": self.api_key,
                "num": 10
            })
            social_results = social_search.get_dict()

            # Search for news articles
            news_search = GoogleSearch({
                "q": f"{full_name} news",
                "api_key": self.api_key,
                "num": 10
            })
            news_results = news_search.get_dict()

            # Process and structure the results
            results = {
                "social_profiles": self._extract_social_profiles(social_results),
                "news_articles": self._extract_news_articles(news_results),
                "professional_info": self._extract_professional_info(social_results),
                "other_references": self._extract_other_references(social_results, news_results)
            }

            return results

        except Exception as e:
            raise Exception(f"Error in search_person: {str(e)}")

    def _extract_social_profiles(self, results: Dict) -> List[Dict]:
        """Extract social media profiles from search results."""
        profiles = []
        if "organic_results" in results:
            for result in results["organic_results"]:
                if any(site in result.get("link", "").lower() 
                      for site in ["linkedin.com", "twitter.com", "facebook.com"]):
                    profiles.append({
                        "platform": self._get_platform(result.get("link", "")),
                        "url": result.get("link"),
                        "title": result.get("title"),
                        "snippet": result.get("snippet")
                    })
        return profiles

    def _extract_news_articles(self, results: Dict) -> List[Dict]:
        """Extract news articles from search results."""
        articles = []
        if "organic_results" in results:
            for result in results["organic_results"]:
                articles.append({
                    "title": result.get("title"),
                    "url": result.get("link"),
                    "snippet": result.get("snippet"),
                    "date": result.get("date")
                })
        return articles

    def _extract_professional_info(self, results: Dict) -> Dict:
        """Extract professional information from search results."""
        professional_info = {
            "current_position": None,
            "company": None,
            "education": None,
            "skills": []
        }
        
        # Extract from LinkedIn profile if available
        if "organic_results" in results:
            for result in results["organic_results"]:
                if "linkedin.com" in result.get("link", "").lower():
                    snippet = result.get("snippet", "")
                    # Basic extraction logic - can be enhanced with more sophisticated parsing
                    if "at" in snippet:
                        parts = snippet.split("at")
                        professional_info["current_position"] = parts[0].strip()
                        professional_info["company"] = parts[1].strip()

        return professional_info

    def _extract_other_references(self, social_results: Dict, news_results: Dict) -> List[Dict]:
        """Extract other relevant references from search results."""
        references = []
        
        # Combine and process results from both searches
        all_results = []
        if "organic_results" in social_results:
            all_results.extend(social_results["organic_results"])
        if "organic_results" in news_results:
            all_results.extend(news_results["organic_results"])

        for result in all_results:
            if not any(site in result.get("link", "").lower() 
                      for site in ["linkedin.com", "twitter.com", "facebook.com"]):
                references.append({
                    "title": result.get("title"),
                    "url": result.get("link"),
                    "snippet": result.get("snippet")
                })

        return references

    def _get_platform(self, url: str) -> str:
        """Determine the social media platform from a URL."""
        url = url.lower()
        if "linkedin.com" in url:
            return "LinkedIn"
        elif "twitter.com" in url:
            return "Twitter"
        elif "facebook.com" in url:
            return "Facebook"
        return "Other" 