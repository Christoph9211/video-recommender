"""
Crawl4AI Video Scraper Façade

This module provides a unified interface for scraping video content from various sites
using Crawl4AI pipelines. It includes retry logic and standardized DataFrame output.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
import pandas as pd
from urllib.parse import quote
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawl4ai_settings import get_crawl4ai_config


# Configure logger for this module
logger = logging.getLogger(__name__)

# Configure logging format if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# Site-specific flow definitions
EPORNER_FLOW = {
    "start": lambda q: f"https://www.eporner.com/search/{quote(q.replace(' ', '-'))}/" if q else "https://www.eporner.com/",
    "css": "div.mbunder p.mbtit a[href^='/video-']",
    "title_attr": "title",
    "href_attr": "href",
    "base_url": "https://www.eporner.com",
    "throttle": 0.7
}

HQPORNER_FLOW = {
    "start": lambda q: f"https://www.hqporner.com/search/{quote(q)}/" if q else "https://www.hqporner.com/top/month",
    "css": "div.searchResult a[href^='/video/']",
    "title_attr": "title",
    "href_attr": "href",
    "base_url": "https://www.hqporner.com",
    "throttle": 0.7
}

PORNTREX_FLOW = {
    "start": lambda q: f"https://www.porntrex.com/search/{quote(q)}/" if q else "https://www.porntrex.com/",
    "css": "div.mbunder p.mbtit a[href^='/video-']",
    "title_attr": "title",
    "href_attr": "href",
    "base_url": "https://www.porntrex.com",
    "throttle": 0.7
}

XNXX_FLOW = {
    "start": lambda q: f"https://www.xnxx.com/search/{quote(q)}" if q else "https://www.xnxx.com/",
    "css": "div.mozaique div.thumb-block div.thumb a[href^='/video-']",
    "title_attr": "title",
    "href_attr": "href",
    "base_url": "https://www.xnxx.com",
    "throttle": 1.0
}

MOTHERLESS_FLOW = {
    "start": lambda q: f"https://motherless.com/search/videos?term={quote(q)}" if q else "https://motherless.com/videos/recent",
    "css": "div.thumb-container a.img-container",
    "title_attr": "title",
    "href_attr": "href",
    "base_url": "https://motherless.com",
    "throttle": 1.2
}

# Site registry for easy access
SITE_FLOWS = {
    'eporner': EPORNER_FLOW,
    'hqporner': HQPORNER_FLOW,
    'porntrex': PORNTREX_FLOW,
    'xnxx': XNXX_FLOW,
    'motherless': MOTHERLESS_FLOW
}


class Crawl4aiVideoScraper:
    """
    Unified façade for video scraping using Crawl4AI pipelines.
    
    This class provides a consistent interface for fetching video content from different
    sites, handling retries, and returning standardized DataFrames with video information.
    """
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """
        Initialize the Crawl4AI video scraper.
        
        Args:
            settings: Optional dictionary of crawler settings. If None, uses defaults from crawl4ai_settings.
        """
        self.settings = settings or get_crawl4ai_config()
        self._site_pipelines = {
            'eporner': self._get_eporner_pipeline,
            'hqporner': self._get_hqporner_pipeline,
            'porntrex': self._get_porntrex_pipeline,
            'xnxx': self._get_xnxx_pipeline,
            'motherless': self._get_motherless_pipeline,
        }
        
    async def fetch(self, site: str, query: Optional[str] = None, max_results: int = 30) -> pd.DataFrame:
        """
        Fetch videos from the specified site.
        
        Args:
            site: The site to scrape from (e.g., 'eporner', 'hqporner', 'porntrex', 'xnxx', 'motherless')
            query: Optional search query. If None, fetches popular/trending content
            max_results: Maximum number of results to return (default: 30)
            
        Returns:
            pd.DataFrame: DataFrame with columns 'title', 'url', 'source', 'description'
            
        Raises:
            ValueError: If the site is not supported
        """
        if site.lower() not in self._site_pipelines:
            supported_sites = ', '.join(self._site_pipelines.keys())
            raise ValueError(f"Site '{site}' not supported. Supported sites: {supported_sites}")
        
        pipeline_func = self._site_pipelines[site.lower()]
        flow_def = pipeline_func(query, max_results)
        
        try:
            results = await self._run_flow(flow_def)
            df = self._convert_to_dataframe(results, site.lower())
            
            # Apply max_results slicing and duplicate removal (mirroring old logic)
            if len(df) > max_results:
                df = df.head(max_results)
            
            # Remove duplicates based on URL
            df = df.drop_duplicates(subset=['url'], keep='first')
            
            return df
        except Exception as e:
            logger.error(f"Failed to fetch videos from {site}: {e}")
            return pd.DataFrame(columns=['title', 'url', 'source', 'description'])
    
    async def _run_flow(self, flow_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Crawl4AI flow with robust retry and fallback logic.
        
        Args:
            flow_def: Flow definition dictionary containing URL, selectors, and config
            
        Returns:
            Dict containing the scraped results
            
        Raises:
            Exception: If all retry attempts fail
        """
        retry_times = self.settings.get('retry_times', 3)
        fallback_enabled = self.settings.get('fallback_enabled', True)
        fallback_user_agents = self.settings.get('fallback_user_agents', [])
        backoff_strategy = self.settings.get('backoff_strategy', 'exponential')
        retry_delay_multiplier = self.settings.get('retry_delay_multiplier', 2.0)
        max_retry_delay = self.settings.get('max_retry_delay', 10.0)
        base_delay = self.settings.get('download_delay', 1.0)
        
        last_exception = None
        current_user_agent = self.settings.get('user_agent')
        
        for attempt in range(retry_times):
            try:
                logger.debug(f"Crawl4AI attempt {attempt + 1}/{retry_times} for {flow_def.get('url', 'unknown URL')}")
                
                # Use fallback user agents if enabled and we've failed before
                if (fallback_enabled and attempt > 0 and fallback_user_agents and 
                    self.settings.get('enable_fallback_user_agents', True)):
                    agent_index = (attempt - 1) % len(fallback_user_agents)
                    flow_def['user_agent'] = fallback_user_agents[agent_index]
                    logger.debug(f"Using fallback user agent #{agent_index + 1}")
                else:
                    flow_def['user_agent'] = current_user_agent
                
                # Simulate Crawl4AI execution with enhanced configuration
                results = await self._simulate_crawl4ai_flow(flow_def)
                
                if results and results.get('videos'):
                    logger.info(f"Successfully scraped {len(results.get('videos', []))} videos on attempt {attempt + 1}")
                    return results
                elif results:
                    logger.warning(f"Attempt {attempt + 1} returned no videos")
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)[:100]}...")
                
                # Only sleep if there are more attempts
                if attempt < retry_times - 1:
                    delay = self._calculate_retry_delay(attempt, base_delay, backoff_strategy, 
                                                      retry_delay_multiplier, max_retry_delay)
                    logger.debug(f"Waiting {delay:.2f}s before retry")
                    await asyncio.sleep(delay)
        
        # Log final failure
        logger.error(f"All {retry_times} attempts failed for {flow_def.get('url', 'unknown URL')}")
        
        if last_exception:
            raise last_exception
        else:
            raise Exception("All retry attempts failed with no results")
    
    def _calculate_retry_delay(self, attempt: int, base_delay: float, strategy: str, 
                             multiplier: float, max_delay: float) -> float:
        """
        Calculate retry delay based on the configured backoff strategy.
        
        Args:
            attempt: Current attempt number (0-based)
            base_delay: Base delay in seconds
            strategy: Backoff strategy ('exponential' or 'linear')
            multiplier: Delay multiplier
            max_delay: Maximum delay cap
            
        Returns:
            Calculated delay in seconds
        """
        if strategy == 'exponential':
            delay = base_delay * (multiplier ** attempt)
        else:  # linear
            delay = base_delay + (base_delay * multiplier * attempt)
        
        return min(delay, max_delay)
    
    async def _simulate_crawl4ai_flow(self, flow_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate Crawl4AI flow execution with enhanced error handling - placeholder for actual implementation.
        
        In a real implementation, this would use Crawl4AI's async crawler with:
        - Proper user agent rotation
        - Request headers customization
        - Cookie handling
        - JavaScript rendering if needed
        - Response validation
        
        Args:
            flow_def: Flow definition dictionary
            
        Returns:
            Dictionary with scraped video data
            
        Raises:
            Exception: Various network, parsing, or validation errors
        """
        try:
            logger.debug(
                f"Crawl4AI config: site={flow_def.get('site')}, "
                f"user_agent={flow_def.get('user_agent', 'default')[:50]}..."
            )

            from .adaptive_crawler import AdaptiveCrawler, AdaptiveConfig

            crawler = AdaptiveCrawler(AdaptiveConfig())
            results = await crawler.digest(flow_def.get('url', ''), flow_def.get('query', ''))

            results.update({
                'total_found': len(results.get('videos', [])),
                'site': flow_def.get('site', 'unknown'),
                'url': flow_def.get('url', ''),
                'success': True
            })

            return results

        except Exception as e:
            logger.debug(f"Simulated crawl4ai error: {e}")
            raise
    
    def _convert_to_dataframe(self, results: Dict[str, Any], source: str) -> pd.DataFrame:
        """
        Convert scraped results to standardized DataFrame format.
        
        Args:
            results: Dictionary containing scraped video data
            source: Source site name
            
        Returns:
            pd.DataFrame with columns 'title', 'url', 'source', 'description'
        """
        videos = results.get('videos', [])
        
        if not videos:
            return pd.DataFrame(columns=['title', 'url', 'source', 'description'])
        
        # Ensure all videos have required columns with defaults
        standardized_videos = []
        for video in videos:
            standardized_videos.append({
                'title': video.get('title', 'No Title'),
                'url': video.get('url', ''),
                'source': source,
                'description': video.get('description', '')
            })
        
        return pd.DataFrame(standardized_videos)
    
    def _get_eporner_pipeline(self, query: Optional[str], max_results: int) -> Dict[str, Any]:
        """
        Get Crawl4AI pipeline configuration for Eporner.
        
        Args:
            query: Search query or None for popular content
            max_results: Maximum results to fetch
            
        Returns:
            Dictionary containing pipeline configuration
        """
        flow = EPORNER_FLOW
        url = flow['start'](query)
        
        return {
            'site': 'eporner',
            'url': url,
            'max_results': max_results,
            'flow': flow,
            'selectors': {
                'css': flow['css'],
                'title_attr': flow['title_attr'],
                'href_attr': flow['href_attr'],
                'base_url': flow['base_url']
            },
            'throttle': flow['throttle'],
            'config': self.settings
        }
    
    def _get_hqporner_pipeline(self, query: Optional[str], max_results: int) -> Dict[str, Any]:
        """
        Get Crawl4AI pipeline configuration for HQPorner.
        
        Args:
            query: Search query or None for popular content
            max_results: Maximum results to fetch
            
        Returns:
            Dictionary containing pipeline configuration
        """
        flow = HQPORNER_FLOW
        url = flow['start'](query)
        
        return {
            'site': 'hqporner',
            'url': url,
            'max_results': max_results,
            'flow': flow,
            'selectors': {
                'css': flow['css'],
                'title_attr': flow['title_attr'],
                'href_attr': flow['href_attr'],
                'base_url': flow['base_url']
            },
            'throttle': flow['throttle'],
            'config': self.settings
        }
    
    def _get_porntrex_pipeline(self, query: Optional[str], max_results: int) -> Dict[str, Any]:
        """
        Get Crawl4AI pipeline configuration for Porntrex.
        
        Args:
            query: Search query or None for popular content
            max_results: Maximum results to fetch
            
        Returns:
            Dictionary containing pipeline configuration
        """
        flow = PORNTREX_FLOW
        url = flow['start'](query)
        
        return {
            'site': 'porntrex',
            'url': url,
            'max_results': max_results,
            'flow': flow,
            'selectors': {
                'css': flow['css'],
                'title_attr': flow['title_attr'],
                'href_attr': flow['href_attr'],
                'base_url': flow['base_url']
            },
            'throttle': flow['throttle'],
            'config': self.settings
        }
    
    def _get_xnxx_pipeline(self, query: Optional[str], max_results: int) -> Dict[str, Any]:
        """
        Get Crawl4AI pipeline configuration for XNXX.
        
        Args:
            query: Search query or None for popular content
            max_results: Maximum results to fetch
            
        Returns:
            Dictionary containing pipeline configuration
        """
        flow = XNXX_FLOW
        url = flow['start'](query)
        
        return {
            'site': 'xnxx',
            'url': url,
            'max_results': max_results,
            'flow': flow,
            'selectors': {
                'css': flow['css'],
                'title_attr': flow['title_attr'],
                'href_attr': flow['href_attr'],
                'base_url': flow['base_url']
            },
            'throttle': flow['throttle'],
            'config': self.settings
        }
    
    def _get_motherless_pipeline(self, query: Optional[str], max_results: int) -> Dict[str, Any]:
        """
        Get Crawl4AI pipeline configuration for Motherless.
        
        Args:
            query: Search query or None for popular content
            max_results: Maximum results to fetch
            
        Returns:
            Dictionary containing pipeline configuration
        """
        flow = MOTHERLESS_FLOW
        url = flow['start'](query)
        
        return {
            'site': 'motherless',
            'url': url,
            'max_results': max_results,
            'flow': flow,
            'selectors': {
                'css': flow['css'],
                'title_attr': flow['title_attr'],
                'href_attr': flow['href_attr'],
                'base_url': flow['base_url']
            },
            'throttle': flow['throttle'],
            'config': self.settings
        }
