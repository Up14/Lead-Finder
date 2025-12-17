"""
Stage 2: Enrichment
Enriches Stage 1 leads with contact info, location data, company info, and LinkedIn profiles
Uses free trial APIs with configurable limits to conserve credits
"""

import json
import os
import hashlib
import logging
from typing import List, Dict, Optional
from datetime import datetime
import streamlit as st
from utils.email_finder import find_email
from utils.phone_finder import find_phone
from utils.company_enricher import enrich_company
from utils.linkedin_finder import find_linkedin, get_company_from_linkedin
from utils.api_credit_manager import APICreditManager
from stages.cache_manager import CacheManager

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize managers
credit_manager = APICreditManager()
cache_manager = CacheManager(cache_file="data/cache/stage2_enrichment.json")


def _generate_cache_key(lead: Dict) -> str:
    """
    Generate cache key for a lead based on name and company
    
    Args:
        lead: Lead dictionary
    
    Returns:
        Cache key string
    """
    name = lead.get('name', '').lower().strip()
    company = lead.get('company', '').lower().strip()
    key_string = f"{name}_{company}"
    return hashlib.md5(key_string.encode()).hexdigest()


def _get_cached_enrichment(lead: Dict) -> Optional[Dict]:
    """
    Get cached enrichment data for a lead
    
    Args:
        lead: Lead dictionary
    
    Returns:
        Cached enrichment data or None
    """
    cache_key = _generate_cache_key(lead)
    cache = cache_manager.load_cache()
    
    enriched_leads = cache.get('enriched_leads', {})
    if cache_key in enriched_leads:
        entry = enriched_leads[cache_key]
        # Check if cache is still valid (30 days)
        timestamp_str = entry.get('timestamp', '')
        if timestamp_str:
            try:
                entry_date = datetime.fromisoformat(timestamp_str)
                if (datetime.now() - entry_date).days < 30:
                    return entry.get('data')
            except (ValueError, TypeError):
                pass
    
    return None


def _save_enrichment_cache(lead: Dict, enriched_data: Dict):
    """
    Save enriched data to cache
    
    Args:
        lead: Original lead dictionary
        enriched_data: Enriched lead data
    """
    cache_key = _generate_cache_key(lead)
    cache = cache_manager.load_cache()
    
    if 'enriched_leads' not in cache:
        cache['enriched_leads'] = {}
    
    cache['enriched_leads'][cache_key] = {
        'timestamp': datetime.now().isoformat(),
        'data': enriched_data
    }
    
    cache_manager.save_cache(cache)


