"""
Stage 4: Dashboard
Transforms ranked leads into final dashboard format with exact column structure
"""

import logging
from typing import List, Dict
from utils.dashboard_utils import (
    normalize_linkedin_url,
    extract_field_value
)

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def run_stage4(stage3_data: List[Dict]) -> List[Dict]:
    """
    Stage 4: Dashboard
    Transforms ranked leads to final dashboard format with exact columns
    
    Args:
        stage3_data: List of ranked lead dictionaries from Stage 3
    
    Returns:
        List of dashboard-formatted lead dictionaries
    """
    if not stage3_data:
        logger.warning("No Stage 3 data provided")
        return []
    
    if not isinstance(stage3_data, list):
        logger.error(f"Invalid stage3_data type: {type(stage3_data)}. Expected list.")
        return []
    
    dashboard_data = []
    failed_count = 0
    
    for idx, lead in enumerate(stage3_data):
        if not isinstance(lead, dict):
            logger.warning(f"Lead at index {idx} is not a dictionary, skipping")
            failed_count += 1
            continue
        
        try:
            # Transform to dashboard format with exact column names
            dashboard_row = _transform_to_dashboard_format(lead)
            
            # Validate required fields
            if not _validate_dashboard_row(dashboard_row):
                logger.warning(f"Invalid dashboard row for lead {lead.get('name', 'Unknown')}, skipping")
                failed_count += 1
                continue
            
            dashboard_data.append(dashboard_row)
        except KeyError as e:
            logger.error(f"Missing required field in lead {lead.get('name', 'Unknown')}: {e}")
            failed_count += 1
            continue
        except Exception as e:
            logger.error(f"Error transforming lead {lead.get('name', 'Unknown')}: {e}")
            failed_count += 1
            continue
    
    if failed_count > 0:
        logger.warning(f"Failed to transform {failed_count} out of {len(stage3_data)} leads")
    
    logger.info(f"Successfully transformed {len(dashboard_data)} leads to dashboard format")
    return dashboard_data


def _validate_dashboard_row(row: Dict) -> bool:
    """
    Validate that dashboard row has all required fields.
    
    Args:
        row: Dashboard row dictionary
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['rank', 'probability', 'name', 'title', 'company', 
                      'location', 'hq', 'email', 'linkedin', 'action']
    
    for field in required_fields:
        if field not in row:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate types
    if not isinstance(row.get('rank'), (int, float)):
        logger.error(f"Invalid rank type: {type(row.get('rank'))}")
        return False
    
    if not isinstance(row.get('probability'), (int, float)):
        logger.error(f"Invalid probability type: {type(row.get('probability'))}")
        return False
    
    return True


def _transform_to_dashboard_format(lead: Dict) -> Dict:
    """
    Transform a single lead to dashboard format with exact column structure
    
    Args:
        lead: Lead dictionary from Stage 3
    
    Returns:
        Dashboard-formatted dictionary with exact column names
    """
    # Extract fields using priority order
    title = extract_field_value(lead, ['linkedin_title', 'title'], 'N/A')
    company = extract_field_value(lead, ['company_name_verified', 'company'], 'N/A')
    location = extract_field_value(lead, ['person_location', 'location'], 'N/A')
    hq = extract_field_value(lead, ['company_hq'], 'N/A')
    email = extract_field_value(lead, ['email'], 'N/A')
    
    # Get and normalize LinkedIn URL
    linkedin_raw = lead.get('linkedin_url', '') or ''
    linkedin = normalize_linkedin_url(linkedin_raw)
    
    # Get rank and probability with defaults
    rank = lead.get('rank', 0)
    probability = lead.get('propensity_score', 0)
    name = extract_field_value(lead, ['name'], 'N/A')
    
    # Build dashboard row with exact column names
    dashboard_row = {
        'rank': rank,
        'probability': probability,
        'name': name,
        'title': title,
        'company': company,
        'location': location,
        'hq': hq,
        'email': email,
        'linkedin': linkedin,
        'action': 'Contact'  # Default action
    }
    
    return dashboard_row

