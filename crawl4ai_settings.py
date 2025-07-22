"""
Crawl4AI Configuration Settings

This module provides default settings for Crawl4AI operations with environment variable
override support for power users to customize without code changes.
"""

import os


# Default configuration values
CRAWL4AI_DEFAULTS = {
    "user_agent": "Mozilla/5.0 (compatible; VideoRecommender/1.0)",
    "max_concurrent": 2,
    "download_delay": 1.0,
    "retry_times": 3,
    "timeout": 20,
    "fallback_enabled": True,
    "fallback_delay": 2.0,
    "retry_delay_multiplier": 2.0,
    "max_retry_delay": 10.0,
    "backoff_strategy": "exponential",  # or "linear"
    "enable_fallback_user_agents": True,
    "fallback_user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]
}


def get_crawl4ai_config():
    """
    Get Crawl4AI configuration with environment variable overrides.
    
    Environment variables:
    - CRAWL4AI_USER_AGENT: Override user agent string
    - CRAWL4AI_MAX_CONCURRENT: Override max concurrent requests (int)
    - CRAWL4AI_DOWNLOAD_DELAY: Override download delay in seconds (float)
    - CRAWL4AI_RETRY_TIMES: Override retry attempts (int)
    - CRAWL4AI_TIMEOUT: Override timeout in seconds (int)
    
    Returns:
        dict: Configuration dictionary with defaults and overrides applied
    """
    config = CRAWL4AI_DEFAULTS.copy()
    
    # Apply environment variable overrides
    if os.getenv("CRAWL4AI_USER_AGENT"):
        config["user_agent"] = os.getenv("CRAWL4AI_USER_AGENT")
    
    if os.getenv("CRAWL4AI_MAX_CONCURRENT"):
        try:
            config["max_concurrent"] = int(os.getenv("CRAWL4AI_MAX_CONCURRENT"))
        except ValueError:
            pass  # Keep default if invalid value
    
    if os.getenv("CRAWL4AI_DOWNLOAD_DELAY"):
        try:
            config["download_delay"] = float(os.getenv("CRAWL4AI_DOWNLOAD_DELAY"))
        except ValueError:
            pass  # Keep default if invalid value
    
    if os.getenv("CRAWL4AI_RETRY_TIMES"):
        try:
            config["retry_times"] = int(os.getenv("CRAWL4AI_RETRY_TIMES"))
        except ValueError:
            pass  # Keep default if invalid value
    
    if os.getenv("CRAWL4AI_TIMEOUT"):
        try:
            config["timeout"] = int(os.getenv("CRAWL4AI_TIMEOUT"))
        except ValueError:
            pass  # Keep default if invalid value
    
    # Additional fallback and retry settings
    if os.getenv("CRAWL4AI_FALLBACK_ENABLED"):
        config["fallback_enabled"] = os.getenv("CRAWL4AI_FALLBACK_ENABLED").lower() == "true"
    
    if os.getenv("CRAWL4AI_FALLBACK_DELAY"):
        try:
            config["fallback_delay"] = float(os.getenv("CRAWL4AI_FALLBACK_DELAY"))
        except ValueError:
            pass
    
    if os.getenv("CRAWL4AI_RETRY_DELAY_MULTIPLIER"):
        try:
            config["retry_delay_multiplier"] = float(os.getenv("CRAWL4AI_RETRY_DELAY_MULTIPLIER"))
        except ValueError:
            pass
    
    if os.getenv("CRAWL4AI_MAX_RETRY_DELAY"):
        try:
            config["max_retry_delay"] = float(os.getenv("CRAWL4AI_MAX_RETRY_DELAY"))
        except ValueError:
            pass
    
    if os.getenv("CRAWL4AI_BACKOFF_STRATEGY"):
        strategy = os.getenv("CRAWL4AI_BACKOFF_STRATEGY").lower()
        if strategy in ["exponential", "linear"]:
            config["backoff_strategy"] = strategy
    
    return config


# Convenience function to get individual settings
def get_user_agent():
    """Get the user agent string with environment override support."""
    return os.getenv("CRAWL4AI_USER_AGENT", CRAWL4AI_DEFAULTS["user_agent"])


def get_max_concurrent():
    """Get the max concurrent requests with environment override support."""
    try:
        return int(os.getenv("CRAWL4AI_MAX_CONCURRENT", CRAWL4AI_DEFAULTS["max_concurrent"]))
    except ValueError:
        return CRAWL4AI_DEFAULTS["max_concurrent"]


def get_download_delay():
    """Get the download delay with environment override support."""
    try:
        return float(os.getenv("CRAWL4AI_DOWNLOAD_DELAY", CRAWL4AI_DEFAULTS["download_delay"]))
    except ValueError:
        return CRAWL4AI_DEFAULTS["download_delay"]


def get_retry_times():
    """Get the retry times with environment override support."""
    try:
        return int(os.getenv("CRAWL4AI_RETRY_TIMES", CRAWL4AI_DEFAULTS["retry_times"]))
    except ValueError:
        return CRAWL4AI_DEFAULTS["retry_times"]


def get_timeout():
    """Get the timeout with environment override support."""
    try:
        return int(os.getenv("CRAWL4AI_TIMEOUT", CRAWL4AI_DEFAULTS["timeout"]))
    except ValueError:
        return CRAWL4AI_DEFAULTS["timeout"]
