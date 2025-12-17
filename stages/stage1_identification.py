"""
Stage 1: Identification
Searches PubMed for leads based on scientific keywords
Long-term solution with proper error handling and cache management
"""

import logging
from typing import List, Dict
import streamlit as st
from utils.pubmed_api import search_pubmed
from utils.data_processing import deduplicate_leads
from stages.cache_manager import CacheManager

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize cache manager
cache_manager = CacheManager()


def run_stage1(criteria: Dict) -> List[Dict]:
    """
    Stage 1: Identification
    Scans PubMed based on scientific keywords and extracts leads
    
    Args:
        criteria: Dictionary containing search criteria:
            - scientific_keywords: List of keywords to search
            - results_per_keyword: Number of results per keyword
            - years_back: Number of years to look back (default: 2)
    
    Returns:
        List of lead dictionaries
    """
    scientific_keywords = criteria.get('scientific_keywords', [])
    results_per_keyword = criteria.get('results_per_keyword', 50)
    years_back = criteria.get('years_back', 2)
    
    if not scientific_keywords:
        st.warning("⚠️ No scientific keywords provided. Please enter keywords in the sidebar.")
        return []
    
    all_results = []
    
    # Process each keyword
    total_keywords = len(scientific_keywords)
    for idx, keyword in enumerate(scientific_keywords, 1):
        keyword = keyword.strip()
        if not keyword:
            continue
        
        st.info(f"🔍 Searching PubMed for: '{keyword}' ({idx}/{total_keywords})")
        
        # Check cache first
        cache_key = f"{keyword}_{results_per_keyword}_{years_back}"
        cached_results = cache_manager.get_cached_results(cache_key)
        
        if cached_results:
            st.success(f"✅ Using cached results for '{keyword}' ({len(cached_results)} leads)")
            all_results.extend(cached_results)
        else:
            # Search PubMed
            try:
                with st.spinner(f"Fetching data from PubMed for '{keyword}'..."):
                    keyword_results = search_pubmed(
                        keyword=keyword,
                        max_results=results_per_keyword,
                        years_back=years_back
                    )
                
                if keyword_results:
                    st.success(f"✅ Found {len(keyword_results)} leads for '{keyword}'")
                    all_results.extend(keyword_results)
                    
                    # Cache the results
                    cache_manager.save_query_results(cache_key, keyword_results)
                else:
                    st.warning(f"⚠️ No results found for '{keyword}'")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error searching PubMed for '{keyword}': {error_msg}")
                st.error(f"❌ Error searching PubMed for '{keyword}': {error_msg}")
                # Continue with next keyword instead of failing completely
                continue
    
    if not all_results:
        st.warning("⚠️ No leads found. Try different keywords or increase results per keyword.")
        return []
    
    # Deduplicate results
    st.info("🔄 Deduplicating results...")
    try:
        deduplicated_results = deduplicate_leads(all_results)
        if len(deduplicated_results) != len(all_results):
            st.success(f"✅ Deduplication complete: {len(all_results)} → {len(deduplicated_results)} unique leads")
        else:
            st.info(f"ℹ️ No duplicates found: {len(deduplicated_results)} unique leads")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error during deduplication: {error_msg}")
        st.error(f"❌ Error during deduplication: {error_msg}")
        # Return original results if deduplication fails (better than empty list)
        deduplicated_results = all_results
    
    return deduplicated_results


def clear_cache() -> bool:
    """
    Clear all cached results using cache manager
    
    Returns:
        True if successful, False otherwise
    """
    return cache_manager.clear_all_cache()


def get_cache_info() -> Dict:
    """
    Get cache information
    
    Returns:
        Dictionary with cache information
    """
    return cache_manager.get_cache_info()