def _enrich_single_lead(lead: Dict, api_keys: Dict) -> Dict:
    """
    Enrich a single lead with all available data sources
    
    Args:
        lead: Lead dictionary from Stage 1
        api_keys: Dictionary with API keys (apollo, hunter, clearbit)
    
    Returns:
        Enriched lead dictionary
    """
    # Start with original lead data
    enriched = lead.copy()
    
    # Track enrichment status
    enrichment_status = []
    api_credits_used = {}
    
    name = lead.get('name', '')
    company = lead.get('company', '')
    
    if not name:
        enriched['enrichment_status'] = 'failed'
        enriched['enrichment_errors'] = 'Missing name'
        return enriched
    
    # Step 1: Get proper company name from LinkedIn/API (priority)
    if api_keys.get('apollo'):
        try:
            company_from_linkedin = get_company_from_linkedin(
                name, company, api_keys['apollo']
            )
            if company_from_linkedin:
                company = company_from_linkedin
                enriched['company_name_verified'] = company_from_linkedin
                enrichment_status.append('company_name')
        except Exception as e:
            logger.debug(f"Error getting company from LinkedIn: {e}")
    
    # Step 2: Find LinkedIn profile
    if api_keys.get('apollo'):
        try:
            linkedin_data = find_linkedin(name, company, api_keys['apollo'])
            if linkedin_data:
                if linkedin_data.get('linkedin_url'):
                    enriched['linkedin_url'] = linkedin_data['linkedin_url']
                if linkedin_data.get('linkedin_title'):
                    enriched['linkedin_title'] = linkedin_data['linkedin_title']
                if linkedin_data.get('company_name_verified'):
                    enriched['company_name_verified'] = linkedin_data['company_name_verified']
                    company = linkedin_data['company_name_verified']  # Update for subsequent calls
                enrichment_status.append('linkedin')
        except Exception as e:
            logger.debug(f"Error finding LinkedIn: {e}")
    
    # Step 3: Find email (only if not already a valid business email)
    existing_email = lead.get('email', '')
    if not existing_email or '@' not in existing_email:
        if api_keys.get('apollo') or api_keys.get('hunter') or api_keys.get('contactout'):
            try:
                # Get LinkedIn URL if available (from Step 2 or original lead)
                linkedin_url = enriched.get('linkedin_url') or lead.get('linkedin_url', '')
                
                email_data = find_email(
                    name, company,
                    api_keys.get('apollo'),
                    api_keys.get('hunter'),
                    api_keys.get('contactout'),
                    linkedin_url if linkedin_url else None
                )
                if email_data.get('email'):
                    enriched['email'] = email_data['email']
                    enriched['email_source'] = email_data.get('email_source', '')
                    enriched['email_confidence'] = email_data.get('email_confidence', '')
                    # ContactOut can also return phone, store it if available
                    if email_data.get('phone'):
                        enriched['phone'] = email_data['phone']
                        enriched['phone_source'] = 'ContactOut API'
                    enrichment_status.append('email')
            except Exception as e:
                logger.debug(f"Error finding email: {e}")
    
    # Step 4: Find phone
    if api_keys.get('apollo'):
        try:
            phone_data = find_phone(name, company, api_keys['apollo'])
            if phone_data.get('phone'):
                enriched['phone'] = phone_data['phone']
                enriched['phone_source'] = phone_data.get('phone_source', '')
                enrichment_status.append('phone')
        except Exception as e:
            logger.debug(f"Error finding phone: {e}")
    
    # Step 5: Enrich company data (HQ, funding, size)
    if company and (api_keys.get('apollo') or api_keys.get('clearbit')):
        try:
            company_data = enrich_company(
                company,
                api_keys.get('apollo'),
                api_keys.get('clearbit')
            )
            if company_data:
                # Update company name if verified
                if company_data.get('company_name_verified'):
                    enriched['company_name_verified'] = company_data['company_name_verified']
                
                # Add company enrichment data
                if company_data.get('company_hq'):
                    enriched['company_hq'] = company_data['company_hq']
                if company_data.get('company_hq_address'):
                    enriched['company_hq_address'] = company_data['company_hq_address']
                if company_data.get('company_size'):
                    enriched['company_size'] = company_data['company_size']
                if company_data.get('company_industry'):
                    enriched['company_industry'] = company_data['company_industry']
                if company_data.get('company_funding_stage'):
                    enriched['company_funding_stage'] = company_data['company_funding_stage']
                if company_data.get('company_funding_amount'):
                    enriched['company_funding_amount'] = company_data['company_funding_amount']
                
                enrichment_status.append('company_data')
        except Exception as e:
            logger.debug(f"Error enriching company: {e}")
    
    # Step 6: Refine person location (keep existing if available)
    if lead.get('location'):
        enriched['person_location'] = lead['location']
    
    # Determine overall enrichment status
    if len(enrichment_status) >= 3:
        enriched['enrichment_status'] = 'success'
    elif len(enrichment_status) >= 1:
        enriched['enrichment_status'] = 'partial'
    else:
        enriched['enrichment_status'] = 'failed'
    
    enriched['enrichment_timestamp'] = datetime.now().isoformat()
    enriched['enrichment_fields'] = enrichment_status
    
    # Get API credits used
    all_credits = credit_manager.get_all_credits()
    enriched['api_credits_info'] = all_credits
    
    return enriched


