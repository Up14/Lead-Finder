"""
Phone Finder
Finds business phone numbers using API services (Apollo.io)
"""

import requests
import logging
from typing import Dict, Optional
from utils.api_credit_manager import APICreditManager

logger = logging.getLogger(__name__)

# Initialize credit manager
credit_manager = APICreditManager()


def find_phone_apollo(name: str, company: str, api_key: str) -> Optional[Dict]:
    """
    Find phone number using Apollo.io API
    
    Args:
        name: Person's full name
        company: Company name
        api_key: Apollo.io API key
    
    Returns:
        Dictionary with phone and metadata, or None if not found
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
            logger.warning("Apollo.io free plan doesn't support phone lookup")
            return None
        elif response.status_code != 200:
            error_detail = response.text
            logger.error(f"Apollo.io API error {response.status_code}: {error_detail}")
            return None
        
        data = response.json()
        
        # Record API call only on success
        credit_manager.record_api_call('apollo')
        
        # Extract phone from response
        people = data.get('people', [])
        if people and len(people) > 0:
            person = people[0]
            phone = person.get('phone_numbers', [])
            
            if phone and len(phone) > 0:
                # Get first phone number
                phone_number = phone[0].get('raw_number') or phone[0].get('sanitized_number')
                
                if phone_number:
                    return {
                        'phone': phone_number,
                        'source': 'Apollo API',
                        'phone_type': phone[0].get('type', 'unknown')
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
        logger.error(f"Error finding phone via Apollo: {e}")
        return None


def find_phone(name: str, company: str, apollo_key: Optional[str] = None) -> Dict:
    """
    Find phone number using available APIs
    
    Args:
        name: Person's full name
        company: Company name
        apollo_key: Apollo.io API key (optional)
    
    Returns:
        Dictionary with phone information or empty dict if not found
    """
    result = {
        'phone': '',
        'phone_source': ''
    }
    
    # Try Apollo
    if apollo_key:
        apollo_result = find_phone_apollo(name, company, apollo_key)
        if apollo_result and apollo_result.get('phone'):
            result['phone'] = apollo_result['phone']
            result['phone_source'] = apollo_result['source']
            return result
    
    return result

