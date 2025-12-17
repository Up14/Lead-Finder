"""
LinkedIn Finder
Finds LinkedIn profiles and extracts company names from LinkedIn
Uses Apollo.io (includes LinkedIn data) or LinkedIn API if available
"""

import requests
import logging
from typing import Dict, Optional
from utils.api_credit_manager import APICreditManager

logger = logging.getLogger(__name__)

# Initialize credit manager
credit_manager = APICreditManager()


def find_linkedin_apollo(name: str, company: str, api_key: str) -> Optional[Dict]:
    """
    Find LinkedIn profile using Apollo.io API (includes LinkedIn data)
    
    Args:
        name: Person's full name
        company: Company name
        api_key: Apollo.io API key
    
    Returns:
        Dictionary with LinkedIn data and company name, or None if not found
    """
    if not credit_manager.can_make_call('apollo'):
        logger.warning("Apollo.io credits exhausted")
        return None
    
    try:
        # Split name into first and last
        name_parts = name.strip().split(' ', 1)
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        if not first_name or not company:
            return None
        
        # Apollo.io API endpoint for person search
        url = "https://api.apollo.io/v1/mixed_people/search"
        
        headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "X-Api-Key": api_key  # API key in header (correct format)
        }
        
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "organization_name": company,
            "page": 1,
            "per_page": 1
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Check for errors and handle appropriately
        if response.status_code == 403:
            # Free plan doesn't support this endpoint
            logger.warning("Apollo.io free plan doesn't support LinkedIn lookup")
            return None
        elif response.status_code != 200:
            error_detail = response.text
            logger.error(f"Apollo.io API error {response.status_code}: {error_detail}")
            return None
        
        data = response.json()
        
        # Record API call only on success
        credit_manager.record_api_call('apollo')
        
        # Extract LinkedIn data from response
        people = data.get('people', [])
        if people and len(people) > 0:
            person = people[0]
            
            linkedin_url = person.get('linkedin_url', '')
            linkedin_title = person.get('title', '')
            
            # Get current company from Apollo response
            # Apollo provides organization data which is the most reliable source
            organization = person.get('organization', {})
            company_name = ''
            if organization and isinstance(organization, dict):
                company_name = organization.get('name', '')
            
            # Build result dictionary
            result = {
                'linkedin_url': linkedin_url,
                'linkedin_title': linkedin_title,
                'company_name_from_linkedin': company_name,
                'source': 'Apollo API'
            }
            
            # Return result if we have at least LinkedIn URL or company name
            if linkedin_url or company_name:
                return result
        
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
        logger.error(f"Error finding LinkedIn via Apollo: {e}")
        return None


def get_company_from_linkedin(name: str, company_hint: str, api_key: str) -> Optional[str]:
    """
    Get proper company name from LinkedIn/API
    
    Args:
        name: Person's full name
        company_hint: Company name hint (from PubMed)
        api_key: API key (Apollo or LinkedIn)
    
    Returns:
        Proper company name or None if not found
    """
    # Use Apollo to get company name
    result = find_linkedin_apollo(name, company_hint, api_key)
    
    if result and result.get('company_name_from_linkedin'):
        return result['company_name_from_linkedin']
    
    return None


def find_linkedin(name: str, company: str, apollo_key: Optional[str] = None) -> Dict:
    """
    Find LinkedIn profile and extract company name
    
    Args:
        name: Person's full name
        company: Company name (hint from PubMed)
        apollo_key: Apollo.io API key (optional)
    
    Returns:
        Dictionary with LinkedIn information and company name
    """
    result = {
        'linkedin_url': '',
        'linkedin_title': '',
        'company_name_verified': company,  # Default to original company name
        'source': ''
    }
    
    # Try Apollo
    if apollo_key:
        apollo_result = find_linkedin_apollo(name, company, apollo_key)
        if apollo_result:
            if apollo_result.get('linkedin_url'):
                result['linkedin_url'] = apollo_result['linkedin_url']
            if apollo_result.get('linkedin_title'):
                result['linkedin_title'] = apollo_result['linkedin_title']
            if apollo_result.get('company_name_from_linkedin'):
                # Use LinkedIn company name as it's more accurate
                result['company_name_verified'] = apollo_result['company_name_from_linkedin']
            result['source'] = apollo_result.get('source', 'Apollo API')
            return result
    
    return result

