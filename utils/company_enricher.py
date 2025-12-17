"""
Company Enricher
Enriches company data with HQ location, funding info, size, industry
Uses Apollo.io, Clearbit, or Crunchbase APIs
"""

import requests
import logging
from typing import Dict, Optional
from utils.api_credit_manager import APICreditManager

logger = logging.getLogger(__name__)

# Initialize credit manager
credit_manager = APICreditManager()


def enrich_company_apollo(company_name: str, api_key: str) -> Optional[Dict]:
    """
    Enrich company data using Apollo.io API
    
    Args:
        company_name: Company name
        api_key: Apollo.io API key
    
    Returns:
        Dictionary with company data or None if not found
    """
    if not credit_manager.can_make_call('apollo'):
        logger.warning("Apollo.io credits exhausted")
        return None
    
    try:
        # Apollo.io API endpoint for organization search
        url = "https://api.apollo.io/v1/organizations/search"
        
        headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "X-Api-Key": api_key  # API key in header (correct format)
        }
        
        payload = {
            "name": company_name,
            "page": 1,
            "per_page": 1
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Check for errors and handle appropriately
        if response.status_code == 403:
            # Free plan doesn't support this endpoint
            logger.warning("Apollo.io free plan doesn't support organization search")
            return None
        elif response.status_code != 200:
            error_detail = response.text
            logger.error(f"Apollo.io API error {response.status_code}: {error_detail}")
            return None
        
        data = response.json()
        
        # Record API call only on success
        credit_manager.record_api_call('apollo')
        
        # Extract company data from response
        organizations = data.get('organizations', [])
        if organizations and len(organizations) > 0:
            org = organizations[0]
            
            # Extract location
            city = org.get('city', '')
            state = org.get('state', '')
            country = org.get('country', '')
            location_parts = [p for p in [city, state, country] if p]
            hq_location = ', '.join(location_parts) if location_parts else ''
            
            return {
                'company_name_verified': org.get('name', company_name),
                'company_hq': hq_location,
                'company_hq_address': org.get('street_address', ''),
                'company_size': org.get('estimated_num_employees', ''),
                'company_industry': org.get('industry', ''),
                'company_website': org.get('website_url', ''),
                'company_linkedin': org.get('linkedin_url', ''),
                'source': 'Apollo API'
            }
        
        return None
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.text
                logger.error(f"Apollo.io API error: {error_msg}. Response: {error_detail}")
            except Exception:
                logger.error(f"Apollo.io API error: {error_msg}")
        else:
            logger.error(f"Apollo.io API error: {error_msg}")
        return None
    except Exception as e:
        logger.error(f"Error enriching company via Apollo: {e}")
        return None


def enrich_company_clearbit(company_name: str, api_key: str) -> Optional[Dict]:
    """
    Enrich company data using Clearbit API
    
    Args:
        company_name: Company name
        api_key: Clearbit API key
    
    Returns:
        Dictionary with company data or None if not found
    """
    if not credit_manager.can_make_call('clearbit'):
        logger.warning("Clearbit credits exhausted")
        return None
    
    try:
        # Clearbit Company API endpoint
        # Note: Clearbit uses domain, so we need to search by name first or use domain
        # For now, using name search endpoint if available
        url = f"https://company.clearbit.com/v2/companies/find"
        
        params = {
            "name": company_name
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Record API call
        credit_manager.record_api_call('clearbit')
        
        # Extract company data
        if data:
            location = data.get('geo', {})
            city = location.get('city', '')
            state = location.get('state', '')
            country = location.get('country', '')
            location_parts = [p for p in [city, state, country] if p]
            hq_location = ', '.join(location_parts) if location_parts else ''
            
            return {
                'company_name_verified': data.get('name', company_name),
                'company_hq': hq_location,
                'company_hq_address': '',
                'company_size': data.get('metrics', {}).get('employees', ''),
                'company_industry': data.get('category', {}).get('industry', ''),
                'company_website': data.get('domain', ''),
                'company_linkedin': data.get('linkedin', {}).get('handle', ''),
                'source': 'Clearbit API'
            }
        
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Clearbit API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error enriching company via Clearbit: {e}")
        return None


def enrich_company(company_name: str, apollo_key: Optional[str] = None,
                   clearbit_key: Optional[str] = None) -> Dict:
    """
    Enrich company data using available APIs
    
    Args:
        company_name: Company name
        apollo_key: Apollo.io API key (optional)
        clearbit_key: Clearbit API key (optional)
    
    Returns:
        Dictionary with enriched company data
    """
    result = {
        'company_name_verified': company_name,
        'company_hq': '',
        'company_hq_address': '',
        'company_size': '',
        'company_industry': '',
        'company_website': '',
        'company_linkedin': '',
        'company_funding_stage': '',
        'company_funding_amount': '',
        'company_funding_date': '',
        'source': ''
    }
    
    # Try Apollo first
    if apollo_key:
        apollo_result = enrich_company_apollo(company_name, apollo_key)
        if apollo_result:
            result.update(apollo_result)
            return result
    
    # Try Clearbit as fallback
    if clearbit_key:
        clearbit_result = enrich_company_clearbit(company_name, clearbit_key)
        if clearbit_result:
            # Merge with existing result (don't overwrite if Apollo already filled)
            for key, value in clearbit_result.items():
                if not result.get(key) and value:
                    result[key] = value
            if not result.get('source'):
                result['source'] = clearbit_result.get('source', '')
    
    return result

