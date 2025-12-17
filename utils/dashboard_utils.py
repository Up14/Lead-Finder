"""
Dashboard Utility Functions
Long-term solutions for data formatting, URL normalization, and export functionality
"""

import logging
from typing import Optional, List, Tuple
from urllib.parse import urlparse, urlunparse
import pandas as pd
from io import BytesIO

logger = logging.getLogger(__name__)


def normalize_linkedin_url(url: str) -> str:
    """
    Normalize LinkedIn URL to proper format.
    
    Args:
        url: LinkedIn URL (can be partial, full, or N/A)
    
    Returns:
        Properly formatted LinkedIn URL or 'N/A'
    """
    if not url or url == 'N/A' or not isinstance(url, str):
        return 'N/A'
    
    url = url.strip()
    
    # If already a full URL, validate and return
    if url.startswith('http://') or url.startswith('https://'):
        try:
            parsed = urlparse(url)
            if parsed.netloc and 'linkedin.com' in parsed.netloc:
                return url
            # If it's a URL but not LinkedIn, return as-is
            return url
        except Exception:
            return 'N/A'
    
    # If it's just a path or partial URL
    if url.startswith('linkedin.com') or url.startswith('www.linkedin.com'):
        return f"https://{url}"
    
    # If it starts with /, assume it's a LinkedIn path
    if url.startswith('/'):
        return f"https://www.linkedin.com{url}"
    
    # If it contains linkedin.com anywhere, try to construct proper URL
    if 'linkedin.com' in url.lower():
        if not url.startswith('http'):
            return f"https://{url}"
        return url
    
    # If none of the above, return as-is (might be a profile ID or other format)
    return url


def extract_field_value(lead: dict, field_priority: List[str], default: str = 'N/A') -> str:
    """
    Extract field value from lead dictionary using priority order.
    
    Args:
        lead: Lead dictionary
        field_priority: List of field names to try in order
        default: Default value if none found
    
    Returns:
        First available field value or default
    """
    for field in field_priority:
        value = lead.get(field)
        if value and str(value).strip() and str(value).strip() != 'N/A':
            return str(value).strip()
    
    return default


def calculate_priority_ranges(priority_levels: List[str]) -> List[Tuple[int, int]]:
    """
    Calculate score ranges for priority levels.
    
    Args:
        priority_levels: List of priority level strings (e.g., ['High (80+)', 'Medium (50-79)'])
    
    Returns:
        List of (min, max) tuples for score ranges
    """
    priority_map = {
        'High (80+)': (80, 100),
        'Medium (50-79)': (50, 79),
        'Low (<50)': (0, 49)
    }
    
    ranges = []
    for level in priority_levels:
        if level in priority_map:
            ranges.append(priority_map[level])
    
    return ranges


def filter_by_priority_range(df: pd.DataFrame, priority_ranges: List[Tuple[int, int]]) -> pd.DataFrame:
    """
    Filter DataFrame by priority score ranges.
    
    Args:
        df: DataFrame with 'probability' column
        priority_ranges: List of (min, max) score ranges
    
    Returns:
        Filtered DataFrame
    """
    if not priority_ranges:
        return df
    
    mask = df['probability'].apply(
        lambda x: any(low <= x <= high for low, high in priority_ranges)
    )
    return df[mask]


def export_to_excel(df: pd.DataFrame, sheet_name: str = 'Leads') -> Optional[BytesIO]:
    """
    Export DataFrame to Excel format.
    
    Args:
        df: DataFrame to export
        sheet_name: Name of the Excel sheet
    
    Returns:
        BytesIO object with Excel data, or None if export fails
    """
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        output.seek(0)
        return output
    except ImportError:
        logger.error("openpyxl not installed. Install with: pip install openpyxl")
        return None
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        return None


def get_hub_cities() -> List[str]:
    """
    Get list of hub cities for filtering.
    
    Returns:
        List of hub city names
    """
    return [
        'Boston', 'Cambridge', 'Bay Area', 'San Francisco', 
        'Basel', 'London', 'Oxford', 'Cambridge UK'
    ]


def extract_hub_locations(all_locations: List[str], hub_cities: Optional[List[str]] = None) -> List[str]:
    """
    Extract locations that match hub cities.
    
    Args:
        all_locations: List of all location strings
        hub_cities: Optional list of hub cities (defaults to get_hub_cities())
    
    Returns:
        Sorted list of unique hub locations
    """
    if hub_cities is None:
        hub_cities = get_hub_cities()
    
    hub_locations = set()
    
    for location in all_locations:
        if location and location != 'N/A':
            location_lower = location.lower()
            for hub in hub_cities:
                if hub.lower() in location_lower:
                    hub_locations.add(location)
                    break
    
    return sorted(hub_locations)

