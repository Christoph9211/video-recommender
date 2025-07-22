#!/usr/bin/env python3
"""
Video Recommender CLI

Command-line interface for the video recommendation system with robust error handling and logging.
"""

import argparse
import logging
import sys
import pandas as pd
from pathlib import Path
# Import functions from the main video_recommender module
from video_recommender_main import (
    parse_bookmarks_from_file, 
    build_user_profile, 
    recommend_videos,
    # scrape_motherless_videos,
    # scrape_xnxx_videos,
    # scrape_hq_porner,
    scrape_eporner_videos,
    # scrape_porntrex_videos
)


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging based on verbosity level.
    
    Args:
        verbose: If True, enable debug-level logging; otherwise INFO level
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    if verbose:
        logging.getLogger('video_recommender.scrapers').setLevel(logging.DEBUG)
        logging.getLogger('crawl4ai_settings').setLevel(logging.DEBUG)
    else:
        logging.getLogger('video_recommender.scrapers').setLevel(logging.INFO)
        logging.getLogger('crawl4ai_settings').setLevel(logging.WARNING)


def scrape_all_sites(query: str, verbose: bool = False) -> pd.DataFrame:
    """
    Scrape videos from all supported sites with robust error handling.
    
    Args:
        query: Search query
        verbose: Enable verbose logging
        
    Returns:
        Combined DataFrame of scraped results
    """
    logger = logging.getLogger(__name__)
    
    # Define scraping functions with their limits
    scrapers = [
        # ("Motherless", scrape_motherless_videos, 10),
        # ("XNXX", scrape_xnxx_videos, 20),
        # ("HQPorner", scrape_hq_porner, 20),
        ("Eporner", scrape_eporner_videos, 50),
        # ("Porntrex", scrape_porntrex_videos, 20)
    ]
    
    scraped_results = []
    
    for site_name, scraper_func, max_results in scrapers:
        try:
            logger.info(f"Scraping {site_name}...")
            df = scraper_func(query, max_results=max_results)
            
            if not df.empty:
                logger.info(f"Successfully scraped {len(df)} videos from {site_name}")
                scraped_results.append(df)
            else:
                logger.warning(f"No videos found from {site_name}")
                
        except Exception as e:
            logger.error(f"Failed to scrape {site_name}: {str(e)[:100]}...")
            if verbose:
                logger.debug(f"Full error for {site_name}: {e}", exc_info=True)
            # Continue with other sites instead of failing completely
    
    # Combine all successful results
    if scraped_results:
        combined_df = pd.concat(scraped_results, ignore_index=True)
        logger.info(f"Combined {len(combined_df)} videos from {len(scraped_results)} sites")
        return combined_df
    else:
        logger.warning("No videos scraped from any site")
        return pd.DataFrame(columns=['title', 'url', 'source', 'description'])


def get_fallback_data() -> pd.DataFrame:
    """
    Return fallback example data when scraping fails completely.
    
    Returns:
        DataFrame with example data
    """
    return pd.DataFrame([
        {
            "title": "Pico C++ Projects", 
            "url": "https://www.raspberrypi.com/documentation/microcontrollers/cpp.html", 
            "description": "", 
            "source": "example"
        },
        {
            "title": "The Pico C++ Projects", 
            "url": "https://projects.raspberrypi.org/en/projects/getting-started-with-pico", 
            "description": "", 
            "source": "example"
        },
        {
            "title": "Advanced Pico C++ Projects", 
            "url": "https://www.tomshardware.com/how-to/raspberry-pi-pico-projects", 
            "description": "", 
            "source": "example"
        },
    ])


def main():
    """Main CLI entry point with comprehensive error handling."""
    parser = argparse.ArgumentParser(
        description="Video Recommender - Find personalized video recommendations",
        epilog="Example: python cli.py --bookmarks favorites.txt --query 'python programming' --verbose"
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose debug output and detailed logging'
    )
    
    parser.add_argument(
        '--bookmarks', '-b',
        type=str,
        default='favorites_6_10_25.txt',
        help='Path to bookmarks file (default: favorites_6_10_25.txt)'
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Search query for videos. If not provided, will prompt interactively'
    )
    
    parser.add_argument(
        '--max-recommendations', '-n',
        type=int,
        default=30,
        help='Maximum number of recommendations to return (default: 30)'
    )
    
    parser.add_argument(
        '--no-fallback',
        action='store_true',
        help='Disable fallback to example data when scraping fails'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Load and validate bookmarks
        logger.info(f"Loading bookmarks from: {args.bookmarks}")
        bookmarks_path = Path(args.bookmarks)
        
        if not bookmarks_path.exists():
            logger.error(f"Bookmarks file not found: {args.bookmarks}")
            sys.exit(1)
            
        bookmarks = parse_bookmarks_from_file(str(bookmarks_path))
        if bookmarks.empty:
            logger.error("No valid bookmarks found in the file")
            sys.exit(1)
            
        logger.info(f"Loaded {len(bookmarks)} bookmarks")
        
        # Build user profile
        logger.info("Building user profile from bookmarks...")
        vectorizer, user_profile = build_user_profile(bookmarks)
        
        if vectorizer is None or user_profile is None:
            logger.error("Could not create a user profile from bookmarks")
            sys.exit(1)
            
        logger.info("User profile created successfully")
        
        # Get search query
        query = args.query
        if not query:
            try:
                query = input("Enter a search query for new videos: ").strip()
                if not query:
                    logger.error("No search query provided")
                    sys.exit(1)
            except (KeyboardInterrupt, EOFError):
                logger.info("Interrupted by user")
                sys.exit(0)
        
        logger.info(f"Searching for: '{query}'")
        
        # Scrape videos with robust error handling
        scraped_candidates = scrape_all_sites(query, args.verbose)
        
        # Fallback to example data if scraping failed completely
        if scraped_candidates.empty and not args.no_fallback:
            logger.warning("No videos found from web scraping, using fallback example data")
            scraped_candidates = get_fallback_data()
        elif scraped_candidates.empty:
            logger.error("No videos found and fallback disabled")
            sys.exit(1)
        
        # Generate recommendations
        logger.info("Generating recommendations...")
        recommendations = recommend_videos(
            scraped_candidates, 
            vectorizer, 
            user_profile, 
            top_n=args.max_recommendations
        )
        
        if recommendations.empty:
            logger.warning("No recommendations could be generated")
            print("No recommendations found based on your profile.")
        else:
            print(f"\nTop {len(recommendations)} Recommendations:\n")
            print("=" * 80)
            
            for i, (_, row) in enumerate(recommendations.iterrows(), 1):
                score = row.get('relevance_score', 0.0)
                print(f"{i:2d}. {row['title']}")
                print(f"    URL: {row['url']}")
                print(f"    Source: {row['source']} | Relevance: {score:.3f}")
                print()
        
        logger.info("Process completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            logger.debug("Full error details:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
