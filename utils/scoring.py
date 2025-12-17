"""
Scoring Engine
Calculates Propensity to Buy scores (0-100) based on weighted criteria
"""

import logging
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def calculate_propensity_score(lead: Dict) -> Dict:
    """
    Calculate Propensity to Buy score (0-100) for a lead
    
    Args:
        lead: Lead dictionary from Stage 2 with all enrichment data
    
    Returns:
        Dictionary with score, breakdown, and priority level
    """
    score_breakdown = {
        'role_fit': 0,
        'scientific_intent': 0,
        'company_intent': 0,
        'technographic': 0,
        'location': 0
    }
    
    # 1. Role Fit (+30 points)
    score_breakdown['role_fit'] = _calculate_role_fit_score(lead)
    
    # 2. Scientific Intent (+40 points)
    score_breakdown['scientific_intent'] = _calculate_scientific_intent_score(lead)
    
    # 3. Company Intent (+20 points)
    score_breakdown['company_intent'] = _calculate_company_intent_score(lead)
    
    # 4. Technographic (+15 points)
    score_breakdown['technographic'] = _calculate_technographic_score(lead)
    
    # 5. Location (+10 points)
    score_breakdown['location'] = _calculate_location_score(lead)
    
    # Calculate total score (cap at 100)
    total_score = sum(score_breakdown.values())
    propensity_score = min(total_score, 100)
    
    # Determine priority level
    if propensity_score >= 80:
        priority_level = 'High'
    elif propensity_score >= 50:
        priority_level = 'Medium'
    else:
        priority_level = 'Low'
    
    return {
        'propensity_score': propensity_score,
        'score_breakdown': score_breakdown,
        'priority_level': priority_level
    }


def _calculate_role_fit_score(lead: Dict) -> int:
    """
    Calculate Role Fit score (+30 points)
    
    Checks if job title contains relevant keywords
    """
    # Role keywords to search for
    role_keywords = [
        'toxicology', 'safety', 'hepatic', '3d', 'preclinical',
        'pre-clinical', 'drug safety', 'safety assessment',
        'preclinical safety', 'toxicologist', 'safety scientist'
    ]
    
    # Get title from multiple sources (LinkedIn, PubMed, or original)
    title = ''
    if lead.get('linkedin_title'):
        title = lead.get('linkedin_title', '')
    elif lead.get('title'):
        title = lead.get('title', '')
    
    if not title:
        return 0
    
    title_lower = title.lower()
    
    # Check if any keyword matches
    if any(keyword in title_lower for keyword in role_keywords):
        return 30
    
    return 0


def _calculate_scientific_intent_score(lead: Dict) -> int:
    """
    Calculate Scientific Intent score (+40 points)
    
    Checks if published on DILI/liver toxicity in last 2 years
    """
    # Scientific keywords
    scientific_keywords = [
        'dili', 'drug-induced liver injury', 'liver toxicity',
        'hepatic', 'liver injury', 'drug-induced',
        'hepatotoxicity', 'liver damage'
    ]
    
    # Get publication title
    pub_title = lead.get('publication_title', '')
    pub_date = lead.get('publication_date', '')
    
    if not pub_title:
        return 0
    
    pub_title_lower = pub_title.lower()
    
    # Check if title contains scientific keywords
    has_scientific_keyword = any(keyword in pub_title_lower for keyword in scientific_keywords)
    
    if not has_scientific_keyword:
        return 0
    
    # Check if published in last 2 years
    if pub_date:
        try:
            # Parse date (format: YYYY-MM-DD or YYYY-MM or YYYY)
            if len(pub_date) >= 4:
                year = int(pub_date[:4])
                current_year = datetime.now().year
                
                # Check if within last 2 years
                if current_year - year <= 2:
                    return 40
        except (ValueError, TypeError):
            # If date parsing fails, still award points if keyword found
            # (publication exists, just date unclear)
            return 40
    
    # If keyword found but date unclear, still award points
    return 40


def _calculate_company_intent_score(lead: Dict) -> int:
    """
    Calculate Company Intent score (+20 points)
    
    Checks if company raised Series A/B funding
    """
    funding_stage = lead.get('company_funding_stage', '')
    
    if not funding_stage:
        return 0
    
    funding_stage_lower = funding_stage.lower()
    
    # Check for Series A or B (highest priority)
    if 'series a' in funding_stage_lower or 'series b' in funding_stage_lower:
        return 20
    
    # Series C or IPO also indicates budget (slightly lower priority)
    if 'series c' in funding_stage_lower or 'ipo' in funding_stage_lower:
        return 15
    
    return 0


def _calculate_technographic_score(lead: Dict) -> int:
    """
    Calculate Technographic score (+15 points)
    
    Checks if company uses similar technology (in-vitro models, NAMs)
    """
    # Technology keywords
    tech_keywords = [
        '3d', 'in-vitro', 'in vitro', 'organ-on-chip', 'organ on chip',
        'spheroid', 'cell culture', 'nam', 'new approach methodology',
        'organoid', 'microphysiological', 'mps'
    ]
    
    # Check company industry
    industry = lead.get('company_industry', '').lower()
    
    # Check publication title for tech keywords
    pub_title = lead.get('publication_title', '').lower()
    
    # Check if any tech keyword found
    if any(keyword in industry or keyword in pub_title for keyword in tech_keywords):
        return 15
    
    return 0


def _calculate_location_score(lead: Dict) -> int:
    """
    Calculate Location score (+10 points)
    
    Checks if located in hub cities
    """
    # Hub cities mapping
    hubs = {
        'boston/cambridge': ['boston', 'cambridge', 'cambridge, ma', 'boston, ma'],
        'bay area': [
            'san francisco', 'palo alto', 'south san francisco',
            'fremont', 'bay area', 'menlo park', 'san jose',
            'mountain view', 'redwood city'
        ],
        'basel': ['basel', 'switzerland'],
        'uk golden triangle': [
            'london', 'oxford', 'cambridge', 'cambridgeshire',
            'london, uk', 'oxford, uk', 'cambridge, uk'
        ]
    }
    
    # Get location from person_location or company_hq
    location = ''
    if lead.get('person_location'):
        location = lead.get('person_location', '')
    elif lead.get('company_hq'):
        location = lead.get('company_hq', '')
    
    if not location:
        return 0
    
    location_lower = location.lower()
    
    # Check if location matches any hub city
    for hub_name, cities in hubs.items():
        if any(city in location_lower for city in cities):
            return 10
    
    return 0

