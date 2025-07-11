import re
import pandas as pd
from bs4 import BeautifulSoup
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


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
            candidates["score"] = scores
            return candidates.nlargest(top_n, "score")
        except Exception as e:
            print(e)
    return pd.DataFrame()


def scrape_eporner_videos(query: str, max_results: int = 10) -> pd.DataFrame:
    """Scrape Eporner search results for video titles and URLs."""
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

        video_data.append(
            {
                "title": title,
                "url": full_url,
                "source": "eporner",
                "description": "",
            }
        )

    return pd.DataFrame(video_data)

def scrape_hq_porner(query: str, max_results: int = 10) -> pd.DataFrame:
    """Scrape HQ PornHub search results for video titles and URLs."""
    search_url = f"https://www.hqporner.com/?q={query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
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

        full_url = f"https://www.hqporner.com{href}"
        if any(video["url"] == full_url for video in video_data):
            continue

        video_data.append(
            {
                "title": title,
                "url": full_url,
                "source": "hqporner",
                "description": "",
            }
        )

    return pd.DataFrame(video_data)

def scrape_porntrex_videos(query: str, max_results: int = 10) -> pd.DataFrame:
    """Scrape Porntrex search results for video titles and URLs."""
    search_url = f"https://www.porntrex.com/search/{query}/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
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

        full_url = f"https://www.porntrex.com{href}"
        if any(video["url"] == full_url for video in video_data):
            continue

        video_data.append(
            {
                "title": title,
                "url": full_url,
                "source": "porntrex",
                "description": "",
            }
        )

    if video_data:
        return pd.DataFrame(video_data)
    

if __name__ == "__main__":
    bookmark_file_path = "favorites_6_10_25.txt"
    if bookmark_file_path is not None:
        print(f"Using default bookmark file: {bookmark_file_path}")
    else:
        print("No default bookmark file found. Please provide a path to your bookmark .txt file.")
        bookmark_file_path = input("Enter path to your bookmark .txt file: ").strip()

    bookmarks = parse_bookmarks_from_file(bookmark_file_path)
    if bookmarks.empty:
        print("No valid bookmarks found. Exiting.")
        exit()

    vectorizer, user_profile = build_user_profile(bookmarks)
    if vectorizer is None or user_profile is None:
        print("Could not create a user profile. Exiting.")
        exit()

    query = input("Enter a search query for new videos: ").strip()
    try:
        scraped_candidates = [scrape_hq_porner(query, max_results=20), scrape_eporner_videos(query, max_results=30), scrape_porntrex_videos(query, max_results=20)]
    except Exception as e:
        print(f"Error during scraping: {e}")
        
    # Combine the results from both sources
    combined_scraped_candidates = pd.concat(scraped_candidates, ignore_index=True)
    print(combined_scraped_candidates.columns)
    if combined_scraped_candidates.empty:
        print("No videos found from the web, falling back to example data.")
        default_scraped_candidates = pd.DataFrame(
            [
                {"title": "Pico C++ Projects", "url": "https://www.raspberrypi.com/documentation/microcontrollers/cpp.html"},
                {"title": "The Pico C++ Projects", "url": "https://projects.raspberrypi.org/en/projects/getting-started-with-pico"},
                {"title": "Advanced Pico C++ Projects", "url": "https://www.tomshardware.com/how-to/raspberry-pi-pico-projects"},
            ]
        )
        default_scraped_candidates["description"] = ""
        default_scraped_candidates["source"] = "example"

    top_recommendations = recommend_videos(combined_scraped_candidates, vectorizer, user_profile, top_n=30)
    if top_recommendations.empty:
        print("No recommendations could be made.")
    else:
        print("\nTop Recommendations:\n")
        for _, row in top_recommendations.iterrows():
            print(f"{row['title']} ({row['url']}) — Score: {row['score']:.3f}")

