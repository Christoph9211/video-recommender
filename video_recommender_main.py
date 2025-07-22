import re
import pandas as pd
from bs4 import BeautifulSoup
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
from lxml import html
from typing import Dict, Optional, Tuple
import asyncio
from video_recommender.scrapers import Crawl4aiVideoScraper

# Initialize the global scraper instance
scraper = Crawl4aiVideoScraper()

# Synchronous wrapper functions for the async scraper
def scrape_eporner_videos(query: str, max_results: int = 30) -> pd.DataFrame:
    """Synchronous wrapper for Eporner video scraping using Crawl4AI."""
    return asyncio.run(scraper.fetch("eporner", query, max_results))

def scrape_hqporner_videos(query: str, max_results: int = 20) -> pd.DataFrame:
    """Synchronous wrapper for HQPorner video scraping using Crawl4AI."""
    return asyncio.run(scraper.fetch("hqporner", query, max_results))

def scrape_porntrex_videos(query: str, max_results: int = 10) -> pd.DataFrame:
    """Synchronous wrapper for Porntrex video scraping using Crawl4AI."""
    return asyncio.run(scraper.fetch("porntrex", query, max_results))

def scrape_xnxx_videos(query: str, max_results: int = 20) -> pd.DataFrame:
    """Synchronous wrapper for XNXX video scraping using Crawl4AI."""
    return asyncio.run(scraper.fetch("xnxx", query, max_results))

def scrape_motherless_videos(query: str, max_results: int = 10) -> pd.DataFrame:
    """Synchronous wrapper for Motherless video scraping using Crawl4AI."""
    return asyncio.run(scraper.fetch("motherless", query, max_results))

def scrape_hq_porner(query: str, max_results: int = 20) -> pd.DataFrame:
    """Alias for scrape_hqporner_videos for backward compatibility."""
    return scrape_hqporner_videos(query, max_results)


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
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(combined_text)
    user_profile = np.asarray(tfidf_matrix.mean(axis=0)).reshape(1, -1)
    return vectorizer, user_profile


def _encode_domains(domains: pd.Series, mapping: Optional[Dict[str, int]] = None) -> Tuple[np.ndarray, Dict[str, int]]:
    """One-hot encode domain strings."""
    if mapping is None:
        unique = sorted(domains.unique())
        mapping = {d: i for i, d in enumerate(unique)}

    vectors = np.zeros((len(domains), len(mapping)))
    for i, d in enumerate(domains):
        idx = mapping.get(d)
        if idx is not None:
            vectors[i, idx] = 1.0
    return vectors, mapping


def build_user_embedding_profile(
    bookmarks: pd.DataFrame,
    model_name: str = "all-MiniLM-L6-v2",
) -> tuple[Optional[SentenceTransformer], Optional[Dict[str, int]], Optional[np.ndarray]]:
    """Create a user profile using sentence embeddings and domain features."""
    if bookmarks.empty:
        return None, None, None

    model = SentenceTransformer(model_name)
    texts = (bookmarks["title"].fillna("") + " " + bookmarks["description"].fillna(""))
    embeddings = model.encode(list(texts), convert_to_numpy=True)

    domain_vecs, mapping = _encode_domains(bookmarks["source"].fillna("unknown"))
    combined = np.hstack([embeddings, domain_vecs])
    profile = combined.mean(axis=0, keepdims=True)
    return model, mapping, profile


def recommend_videos_with_embeddings(
    candidates: pd.DataFrame,
    model: SentenceTransformer,
    domain_mapping: Dict[str, int],
    user_profile: np.ndarray,
    top_n: int = 30,
) -> pd.DataFrame:
    """Recommend videos using sentence embeddings and domain features."""
    if candidates.empty or model is None or user_profile is None:
        return pd.DataFrame()

    texts = (candidates["title"].fillna("") + " " + candidates["description"].fillna(""))
    embeddings = model.encode(list(texts), convert_to_numpy=True)
    domain_vecs, _ = _encode_domains(candidates["source"].fillna("unknown"), mapping=domain_mapping)
    combined = np.hstack([embeddings, domain_vecs])
    scores = cosine_similarity(combined, user_profile).flatten()
    candidates["relevance_score"] = scores
    return candidates.nlargest(top_n, "relevance_score")


def recommend_videos(
    candidates: pd.DataFrame, vectorizer: TfidfVectorizer, user_profile: np.ndarray, top_n: int = 30
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
    
    bookmark_file_path = "favorites_6_10_25.txt"
    print(f"Using bookmark file: {bookmark_file_path}")

    bookmarks = parse_bookmarks_from_file(bookmark_file_path)
    if bookmarks.empty:
        print("No valid bookmarks found. Exiting.")
        exit()

    vectorizer, user_profile = build_user_profile(bookmarks)
    model, domain_map, emb_profile = build_user_embedding_profile(bookmarks)

    if vectorizer is None or user_profile is None:
        print("Could not create a user profile. Exiting.")
        exit()

    query = input("Enter a search query for new videos: ").strip()
    scraped_candidates = []
    try:
        scraped_candidates = [
            scrape_motherless_videos(query, max_results=10),
            scrape_xnxx_videos(query, max_results=20),
            scrape_hq_porner(query, max_results=20),
            scrape_eporner_videos(query, max_results=30),
            scrape_porntrex_videos(query, max_results=20)
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
    emb_recs = recommend_videos_with_embeddings(
        combined_scraped_candidates, model, domain_map, emb_profile, top_n=30
    )

    if top_recommendations.empty and emb_recs.empty:
        print("No recommendations could be made.")
    else:
        print("\nTop Recommendations (TF-IDF):\n")
        for _, row in top_recommendations.iterrows():
            print(f"{row['title']} ({row['url']}) — Score: {row['relevance_score']:.3f}")

        print("\nTop Recommendations (Embeddings):\n")
        for _, row in emb_recs.iterrows():
            print(f"{row['title']} ({row['url']}) — Score: {row['relevance_score']:.3f}")
