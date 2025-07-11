import re
import pandas as pd
from bs4 import BeautifulSoup
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from urllib.parse import urlparse


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

def scrape_xnxx_videos(query: str, max_results: int = 10) -> pd.DataFrame:
    if not query:
        print("Query cannot be empty.")
        return pd.DataFrame()

    formatted_query = requests.utils.quote(query.replace(" ", "-"))
    search_url = f"https://www.xnxx.com/search/{formatted_query}/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    session = requests.Session()
    requests.packages.urllib3.disable_warnings()

    try:
        response = session.get(search_url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        print(f"Error fetching videos: {error}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    video_data = []

    for link in soup.select("div.mbunder p.mbtit a[href^='/video-']"):
        if len(video_data) >= max_results:
            break

        href = link.get("href")
        title = link.get("title") or link.text.strip()
        if not href or not title:
            continue

        full_url = f"https://www.xnxx.com{href}"
        if any(video["url"] == full_url for video in video_data):
            continue

        video_data.append({
            "title": title,
            "url": full_url,
            "source": "xnxx",
            "description": "",
        })

    return pd.DataFrame(video_data)

def scrape_motherless_videos(query: str, max_results: int = 10) -> pd.DataFrame:
    if not query:
        print("Query cannot be empty.")
        return pd.DataFrame()

    formatted_query = requests.utils.quote(query.replace(" ", "-"))
    search_url = f"https://www.motherless.com/search/{formatted_query}/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    session = requests.Session()
    requests.packages.urllib3.disable_warnings()

    try:
        response = session.get(search_url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        print(f"Error fetching videos: {error}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    video_data = []

    for link in soup.select("div.mbunder p.mbtit a[href^='/video-']"):
        if len(video_data) >= max_results:
            break

        href = link.get("href")
        title = link.get("title") or link.text.strip()
        if not href or not title:
            continue

        full_url = f"https://www.motherless.com{href}"
        if any(video["url"] == full_url for video in video_data):
            continue

        video_data.append({
            "title": title,
            "url": full_url,
            "source": "motherless",
            "description": "",
        })

    return pd.DataFrame(video_data)

def scrape_eporner_videos(query: str, max_results: int = 10) -> pd.DataFrame:
    if not query:
        print("Query cannot be empty.")
        return pd.DataFrame()

    formatted_query = requests.utils.quote(query.replace(" ", "-"))
    search_url = f"https://www.eporner.com/search/{formatted_query}/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    session = requests.Session()
    requests.packages.urllib3.disable_warnings()

    try:
        response = session.get(search_url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        print(f"Error fetching videos: {error}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    video_data = []

    for link in soup.select("div.mbunder p.mbtit a[href^='/video-']"):
        if len(video_data) >= max_results:
            break

        href = link.get("href")
        title = link.get("title") or link.text.strip()
        if not href or not title:
            continue

        full_url = f"https://www.eporner.com{href}"
        if any(video["url"] == full_url for video in video_data):
            continue

        video_data.append({
            "title": title,
            "url": full_url,
            "source": "eporner",
            "description": "",
        })

    return pd.DataFrame(video_data)


def scrape_hq_porner(max_results: int = 20) -> pd.DataFrame:
    """Scrape top videos from HQ Porner."""

    search_url = "https://hqporner.com/top"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/58.0.3029.110 Safari/537.3"
        )
    }

    session = requests.Session()
    requests.packages.urllib3.disable_warnings()

    try:
        response = session.get(search_url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        print(f"Error fetching videos: {error}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    videos = []

    for link in soup.select("div.searchResult a[href^='/video/']"):
        if len(videos) >= max_results:
            break

        href = link.get("href")
        title = link.get("title") or link.text.strip()
        if not href or not title:
            continue

        full_url = f"https://www.hqporner.com{href}"
        if any(video["url"] == full_url for video in videos):
            continue

        videos.append({
            "title": title,
            "url": full_url,
            "source": "hqporner",
            "description": "",
        })

    return pd.DataFrame(videos)


def scrape_porntrex_videos(query: str, max_results: int = 10) -> pd.DataFrame:
    print("scrape_porntrex_videos() is currently a placeholder and may need valid CSS selectors.")
    return pd.DataFrame()


if __name__ == "__main__":
    bookmark_file_path = "favorites_6_10_25.txt"
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
            scrape_motherless_videos(query, max_results=10),
            scrape_xnxx_videos(query, max_results=20),
            scrape_hq_porner(max_results=20),
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
    if top_recommendations.empty:
        print("No recommendations could be made.")
    else:
        print("\nTop Recommendations:\n")
        for _, row in top_recommendations.iterrows():
            print(f"{row['title']} ({row['url']}) — Score: {row['score']:.3f}")
