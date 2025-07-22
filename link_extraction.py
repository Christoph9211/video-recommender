import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import LinkPreviewConfig

async def extract_link_heads_example():
    """
    Complete example showing link head extraction with scoring.
    This will crawl a documentation site and extract head content from internal links.
    """

    # Configure link head extraction
    config = CrawlerRunConfig(
        # Enable link head extraction with detailed configuration
        link_preview_config=LinkPreviewConfig(
            include_internal=True,           # Extract from internal links
            include_external=False,          # Skip external links for this example
            max_links=100,                   # Limit to 10 links for demo
            concurrency=5,                  # Process 5 links simultaneously
            timeout=10,                     # 10 second timeout per link
            query="4k", # Query for contextual scoring
            score_threshold=0.3,            # Only include links scoring above 0.3
            verbose=True                    # Show detailed progress
        ),
        # Enable intrinsic scoring (URL quality, text relevance)
        score_links=True,
        # Keep output clean
        only_text=True,
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        # Crawl a documentation site (great for testing)
        result = await crawler.arun("https://www.eporner.com/video-4eJIWhw8aYB/aj-applegate-angela-white-hot-lesbian-sex/", config=config)

        if result.success:
            print(f"✅ Successfully crawled: {result.url}")
            print(f"📄 Page title: {result.metadata.get('title', 'No title')}")

            # Access links (now enhanced with head data and scores)
            internal_links = result.links.get("internal", [])
            external_links = result.links.get("external", [])

            print(f"\n🔗 Found {len(internal_links)} internal links")
            print(f"🌍 Found {len(external_links)} external links")

            # Count links with head data
            links_with_head = [link for link in internal_links 
                             if link.get("head_data") is not None]
            print(f"🧠 Links with head data extracted: {len(links_with_head)}")

            # Show the top 10 scoring links
            print(f"\n🏆 Top 10 Links with Full Scoring:")
            for i, link in enumerate(links_with_head[:10]):
                print(f"\n{i+1}. {link['href']}")
                print(f"   Link Text: '{link.get('text', 'No text')[:50]}...'")

                # Show all three score types
                intrinsic = link.get('intrinsic_score')
                contextual = link.get('contextual_score') 
                total = link.get('total_score')

                if intrinsic is not None:
                    print(f"   📊 Intrinsic Score: {intrinsic:.2f}/10.0 (URL quality & context)")
                if contextual is not None:
                    print(f"   🎯 Contextual Score: {contextual:.3f} (BM25 relevance to query)")
                if total is not None:
                    print(f"   ⭐ Total Score: {total:.3f} (combined final score)")

                # Show extracted head data
                head_data = link.get("head_data", {})
                if head_data:
                    title = head_data.get("title", "No title")
                    description = head_data.get("meta", {}).get("description", "No description")

                    print(f"   📰 Title: {title[:60]}...")
                    if description:
                        print(f"   📝 Description: {description[:80]}...")

                    # Show extraction status
                    status = link.get("head_extraction_status", "unknown")
                    print(f"   ✅ Extraction Status: {status}")
        else:
            print(f"❌ Crawl failed: {result.error_message}")

# Run the example
if __name__ == "__main__":
    asyncio.run(extract_link_heads_example())
