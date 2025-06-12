import os
import re
import pandas as pd
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def parse_bookmarks_from_html(file_path):
    """Parse bookmarks from an HTML file."""

    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')

    bookmarks = []
    for link in soup.find_all('a'):
        title = link.text.strip()
        url = link.get('href', '').strip()
        
        # More robust domain extraction
        try:
            if url:
                # Try to find domain using regex
                domain_match = re.findall(r'https?://(?:www\.)?([^/]+)', url)
                if domain_match:
                    domain = domain_match[0]
                else:
                    # Fallback: try to get domain from URL directly
                    domain = url.split('/')[0]
            else:
                domain = 'Unknown Source'
        except Exception:
            domain = 'Unknown Source'

        bookmarks.append({
            'title': title,
            'url': url,
            'source': domain,
            'description': ''  # Placeholder, can be filled with metadata/scraping
        })

    return pd.DataFrame(bookmarks)

def build_user_profile(bookmarks_df):
    bookmarks_df["combined_text"] = bookmarks_df["title"] + " " + bookmarks_df["url"]
    tfidf_vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = tfidf_vectorizer.fit_transform(bookmarks_df["combined_text"])
    user_profile_vector = np.asarray(tfidf_matrix.mean(axis=0)).reshape(1, -1)
    return tfidf_vectorizer, user_profile_vector


def recommend_videos(candidates, vectorizer, user_profile_vector, top_n=5):
    candidates["text"] = candidates["title"] + " " + candidates["url"]
    tfidf_candidates = vectorizer.transform(candidates["text"])
    scores = cosine_similarity(tfidf_candidates, user_profile_vector)
    candidates["score"] = scores.flatten()
    return candidates.sort_values("score", ascending=False).head(top_n)

if __name__ == "__main__":
    bookmark_file_path = input("Enter path to your bookmark .txt file: ").strip()

    bookmarks = parse_bookmarks_from_html(bookmark_file_path)
    vectorizer, user_profile = build_user_profile(bookmarks)

    example_candidates = pd.DataFrame([
        {"title": "Amirah Adara & Rebecca Volpetti", "url": "www.eporner.com/video-xmefJNVPrrF/amirah-adara-rebecca-volpetti/"},
        {"title": "Amazing Young Lesbians", "url": "www.eporner.com/hd-porn/gbT1bBqMMIk/Amazing-Young-Lesbians/"},
        {"title": "Advanced Pico C++ Projects", "url": "www.raspberrypi.com"},
        {"title": "Full Video - Dyked - Nympho Tries To Study | Pornhub", "url": "www.pornhub.com/view_video.php?viewkey=ph5e6a8b5c23b0c"}
    ])
    example_candidates["description"] = ""
    example_candidates["url"] = ["", "", "", ""]

    top_recommendations = recommend_videos(example_candidates, vectorizer, user_profile, top_n=3)
    print("\nTop Recommendations:\n")
    for _, row in top_recommendations.iterrows():
        print(f"{row['title']} ({row['url']}) — Score: {row['score']:.3f}")