def run_stage2(stage1_data: List[Dict], leads_to_enrich: int = 5,
                api_keys: Optional[Dict] = None, priority: str = 'first_n') -> List[Dict]:
    """
    Stage 2: Enrichment
    Enriches leads from Stage 1 with contact info, location, company data, LinkedIn
    
    Args:
        stage1_data: List of lead dictionaries from Stage 1
        leads_to_enrich: Number of leads to enrich (default: 5)
        api_keys: Dictionary with API keys (apollo, hunter, clearbit)
        priority: Priority method ('first_n', 'corresponding_first')
    
    Returns:
        List of enriched lead dictionaries
    """
    if not stage1_data:
        st.warning("⚠️ No Stage 1 data available. Please run Stage 1 first.")
        return []
    
    if not api_keys or not any(api_keys.values()):
        st.warning("⚠️ No API keys provided. Please configure API keys in the sidebar.")
        return []
    
    # Check if Apollo.io is being used and warn about free plan limitations
    if api_keys.get('apollo'):
        st.info("ℹ️ **Apollo.io Free Plan Note**: The free plan has limited access to search endpoints. "
                "If you see 403 errors, consider using Hunter.io for email finding or upgrading your Apollo.io plan.")
    
    # Initialize API credit tracking
    for api_name in ['apollo', 'hunter', 'clearbit']:
        if api_keys.get(api_name):
            credit_manager.initialize_api(api_name, quota_limit=100)  # Default quota
    
    # Select leads to enrich based on priority
    leads_to_process = []
    
    if priority == 'corresponding_first':
        # Prioritize Corresponding Authors, then First Authors
        corresponding = [l for l in stage1_data if l.get('author_position') == 'Corresponding Author']
        first_authors = [l for l in stage1_data if l.get('author_position') == 'First Author']
        others = [l for l in stage1_data if l not in corresponding and l not in first_authors]
        
        leads_to_process = (corresponding + first_authors + others)[:leads_to_enrich]
    else:
        # First N leads
        leads_to_process = stage1_data[:leads_to_enrich]
    
    if not leads_to_process:
        st.warning("⚠️ No leads selected for enrichment.")
        return []
    
    st.info(f"🔄 Enriching {len(leads_to_process)} leads...")
    
    # Check for Apollo.io free plan limitations
    apollo_available = api_keys.get('apollo') and credit_manager.can_make_call('apollo')
    if api_keys.get('apollo') and not apollo_available:
        st.warning("⚠️ Apollo.io credits exhausted or API key invalid. Will try alternative APIs if available.")
    elif api_keys.get('apollo'):
        st.info("ℹ️ Using Apollo.io API (note: free plan has limited endpoint access)")
    
    enriched_results = []
    progress_bar = st.progress(0)
    
    for idx, lead in enumerate(leads_to_process):
        # Check cache first
        cached_data = _get_cached_enrichment(lead)
        
        if cached_data:
            st.success(f"✅ Using cached data for {lead.get('name', 'Unknown')}")
            enriched_results.append(cached_data)
        else:
            # Check API credits before processing
            can_process = True
            if api_keys.get('apollo') and not credit_manager.can_make_call('apollo'):
                st.warning(f"⚠️ Apollo.io credits exhausted. Skipping {lead.get('name', 'Unknown')}")
                can_process = False
            
            if can_process:
                try:
                    with st.spinner(f"Enriching {lead.get('name', 'Unknown')} ({idx+1}/{len(leads_to_process)})..."):
                        enriched_lead = _enrich_single_lead(lead, api_keys)
                        enriched_results.append(enriched_lead)
                        
                        # Cache the result
                        _save_enrichment_cache(lead, enriched_lead)
                        
                        # Show status
                        status = enriched_lead.get('enrichment_status', 'unknown')
                        if status == 'success':
                            st.success(f"✅ Enriched {lead.get('name', 'Unknown')} - Success")
                        elif status == 'partial':
                            st.info(f"ℹ️ Enriched {lead.get('name', 'Unknown')} - Partial")
                        else:
                            st.warning(f"⚠️ Failed to enrich {lead.get('name', 'Unknown')}")
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error enriching lead {lead.get('name', 'Unknown')}: {error_msg}")
                    st.error(f"❌ Error enriching {lead.get('name', 'Unknown')}: {error_msg}")
                    # Add original lead with error status
                    lead_copy = lead.copy()
                    lead_copy['enrichment_status'] = 'failed'
                    lead_copy['enrichment_errors'] = error_msg
                    enriched_results.append(lead_copy)
        
        # Update progress
        progress_bar.progress((idx + 1) / len(leads_to_process))
    
    # Show summary
    success_count = sum(1 for r in enriched_results if r.get('enrichment_status') == 'success')
    partial_count = sum(1 for r in enriched_results if r.get('enrichment_status') == 'partial')
    failed_count = sum(1 for r in enriched_results if r.get('enrichment_status') == 'failed')
    
    st.success(f"✅ Stage 2 Complete: {success_count} success, {partial_count} partial, {failed_count} failed")
    
    return enriched_results


def get_api_credit_info() -> Dict:
    """
    Get API credit information for display
    
    Returns:
        Dictionary with credit information for all APIs
    """
    return credit_manager.get_all_credits()

