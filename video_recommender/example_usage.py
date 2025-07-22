"""
Example usage of the Crawl4aiVideoScraper façade

This demonstrates how to use the unified video scraper interface with robust error handling and logging.
"""

import asyncio
import logging
import pandas as pd
from scrapers import Crawl4aiVideoScraper


async def main():
    """Example usage of the video scraper with enhanced error handling."""
    
    # Configure logging for demonstration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Initialize the scraper with default settings
    scraper = Crawl4aiVideoScraper()
    
    logger.info("Starting enhanced video scraper examples...")
    
    # Example 1: Search for videos on a specific site
    print("Example 1: Searching for 'tech' videos on eporner...")
    try:
        df_search = await scraper.fetch(site='eporner', query='tech', max_results=10)
        print(f"Found {len(df_search)} videos")
        if not df_search.empty:
            print(df_search[['title', 'source']].head())
        else:
            print("No videos found (placeholder implementation)")
    except Exception as e:
        print(f"Error during search: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Get trending content without query
    print("Example 2: Getting trending content from hqporner...")
    try:
        df_trending = await scraper.fetch(site='hqporner', max_results=15)
        print(f"Found {len(df_trending)} trending videos")
        if not df_trending.empty:
            print(df_trending[['title', 'source']].head())
        else:
            print("No videos found (placeholder implementation)")
    except Exception as e:
        print(f"Error fetching trending: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Using custom settings with enhanced retry and fallback
    print("Example 3: Using custom scraper settings with enhanced retry logic...")
    custom_settings = {
        'retry_times': 2,
        'timeout': 15,
        'download_delay': 0.5,
        'fallback_enabled': True,
        'backoff_strategy': 'linear',
        'retry_delay_multiplier': 1.5,
        'max_retry_delay': 5.0
    }
    custom_scraper = Crawl4aiVideoScraper(settings=custom_settings)
    logger.info(f"Custom settings: {custom_settings}")
    
    try:
        df_custom = await custom_scraper.fetch(site='eporner', query='lesbian', max_results=5)
        print(f"Found {len(df_custom)} videos with custom settings")
        if not df_custom.empty:
            print(df_custom[['title', 'source']].head())
        else:
            print("No videos found (placeholder implementation)")
    except Exception as e:
        print(f"Error with custom settings: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 4: Error handling for unsupported site
    print("Example 4: Testing error handling for unsupported site...")
    try:
        df_error = await scraper.fetch(site='unsupported_site', query='test')
        print("This shouldn't be reached")
    except ValueError as e:
        print(f"Expected error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 5: Combining results from multiple sites with enhanced error handling
    print("Example 5: Fetching from multiple sites with robust error handling...")
    sites = ['eporner', 'hqporner', 'porntrex']
    all_results = []
    failed_sites = []
    
    for site in sites:
        try:
            logger.info(f"Attempting to fetch from {site}...")
            df = await scraper.fetch(site=site, query='programming', max_results=5)
            if not df.empty:
                all_results.append(df)
                logger.info(f"Successfully fetched {len(df)} videos from {site}")
            else:
                logger.warning(f"No videos returned from {site}")
        except Exception as e:
            failed_sites.append(site)
            logger.error(f"Failed to fetch from {site}: {str(e)[:100]}...")
            # Continue with other sites instead of failing completely
    
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        print(f"Combined {len(combined_df)} videos from {len(all_results)} sites")
        print(f"Sources: {combined_df['source'].value_counts().to_dict()}")
        if failed_sites:
            print(f"Failed sites: {', '.join(failed_sites)}")
    else:
        print("No results from any site (placeholder implementation)")
        
    print("\n" + "="*50 + "\n")
    
    # Example 6: Demonstration of fallback mechanisms
    print("Example 6: Testing fallback user agent rotation...")
    fallback_settings = {
        'retry_times': 4,
        'fallback_enabled': True,
        'enable_fallback_user_agents': True,
        'fallback_user_agents': [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
    }
    
    fallback_scraper = Crawl4aiVideoScraper(settings=fallback_settings)
    
    try:
        df_fallback = await fallback_scraper.fetch(site='xnxx', query='test', max_results=3)
        print(f"Fallback test completed: {len(df_fallback)} videos")
    except Exception as e:
        print(f"Fallback test failed (expected in placeholder): {e}")


if __name__ == "__main__":
    asyncio.run(main())
