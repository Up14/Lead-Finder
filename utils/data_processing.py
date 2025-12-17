"""
Data processing utilities for deduplication and data cleaning
"""

from typing import List, Dict
from fuzzywuzzy import fuzz
import re


def deduplicate_leads(leads: List[Dict]) -> List[Dict]:
    """
    Deduplicate leads based on name and company using fuzzy matching
    
    Args:
        leads: List of lead dictionaries
    
    Returns:
        Deduplicated list of leads
    """
    if not leads:
        return []
    
    # Threshold for name similarity (85%)
    SIMILARITY_THRESHOLD = 85
    
    # Group leads by potential matches
    processed = []
    seen_indices = set()
    
    for i, lead1 in enumerate(leads):
        if i in seen_indices:
            continue
        
        # Start with this lead as the base
        merged_lead = lead1.copy()
        matching_indices = [i]
        
        # Look for duplicates
        for j, lead2 in enumerate(leads[i+1:], start=i+1):
            if j in seen_indices:
                continue
            
            # Check if same person
            if _is_same_person(lead1, lead2, SIMILARITY_THRESHOLD):
                matching_indices.append(j)
                seen_indices.add(j)
                
                # Merge data from lead2 into merged_lead
                merged_lead = _merge_lead_data(merged_lead, lead2)
        
        seen_indices.add(i)
        processed.append(merged_lead)
    
    return processed


def _is_same_person(lead1: Dict, lead2: Dict, threshold: int) -> bool:
    """
    Check if two leads represent the same person
    
    Args:
        lead1: First lead dictionary
        lead2: Second lead dictionary
        threshold: Similarity threshold (0-100)
    
    Returns:
        True if same person, False otherwise
    """
    name1 = str(lead1.get('name', '')).lower().strip()
    name2 = str(lead2.get('name', '')).lower().strip()
    
    company1 = str(lead1.get('company', '')).lower().strip()
    company2 = str(lead2.get('company', '')).lower().strip()
    
    # If names are empty, can't match
    if not name1 or not name2:
        return False
    
    # Check name similarity
    name_similarity = fuzz.ratio(name1, name2)
    
    # Also check token set ratio (handles name order differences)
    token_ratio = fuzz.token_set_ratio(name1, name2)
    name_match = max(name_similarity, token_ratio) >= threshold
    
    # Check company match (exact or high similarity)
    if company1 and company2:
        company_similarity = fuzz.ratio(company1, company2)
        company_match = company_similarity >= 80 or company1 == company2
    else:
        # If one company is missing, still allow match if names are very similar
        company_match = True
    
    return name_match and company_match


def _merge_lead_data(lead1: Dict, lead2: Dict) -> Dict:
    """
    Merge data from lead2 into lead1, prioritizing lead1 data
    
    Args:
        lead1: Primary lead (data to keep)
        lead2: Secondary lead (data to merge in)
    
    Returns:
        Merged lead dictionary
    """
    merged = lead1.copy()
    
    # Merge publication titles (keep all unique)
    pub1 = merged.get('publication_title', '')
    pub2 = lead2.get('publication_title', '')
    
    if pub1 and pub2 and pub1 != pub2:
        # Combine unique publications
        publications = [pub1]
        if pub2 not in publications:
            publications.append(pub2)
        merged['publication_title'] = '; '.join(publications)
    elif not pub1 and pub2:
        merged['publication_title'] = pub2
    
    # Merge email addresses (prioritize non-empty)
    email1 = merged.get('email', '')
    email2 = lead2.get('email', '')
    if not email1 and email2:
        merged['email'] = email2
    elif email1 and email2 and email1 != email2:
        # Keep both emails
        merged['email'] = f"{email1}; {email2}"
    
    # Merge locations (prioritize non-empty)
    location1 = merged.get('location', '')
    location2 = lead2.get('location', '')
    if not location1 and location2:
        merged['location'] = location2
    
    # Merge companies (prioritize non-"Unknown")
    company1 = merged.get('company', '')
    company2 = lead2.get('company', '')
    if company1 == "Unknown" and company2 and company2 != "Unknown":
        merged['company'] = company2
    
    # Merge author positions (prioritize Corresponding > First > Last > Co-Author)
    pos1 = merged.get('author_position', '')
    pos2 = lead2.get('author_position', '')
    priority = {'Corresponding Author': 4, 'First Author': 3, 'Last Author': 2, 'Co-Author': 1}
    if priority.get(pos2, 0) > priority.get(pos1, 0):
        merged['author_position'] = pos2
    
    # Merge PubMed IDs (keep all unique)
    pmid1 = merged.get('pubmed_id', '')
    pmid2 = lead2.get('pubmed_id', '')
    if pmid1 and pmid2 and pmid1 != pmid2:
        merged['pubmed_id'] = f"{pmid1}; {pmid2}"
    elif not pmid1 and pmid2:
        merged['pubmed_id'] = pmid2
    
    # Merge journals
    journal1 = merged.get('publication_journal', '')
    journal2 = lead2.get('publication_journal', '')
    if journal1 and journal2 and journal1 != journal2:
        journals = [journal1]
        if journal2 not in journals:
            journals.append(journal2)
        merged['publication_journal'] = '; '.join(journals)
    elif not journal1 and journal2:
        merged['publication_journal'] = journal2
    
    # Keep the most recent publication date
    date1 = merged.get('publication_date', '')
    date2 = lead2.get('publication_date', '')
    if date2 and (not date1 or date2 > date1):
        merged['publication_date'] = date2
    
    return merged


def extract_company_from_affiliation(affiliation: str) -> str:
    """
    Extract company/institution name from affiliation text
    
    Args:
        affiliation: Affiliation string
    
    Returns:
        Company name or "Unknown"
    """
    if not affiliation:
        return "Unknown"
    
    # Remove email if present
    affiliation = re.sub(r'\S+@\S+', '', affiliation)
    
    # Split by commas
    parts = [p.strip() for p in affiliation.split(',')]
    
    # Skip department/university keywords
    skip_keywords = ['department', 'university', 'college', 'school', 'institute', 
                     'institution', 'center', 'centre', 'laboratory', 'lab', 'faculty']
    
    for part in parts:
        part_lower = part.lower()
        # Skip if it's a department/university name
        if any(keyword in part_lower for keyword in skip_keywords):
            continue
        # Skip if it's just a location (numbers, postal codes, etc.)
        if re.match(r'^\d+', part) or len(part) < 3:
            continue
        # Return the first substantial part that's not a department
        if len(part) > 3:
            return part
    
    # If no company found, return first substantial part
    for part in parts:
        if len(part) > 5:
            return part
    
    return "Unknown"


def extract_location_from_affiliation(affiliation: str) -> str:
    """
    Extract location (city, state, country) from affiliation
    
    Args:
        affiliation: Affiliation string
    
    Returns:
        Location string or empty
    """
    if not affiliation:
        return ""
    
    # Remove email
    affiliation = re.sub(r'\S+@\S+', '', affiliation)
    
    # Split by commas - location is usually at the end
    parts = [p.strip() for p in affiliation.split(',')]
    
    # Last 1-2 parts are usually location
    if len(parts) >= 2:
        # Return last part (country) or last two parts (city, country)
        location_parts = parts[-2:] if len(parts) >= 2 else parts[-1:]
        return ', '.join(location_parts)
    
    return ""

