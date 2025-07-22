# import re
import pandas as pd
from bs4 import BeautifulSoup
# import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from lxml import html
import asyncio
from video_recommender.scrapers import Crawl4aiVideoScraper

# Initialize the global scraper instance
scraper = Crawl4aiVideoScraper()

# Synchronous wrapper functions for the async scraper
def scrape_eporner_videos(query: str, max_results: int = 50) -> pd.DataFrame:
    """Synchronous wrapper for Eporner video scraping using Crawl4AI."""
    return asyncio.run(scraper.fetch("eporner", query, max_results))

def scrape_porntrex_videos(query: str, max_results: int = 10) -> pd.DataFrame:
    """Synchronous wrapper for Porntrex video scraping using Crawl4AI."""
    return asyncio.run(scraper.fetch("porntrex", query, max_results))

def scrape_xnxx_videos(query: str, max_results: int = 20) -> pd.DataFrame:
    """Synchronous wrapper for XNXX video scraping using Crawl4AI."""
    return asyncio.run(scraper.fetch("xnxx", query, max_results))

def scrape_motherless_videos(query: str, max_results: int = 10) -> pd.DataFrame:
    """Synchronous wrapper for Motherless video scraping using Crawl4AI."""
    return asyncio.run(scraper.fetch("motherless", query, max_results))


def parse_bookmarks_from_file(bookmark_file_path: str) -> pd.DataFrame:
    """Parse bookmarks from a text file."""
    try:
        with open(bookmark_file_path, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

    soup = BeautifulSoup(content, "html.parser")
    bookmarks = []
    for link in soup.find_all("a"):
        title = link.text.strip() if link.text else "No Title"
        url = link.get("href", "").strip()

        # Robust domain extraction
        domain = url.split("/")[0] if url else "Unknown Source"

        bookmarks.append(
            {
                "title": title,
                "url": url,
                "source": domain,
                "description": "",  # Placeholder, can be filled with metadata/scraping
            }
        )

    return pd.DataFrame(bookmarks)


def build_user_profile(bookmarks: pd.DataFrame) -> tuple[TfidfVectorizer, np.ndarray]:
    """
    Build a user profile based on their bookmarks.

    Parameters:
    bookmarks (pd.DataFrame): DataFrame of bookmarks with "title" and "url" columns.

    Returns:
    vectorizer (TfidfVectorizer): Vectorizer used to create the user profile.
    user_profile (np.ndarray): User profile vector.
    """
    if bookmarks.empty:
        return None, None

    combined_text = bookmarks["title"] + " " + bookmarks["url"]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(combined_text)
    user_profile = np.asarray(tfidf_matrix.mean(axis=0)).reshape(1, -1)
    return vectorizer, user_profile


def recommend_videos(
    candidates: pd.DataFrame, vectorizer: TfidfVectorizer, user_profile: np.ndarray, top_n: int = 20
) -> pd.DataFrame:
    """
    Recommend videos based on their similarity to a user's profile.

    Parameters:
    candidates (pd.DataFrame): DataFrame of candidate videos with "title" and "url" columns.
    vectorizer (TfidfVectorizer): Vectorizer fitted on user's bookmarks.
    user_profile (np.ndarray): Vector representation of the user's interests.
    top_n (int, optional): Number of top recommendations to return. Defaults to 10.

    Returns:
    pd.DataFrame: DataFrame of top recommended videos sorted by relevance score.
    """
    if not candidates.empty and vectorizer is not None and user_profile is not None:
        text = candidates["title"] + " " + candidates["url"]
        try:
            tfidf_candidates = vectorizer.transform(text)
            scores = cosine_similarity(tfidf_candidates, user_profile).flatten()
            candidates["relevance_score"] = scores
            return candidates.nlargest(top_n, "relevance_score")
        except Exception as e:
            print(e)
    return pd.DataFrame()


import logging
import argparse

# Configure logger for this module  
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Recommender")
    parser.add_argument('--verbose', action='store_true', help='Enable verbose debug output')
    args = parser.parse_args()

    # Configure logging level based on verbosity flag
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, 
                          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    bookmark_file_path = "Reading_List.html"
    print(f"Using bookmark file: {bookmark_file_path}")

    bookmarks = parse_bookmarks_from_file(bookmark_file_path)
    if bookmarks.empty:
        print("No valid bookmarks found. Exiting.")
        exit()

    vectorizer, user_profile = build_user_profile(bookmarks)
    if vectorizer is None or user_profile is None:
        print("Could not create a user profile. Exiting.")
        exit()

    query = input("Enter a search query for new videos: ").strip()
    scraped_candidates = []
    try:
        scraped_candidates = [
            # scrape_motherless_videos(query, max_results=10),
            # scrape_xnxx_videos(query, max_results=20),
            scrape_eporner_videos(query, max_results=100),
            # scrape_porntrex_videos(query, max_results=20)
        ]
    except Exception as e:
        logger.error(f"Error during scraping: {e}")

    scraped_candidates = [df for df in scraped_candidates if not df.empty]
    if scraped_candidates:
        combined_scraped_candidates = pd.concat(scraped_candidates, ignore_index=True)
    else:
        combined_scraped_candidates = pd.DataFrame()

    if combined_scraped_candidates.empty:
        print("No videos found from the web, falling back to example data.")
        combined_scraped_candidates = pd.DataFrame([
            {"title": "Pico C++ Projects", "url": "https://www.raspberrypi.com/documentation/microcontrollers/cpp.html", "description": "", "source": "example"},
            {"title": "The Pico C++ Projects", "url": "https://projects.raspberrypi.org/en/projects/getting-started-with-pico", "description": "", "source": "example"},
            {"title": "Advanced Pico C++ Projects", "url": "https://www.tomshardware.com/how-to/raspberry-pi-pico-projects", "description": "", "source": "example"},
        ])

    top_recommendations = recommend_videos(combined_scraped_candidates, vectorizer, user_profile, top_n=30)
    if top_recommendations.empty:
        print("No recommendations could be made.")
    else:
        print("\nTop Recommendations:\n")
        for _, row in top_recommendations.iterrows():
            print(f"{row['title']} ({row['url']}) — Score: {row['relevance_score']:.3f}")
