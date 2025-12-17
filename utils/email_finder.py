"""
Email Finder
Finds business emails using API services (Apollo.io, Hunter.io, ContactOut)
No email guessing - only API-based finding
"""

import requests
import logging
from typing import Dict, Optional
from utils.api_credit_manager import APICreditManager

logger = logging.getLogger(__name__)

# Initialize credit manager
credit_manager = APICreditManager()

# Initialize ContactOut API credits (default quota: 100, adjustable based on plan)
# ContactOut typically has rate limits of ~60 requests per minute
credit_manager.initialize_api('contactout', quota_limit=100)


def find_email_apollo(name: str, company: str, api_key: str) -> Optional[Dict]:
    """
    Find email using Apollo.io API
    
    Args:
        name: Person's full name
        company: Company name
        api_key: Apollo.io API key
    
    Returns:
        Dictionary with email and metadata, or None if not found
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
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'API endpoint not accessible on free plan')
                logger.warning(f"Apollo.io free plan limitation: {error_msg}")
                # Return None to allow fallback to other APIs
                return None
            except Exception:
                logger.warning("Apollo.io API endpoint not accessible on free plan")
                return None
        elif response.status_code != 200:
            error_detail = response.text
            logger.error(f"Apollo.io API error {response.status_code}: {error_detail}")
            return None
        
        data = response.json()
        
        # Record API call only on success
        credit_manager.record_api_call('apollo')
        
        # Extract email from response
        people = data.get('people', [])
        if people and len(people) > 0:
            person = people[0]
            email = person.get('email')
            
            if email:
                return {
                    'email': email,
                    'source': 'Apollo API',
                    'confidence': 'high',
                    'verified': person.get('email_status', 'unknown')
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
        logger.error(f"Error finding email via Apollo: {e}")
        return None


def find_email_hunter(name: str, company: str, api_key: str) -> Optional[Dict]:
    """
    Find email using Hunter.io API
    
    Args:
        name: Person's full name
        company: Company name
        api_key: Hunter.io API key
    
    Returns:
        Dictionary with email and metadata, or None if not found
    """
    if not credit_manager.can_make_call('hunter'):
        logger.warning("Hunter.io credits exhausted")
        return None
    
    try:
        # Split name into first and last
        name_parts = name.strip().split(' ', 1)
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        if not first_name or not company:
            return None
        
        # Hunter.io API endpoint
        url = "https://api.hunter.io/v2/email-finder"
        
        params = {
            "api_key": api_key,
            "first_name": first_name,
            "last_name": last_name,
            "domain": _extract_domain_from_company(company)
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Record API call
        credit_manager.record_api_call('hunter')
        
        # Extract email from response
        if data.get('data') and data['data'].get('email'):
            email_data = data['data']
            return {
                'email': email_data.get('email'),
                'source': 'Hunter API',
                'confidence': email_data.get('score', 0),
                'verified': email_data.get('sources', [])
            }
        
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Hunter.io API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error finding email via Hunter: {e}")
        return None


def find_email_contactout(linkedin_url: str, api_key: str) -> Optional[Dict]:
    """
    Find email using ContactOut API
    
    ContactOut enriches LinkedIn profiles to find contact information.
    Requires a LinkedIn profile URL (not name/company like other APIs).
    
    Args:
        linkedin_url: LinkedIn profile URL (e.g., https://linkedin.com/in/username)
        api_key: ContactOut API key
    
    Returns:
        Dictionary with email, phone, and metadata, or None if not found
    """
    if not credit_manager.can_make_call('contactout'):
        logger.warning("ContactOut credits exhausted")
        return None
    
    if not linkedin_url or not api_key:
        return None
    
    # Validate LinkedIn URL format
    if not linkedin_url.startswith('http') and 'linkedin.com' not in linkedin_url.lower():
        logger.warning(f"Invalid LinkedIn URL format for ContactOut: {linkedin_url}")
        return None
    
    try:
        # ContactOut API endpoint
        url = "https://api.contactout.com/v1/people/linkedin"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "token": api_key
        }
        
        params = {
            "profile": linkedin_url,
            "include_phone": "true"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        # Handle errors
        if response.status_code == 403:
            # Invalid API key or unauthorized
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Invalid API key or unauthorized')
                logger.warning(f"ContactOut API error 403: {error_msg}")
            except Exception:
                logger.warning("ContactOut API error 403: Invalid API key or unauthorized")
            return None
        elif response.status_code == 429:
            # Rate limit exceeded
            logger.warning("ContactOut API rate limit exceeded (60 requests/minute)")
            return None
        elif response.status_code == 404:
            # LinkedIn profile not found
            logger.debug(f"ContactOut: LinkedIn profile not found: {linkedin_url}")
            return None
        elif response.status_code != 200:
            error_detail = response.text
            logger.error(f"ContactOut API error {response.status_code}: {error_detail}")
            return None
        
        data = response.json()
        
        # Record API call only on success
        credit_manager.record_api_call('contactout')
        
        # Extract email and phone from response
        email = data.get('email') or data.get('emails', [{}])[0].get('email') if data.get('emails') else None
        phone = data.get('phone') or data.get('phones', [{}])[0].get('phone') if data.get('phones') else None
        
        if email:
            return {
                'email': email,
                'phone': phone,  # ContactOut can also return phone
                'source': 'ContactOut API',
                'confidence': 'high',
                'verified': 'verified' if data.get('email_verified') else 'unknown'
            }
        
        return None
        
    except requests.exceptions.Timeout:
        logger.error("ContactOut API timeout - request took too long")
        return None
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.text
                logger.error(f"ContactOut API error: {error_msg}. Response: {error_detail}")
            except Exception:
                logger.error(f"ContactOut API error: {error_msg}")
        else:
            logger.error(f"ContactOut API error: {error_msg}")
        return None
    except Exception as e:
        logger.error(f"Error finding email via ContactOut: {e}")
        return None


def _extract_domain_from_company(company: str) -> str:
    """
    Extract domain from company name (simple approach)
    For better results, use company enricher to get actual domain
    
    Args:
        company: Company name
    
    Returns:
        Potential domain (company.com format)
    """
    # Simple domain extraction - remove common words and format
    company_clean = company.lower().replace('inc', '').replace('llc', '').replace('ltd', '')
    company_clean = company_clean.strip().replace(' ', '').replace('.', '')
    
    # Return as potential domain (this is a fallback - better to use company API)
    return f"{company_clean}.com"


def find_email(name: str, company: str, apollo_key: Optional[str] = None, 
               hunter_key: Optional[str] = None, contactout_key: Optional[str] = None,
               linkedin_url: Optional[str] = None) -> Dict:
    """
    Find email using available APIs (Apollo → ContactOut → Hunter)
    
    Args:
        name: Person's full name
        company: Company name
        apollo_key: Apollo.io API key (optional)
        hunter_key: Hunter.io API key (optional)
        contactout_key: ContactOut API key (optional)
        linkedin_url: LinkedIn profile URL (required for ContactOut)
    
    Returns:
        Dictionary with email information or empty dict if not found
    """
    # Skip if email already exists and is valid business email
    # (This check should be done at higher level)
    
    result = {
        'email': '',
        'email_source': '',
        'email_confidence': ''
    }
    
    # Try Apollo first (most comprehensive, but free tier limited)
    if apollo_key:
        apollo_result = find_email_apollo(name, company, apollo_key)
        if apollo_result and apollo_result.get('email'):
            result['email'] = apollo_result['email']
            result['email_source'] = apollo_result['source']
            result['email_confidence'] = apollo_result.get('confidence', 'medium')
            return result
    
    # Try ContactOut second (requires LinkedIn URL, good accuracy)
    if contactout_key and linkedin_url:
        contactout_result = find_email_contactout(linkedin_url, contactout_key)
        if contactout_result and contactout_result.get('email'):
            result['email'] = contactout_result['email']
            result['email_source'] = contactout_result['source']
            result['email_confidence'] = contactout_result.get('confidence', 'high')
            # ContactOut can also return phone, store it if available
            if contactout_result.get('phone'):
                result['phone'] = contactout_result['phone']
            return result
    
    # Try Hunter as fallback (domain-based, works without LinkedIn)
    if hunter_key:
        hunter_result = find_email_hunter(name, company, hunter_key)
        if hunter_result and hunter_result.get('email'):
            result['email'] = hunter_result['email']
            result['email_source'] = hunter_result['source']
            result['email_confidence'] = 'high' if hunter_result.get('confidence', 0) > 70 else 'medium'
            return result
    
    return result

