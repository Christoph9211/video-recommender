# Enhanced Error Handling and Logging

This document describes the robust error handling and logging features implemented in the video recommender system as part of Step 9 improvements.

## Features Implemented

### 1. Crawl4AI Built-in Retry + Fallback Options

The system now includes comprehensive retry and fallback mechanisms:

- **Configurable retry attempts** (default: 3)
- **Exponential/Linear backoff strategies** 
- **Fallback user agent rotation**
- **Maximum retry delay caps**
- **Per-attempt timeout handling**

#### Configuration Options

```python
CRAWL4AI_DEFAULTS = {
    "retry_times": 3,
    "fallback_enabled": True,
    "fallback_delay": 2.0,
    "retry_delay_multiplier": 2.0,
    "max_retry_delay": 10.0,
    "backoff_strategy": "exponential",  # or "linear"
    "enable_fallback_user_agents": True,
    "fallback_user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36..."
    ]
}
```

#### Environment Variable Overrides

You can customize settings without code changes:

```bash
export CRAWL4AI_RETRY_TIMES=5
export CRAWL4AI_FALLBACK_ENABLED=true
export CRAWL4AI_BACKOFF_STRATEGY=linear
export CRAWL4AI_MAX_RETRY_DELAY=15.0
```

### 2. Robust Error Handling with Try/Except

All public scraping calls are wrapped in comprehensive try/except blocks:

```python
async def fetch(self, site: str, query: Optional[str] = None, max_results: int = 30) -> pd.DataFrame:
    try:
        results = await self._run_flow(flow_def)
        df = self._convert_to_dataframe(results, site.lower())
        return df
    except Exception as e:
        logger.error(f"Failed to fetch videos from {site}: {e}")
        return pd.DataFrame(columns=['title', 'url', 'source', 'description'])
```

**Key behaviors:**
- **Graceful degradation**: Failed scraping returns empty DataFrame instead of crashing
- **Detailed error logging**: Full error context logged for debugging
- **Site isolation**: Failure of one site doesn't affect others
- **Fallback data**: Example data provided when all scraping fails

### 3. Comprehensive Logging System

#### Logging Levels

- **INFO**: General operation status and success messages
- **WARNING**: Non-fatal issues (empty results, single site failures)
- **ERROR**: Failed operations with recovery
- **DEBUG**: Detailed diagnostic information (enabled with `--verbose`)

#### Log Format

```
2024-01-15 10:30:45 - video_recommender.scrapers - INFO - Successfully scraped 25 videos on attempt 1
2024-01-15 10:30:46 - video_recommender.scrapers - WARNING - Attempt 2 returned no videos  
2024-01-15 10:30:47 - video_recommender.scrapers - ERROR - All 3 attempts failed for https://example.com
2024-01-15 10:30:47 - video_recommender.scrapers - DEBUG - Using fallback user agent #2
```

### 4. CLI Verbose Flag

The `--verbose` flag provides enhanced debugging information:

#### Basic Usage
```bash
python cli.py --query "python programming"
```

#### Verbose Mode
```bash
python cli.py --query "python programming" --verbose
```

#### Additional CLI Options
```bash
python cli.py \
    --bookmarks favorites.txt \
    --query "machine learning" \
    --verbose \
    --max-recommendations 50 \
    --no-fallback
```

## Implementation Details

### Retry Logic Flow

1. **Initial Attempt**: Use default configuration
2. **Retry with Backoff**: Calculate delay based on strategy
3. **Fallback User Agents**: Rotate through different agents
4. **Final Failure**: Log comprehensive error and return empty results

### Error Recovery Strategies

#### Network Failures
- Automatic retry with increasing delays
- User agent rotation to avoid detection
- Timeout handling with graceful fallback

#### Parsing Failures  
- Detailed error logging with truncated messages
- Continue processing other sites
- Return partial results when possible

#### Configuration Errors
- Environment variable validation
- Fallback to defaults for invalid values
- Clear error messages for user issues

### Logging Configuration

#### Production Logging
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### Debug Logging  
```python
if verbose:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('video_recommender.scrapers').setLevel(logging.DEBUG)
```

## Usage Examples

### Basic Error Handling
```python
from video_recommender.scrapers import Crawl4aiVideoScraper

scraper = Crawl4aiVideoScraper()

# This will handle errors gracefully
df = await scraper.fetch("eporner", "python", max_results=20)
if df.empty:
    print("No results found, but no crash!")
```

### Custom Retry Configuration
```python
custom_settings = {
    'retry_times': 5,
    'backoff_strategy': 'linear',
    'fallback_enabled': True,
    'max_retry_delay': 15.0
}

scraper = Crawl4aiVideoScraper(settings=custom_settings)
```

### Multi-Site Error Handling
```python
sites = ['eporner', 'hqporner', 'porntrex']
all_results = []

for site in sites:
    try:
        df = await scraper.fetch(site=site, query='programming')
        if not df.empty:
            all_results.append(df)
            logger.info(f"Success: {len(df)} videos from {site}")
    except Exception as e:
        logger.error(f"Failed {site}: {e}")
        # Continue with other sites
```

## Testing the Features

### Run Basic Example
```bash
python video_recommender/example_usage.py
```

### Test CLI with Verbose Output
```bash
python cli.py --query "test" --verbose
```

### Test Error Scenarios
```bash
# Test with non-existent bookmarks file
python cli.py --bookmarks missing.txt --verbose

# Test with disabled fallback
python cli.py --query "test" --no-fallback --verbose
```

## Environment Variables Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CRAWL4AI_RETRY_TIMES` | int | 3 | Number of retry attempts |
| `CRAWL4AI_FALLBACK_ENABLED` | bool | true | Enable fallback mechanisms |
| `CRAWL4AI_BACKOFF_STRATEGY` | str | exponential | Backoff strategy (exponential/linear) |
| `CRAWL4AI_RETRY_DELAY_MULTIPLIER` | float | 2.0 | Delay multiplier for retries |
| `CRAWL4AI_MAX_RETRY_DELAY` | float | 10.0 | Maximum delay between retries |
| `CRAWL4AI_DOWNLOAD_DELAY` | float | 1.0 | Base delay between requests |
| `CRAWL4AI_TIMEOUT` | int | 20 | Request timeout in seconds |

## Best Practices

1. **Always use verbose mode during development** for better debugging
2. **Set appropriate retry limits** to balance reliability vs performance  
3. **Monitor logs** for patterns in failure modes
4. **Use environment variables** for production configuration
5. **Implement circuit breakers** for frequently failing sites
6. **Handle empty DataFrames** gracefully in your application logic

## Future Enhancements

- [ ] Circuit breaker pattern for failing sites
- [ ] Retry with exponential jitter
- [ ] Structured logging (JSON format)
- [ ] Metrics collection for success/failure rates
- [ ] Automatic user agent updates
- [ ] Site-specific retry strategies
