import re
import pandas as pd
from bs4 import BeautifulSoup
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
from urllib.parse import urlparse
import asyncio
from typing import Dict, Optional, Tuple
from video_recommender.scrapers import Crawl4aiVideoScraper

# Initialize the global scraper instance
scraper = Crawl4aiVideoScraper()

# Synchronous wrapper functions for the async scraper
def scrape_eporner_videos(query: str, max_results: int = 10) -> pd.DataFrame:
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

def scrape_hq_porner(query: str = None, max_results: int = 20) -> pd.DataFrame:
    """Synchronous wrapper for HQPorner video scraping using Crawl4AI."""
    return asyncio.run(scraper.fetch("hqporner", query, max_results))


def parse_bookmarks_from_file(bookmark_file_path: str) -> pd.DataFrame:
    """Parse bookmarks from a text file."""
    try:
        with open(bookmark_file_path, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        return pd.DataFrame()

    soup = BeautifulSoup(content, "html.parser")
    bookmarks = []
    for a_tag in soup.find_all("a"):
        title = a_tag.text.strip() if a_tag.text else "No Title"
        url = a_tag.get("href", "").strip()
        domain = urlparse(url).netloc if url else "Unknown Source"

        bookmarks.append(
            {
                "title": title,
                "url": url,
                "source": domain,
                "description": "",
            }
        )

    return pd.DataFrame(bookmarks)


def build_user_profile(bookmarks: pd.DataFrame) -> tuple[TfidfVectorizer, np.ndarray]:
    """Build a user profile based on their bookmarks."""
    if bookmarks.empty:
        return None, None

    # Combine title and url into a single string
    combined_text = bookmarks["title"].astype(str) + " " + bookmarks["url"].astype(str)

    # Create a TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words="english")

    # Fit the vectorizer to the data and transform it
    tfidf_matrix = vectorizer.fit_transform(combined_text)

    # Calculate the mean TF-IDF vector as the user profile
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
    """Create a user profile using pre-trained sentence embeddings and domain features."""
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
    top_n: int = 20,
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


def recommend_videos(candidates: pd.DataFrame, tfidf_vectorizer: TfidfVectorizer, user_vector: np.ndarray, top_n: int = 20) -> pd.DataFrame:
    if candidates.empty or tfidf_vectorizer is None or user_vector is None:
        return pd.DataFrame()

    try:
        candidate_texts = candidates["title"] + " " + candidates["url"]
        candidate_vectors = tfidf_vectorizer.transform(candidate_texts)
        similarity_scores = cosine_similarity(candidate_vectors, user_vector).flatten()
        candidates["relevance_score"] = similarity_scores
        return candidates.nlargest(top_n, "relevance_score")
    except Exception as error:
        print(f"Error in recommending videos: {error}")
        return pd.DataFrame()



if __name__ == "__main__":
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
            scrape_eporner_videos(query, max_results=20),
            scrape_porntrex_videos(query, max_results=20),
        ]
    except Exception as e:
        print(f"Error during scraping: {e}")

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
