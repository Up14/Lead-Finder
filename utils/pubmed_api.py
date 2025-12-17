"""
PubMed API Wrapper using NCBI E-utilities
Searches PubMed and extracts author information from papers
Long-term solution with proper XML handling and error management
"""

import requests
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import re
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class PubMedParser:
    """
    Robust PubMed XML parser that handles various XML structures
    without relying on XPath or multiple fallback methods
    """
    
    @staticmethod
    def find_element_by_tag(root: ET.Element, tag_name: str, namespace: str = None) -> Optional[ET.Element]:
        """
        Find element by tag name, handling namespaces properly
        
        Args:
            root: Root element to search from
            tag_name: Tag name to find (without namespace)
            namespace: Optional namespace prefix
        
        Returns:
            Found element or None
        """
        # Handle namespaced tags
        if namespace:
            full_tag = f"{{{namespace}}}{tag_name}" if namespace.startswith('{') else f"{namespace}:{tag_name}"
        else:
            full_tag = tag_name
        
        # Try exact match first
        result = root.find(full_tag)
        if result is not None:
            return result
        
        # Try finding by local name (handles namespace variations)
        for elem in root.iter():
            local_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if local_name == tag_name:
                return elem
        
        return None
    
    @staticmethod
    def find_all_elements_by_tag(root: ET.Element, tag_name: str) -> List[ET.Element]:
        """
        Find all elements by tag name, handling namespaces
        
        Args:
            root: Root element to search from
            tag_name: Tag name to find
        
        Returns:
            List of found elements
        """
        results = []
        for elem in root.iter():
            local_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if local_name == tag_name:
                results.append(elem)
        return results
    
    @staticmethod
    def get_text_content(elem: Optional[ET.Element]) -> str:
        """
        Safely extract text content from element
        
        Args:
            elem: XML element
        
        Returns:
            Text content or empty string
        """
        if elem is not None and elem.text:
            return elem.text.strip()
        return ""
    
    @staticmethod
    def extract_author_name(author: ET.Element) -> Optional[Tuple[str, str, str]]:
        """
        Extract author name components from Author element
        
        Args:
            author: Author XML element
        
        Returns:
            Tuple of (first_name, last_name, initials) or None if invalid
        """
        last_name = ""
        first_name = ""
        initials = ""
        
        for child in author:
            local_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            if local_tag == 'LastName':
                last_name = PubMedParser.get_text_content(child)
            elif local_tag == 'FirstName':
                first_name = PubMedParser.get_text_content(child)
            elif local_tag == 'Initials':
                initials = PubMedParser.get_text_content(child)
        
        if not last_name:
            return None
        
        return (first_name, last_name, initials)
    
    @staticmethod
    def extract_affiliation(author: ET.Element) -> str:
        """
        Extract affiliation text from Author element
        
        Args:
            author: Author XML element
        
        Returns:
            Affiliation text or empty string
        """
        # Check for direct Affiliation child
        for child in author:
            local_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            if local_tag == 'Affiliation':
                text = PubMedParser.get_text_content(child)
                if text:
                    return text
            
            # Check for AffiliationInfo -> Affiliation
            elif local_tag == 'AffiliationInfo':
                for subchild in child:
                    sub_tag = subchild.tag.split('}')[-1] if '}' in subchild.tag else subchild.tag
                    if sub_tag == 'Affiliation':
                        text = PubMedParser.get_text_content(subchild)
                        if text:
                            return text
        
        return ""
    
    @staticmethod
    def is_corresponding_author(author: ET.Element, author_index: int, total_authors: int, 
                                known_corresponding: str = "") -> bool:
        """
        Determine if author is corresponding author using proper detection methods
        
        Args:
            author: Author XML element
            author_index: Index of author (0-based)
            total_authors: Total number of authors
            known_corresponding: Known corresponding author name (if available)
        
        Returns:
            True if corresponding author, False otherwise
        """
        # Method 1: Explicit Corresp attribute (most reliable)
        if author.get('Corresp') == 'Y' or author.get('corresp') == 'Y':
            return True
        
        # Method 2: Match known corresponding author name
        if known_corresponding:
            name_data = PubMedParser.extract_author_name(author)
            if name_data:
                first_name, last_name, _ = name_data
                full_name = f"{first_name} {last_name}".strip().lower()
                if full_name == known_corresponding.lower():
                    return True
        
        # Method 3: Check for email in affiliation (strong indicator)
        affiliation = PubMedParser.extract_affiliation(author)
        if affiliation and '@' in affiliation:
            return True
        
        # Method 4: Last author with detailed affiliation (common PI pattern)
        if author_index == total_authors - 1 and affiliation and len(affiliation) > 50:
            return True
        
        return False


def search_pubmed(keyword: str, max_results: int = 50, years_back: int = 2) -> List[Dict]:
    """
    Search PubMed for papers matching keyword and extract Corresponding/First Authors
    
    Args:
        keyword: Search term (e.g., "Drug-Induced Liver Injury")
        max_results: Maximum number of papers to fetch (default: 50)
        years_back: Number of years to look back (default: 2)
    
    Returns:
        List of dictionaries containing author and paper information
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    # Calculate date filter (last N years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years_back * 365)
    date_filter = f"{start_date.strftime('%Y/%m/%d')}:{end_date.strftime('%Y/%m/%d')}[PDAT]"
    
    # Step 1: Search for papers
    search_url = f"{base_url}esearch.fcgi"
    search_params = {
        'db': 'pubmed',
        'term': f'{keyword}[Title/Abstract] AND {date_filter}',
        'retmax': max_results,
        'retmode': 'json',
        'email': 'upanshujain14@gmail.com'
    }
    
    try:
        # Rate limiting: 3 requests/second
        time.sleep(0.35)
        
        search_response = requests.get(search_url, params=search_params, timeout=30)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        pmids = search_data.get('esearchresult', {}).get('idlist', [])
        
        if not pmids:
            logger.info(f"No results found for keyword: {keyword}")
            return []
        
        # Step 2: Fetch full paper details
        fetch_url = f"{base_url}efetch.fcgi"
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml'
        }
        
        time.sleep(0.35)
        
        fetch_response = requests.get(fetch_url, params=fetch_params, timeout=30)
        fetch_response.raise_for_status()
        
        # Parse XML
        try:
            root = ET.fromstring(fetch_response.content)
        except ET.ParseError as e:
            logger.error(f"XML parsing error for keyword {keyword}: {e}")
            return []
        
        # Extract data from each paper
        results = []
        articles = PubMedParser.find_all_elements_by_tag(root, 'PubmedArticle')
        
        for article in articles:
            try:
                paper_data = _parse_paper(article)
                if paper_data:
                    results.extend(paper_data)
            except Exception as e:
                logger.warning(f"Error parsing article: {e}")
                continue  # Continue with next article instead of failing completely
        
        return results
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching data from PubMed for '{keyword}': {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in PubMed search for '{keyword}': {e}")
        return []


def _parse_paper(article: ET.Element) -> List[Dict]:
    """
    Parse a single PubMed article and extract Corresponding/First Authors
    
    Args:
        article: XML element representing a PubmedArticle
    
    Returns:
        List of author dictionaries from this paper
    """
    authors_data = []
    
    try:
        # Find MedlineCitation
        medline_citation = PubMedParser.find_element_by_tag(article, 'MedlineCitation')
        if medline_citation is None:
            return []
        
        # Extract paper metadata
        pubmed_id = ""
        pmid_elem = PubMedParser.find_element_by_tag(medline_citation, 'PMID')
        if pmid_elem is not None:
            pubmed_id = PubMedParser.get_text_content(pmid_elem)
        
        # Article title
        paper_title = ""
        article_elem = PubMedParser.find_element_by_tag(medline_citation, 'Article')
        if article_elem is not None:
            title_elem = PubMedParser.find_element_by_tag(article_elem, 'ArticleTitle')
            if title_elem is not None:
                paper_title = PubMedParser.get_text_content(title_elem)
        
        # Journal
        journal = ""
        if article_elem is not None:
            journal_elem = PubMedParser.find_element_by_tag(article_elem, 'Journal')
            if journal_elem is not None:
                title_elem = PubMedParser.find_element_by_tag(journal_elem, 'Title')
                if title_elem is not None:
                    journal = PubMedParser.get_text_content(title_elem)
        
        # Publication date
        pub_date = ""
        if article_elem is not None:
            pub_date_elem = PubMedParser.find_element_by_tag(article_elem, 'PubDate')
            if pub_date_elem is not None:
                pub_date = _extract_date(pub_date_elem)
        
        # Find AuthorList
        author_list = None
        if article_elem is not None:
            author_list = PubMedParser.find_element_by_tag(article_elem, 'AuthorList')
        
        if author_list is None:
            return []
        
        # Find known corresponding author (if marked in XML)
        corresponding_author = _find_corresponding_author(article)
        
        # Extract all Author elements
        authors = PubMedParser.find_all_elements_by_tag(author_list, 'Author')
        total_authors = len(authors)
        
        # Process only First Author and Corresponding Authors
        for idx, author in enumerate(authors):
            is_first_author = (idx == 0)
            is_last_author = (idx == total_authors - 1)
            has_corresp_attr = (author.get('Corresp') == 'Y' or author.get('corresp') == 'Y')
            
            # Only process First Author or potential Corresponding Authors
            if not (is_first_author or has_corresp_attr or is_last_author):
                continue
            
            author_info = _parse_author(author, idx, total_authors, corresponding_author)
            
            if author_info:
                # Only add if it's First Author or Corresponding Author
                author_position = author_info.get('author_position', '')
                if author_position in ['First Author', 'Corresponding Author']:
                    author_info.update({
                        'publication_title': paper_title,
                        'publication_date': pub_date,
                        'publication_journal': journal,
                        'pubmed_id': pubmed_id
                    })
                    authors_data.append(author_info)
        
        return authors_data
        
    except Exception as e:
        logger.warning(f"Error parsing paper: {e}")
        return []


def _parse_author(author: ET.Element, index: int, total: int, corresponding: str) -> Optional[Dict]:
    """
    Parse a single author element using robust parsing methods
    
    Args:
        author: XML element representing an Author
        index: Author position (0-based)
        total: Total number of authors
        corresponding: Name of corresponding author if known
    
    Returns:
        Dictionary with author information or None if invalid
    """
    try:
        # Extract name using proper parser
        name_data = PubMedParser.extract_author_name(author)
        if not name_data:
            return None
        
        first_name, last_name, initials = name_data
        
        # Construct full name
        if first_name and last_name:
            full_name = f"{first_name} {last_name}"
        elif last_name and initials:
            full_name = f"{initials} {last_name}"
        elif last_name:
            full_name = last_name
        else:
            return None
        
        # Extract affiliation using proper parser
        affiliation_text = PubMedParser.extract_affiliation(author)
        
        # Extract company and location from affiliation
        company = _extract_company_from_affiliation(affiliation_text)
        location = _extract_location_from_affiliation(affiliation_text)
        
        # Extract email from affiliation
        email = _extract_email_from_affiliation(affiliation_text)
        
        # Determine author position using proper detection
        is_corresponding = PubMedParser.is_corresponding_author(
            author, index, total, corresponding
        )
        
        if is_corresponding:
            author_position = "Corresponding Author"
        elif index == 0:
            author_position = "First Author"
        elif index == total - 1:
            author_position = "Last Author"
        else:
            author_position = "Co-Author"
        
        return {
            'name': full_name.strip(),
            'title': "",
            'company': company,
            'location': location,
            'email': email,
            'linkedin_url': "",
            'source': 'PubMed',
            'author_position': author_position,
            'affiliation': affiliation_text
        }
        
    except Exception as e:
        logger.debug(f"Error parsing author at index {index}: {e}")
        return None


def _find_corresponding_author(article: ET.Element) -> str:
    """
    Identify corresponding author from article metadata using proper methods
    
    Args:
        article: XML element representing a PubmedArticle
    
    Returns:
        Name of corresponding author or empty string
    """
    try:
        # Find AuthorList
        author_list = None
        for elem in article.iter():
            local_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if local_tag == 'AuthorList':
                author_list = elem
                break
        
        if author_list is None:
            return ""
        
        # Find author with Corresp attribute
        for author in author_list:
            if 'Author' not in (author.tag.split('}')[-1] if '}' in author.tag else author.tag):
                continue
            
            if author.get('Corresp') == 'Y' or author.get('corresp') == 'Y':
                name_data = PubMedParser.extract_author_name(author)
                if name_data:
                    first_name, last_name, _ = name_data
                    if first_name and last_name:
                        return f"{first_name} {last_name}"
                    elif last_name:
                        return last_name
        
        return ""
    except Exception as e:
        logger.debug(f"Error finding corresponding author: {e}")
        return ""


def _extract_date(pub_date_elem: ET.Element) -> str:
    """
    Extract publication date from XML element
    
    Args:
        pub_date_elem: XML element containing date information
    
    Returns:
        Date string in YYYY-MM-DD format or YYYY-MM or YYYY
    """
    if pub_date_elem is None:
        return ""
    
    try:
        year_elem = PubMedParser.find_element_by_tag(pub_date_elem, 'Year')
        month_elem = PubMedParser.find_element_by_tag(pub_date_elem, 'Month')
        day_elem = PubMedParser.find_element_by_tag(pub_date_elem, 'Day')
        
        year = PubMedParser.get_text_content(year_elem)
        month = PubMedParser.get_text_content(month_elem)
        day = PubMedParser.get_text_content(day_elem)
        
        # Normalize month to number
        if month and not month.isdigit():
            month_map = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            month = month_map.get(month.lower()[:3], month)
        
        if year and month and day:
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        elif year and month:
            return f"{year}-{month.zfill(2)}"
        elif year:
            return year
        
        return ""
    except Exception:
        return ""


def _extract_company_from_affiliation(affiliation: str) -> str:
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


def _extract_location_from_affiliation(affiliation: str) -> str:
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


def _extract_email_from_affiliation(affiliation: str) -> str:
    """
    Extract email address from affiliation text
    
    Args:
        affiliation: Affiliation string
    
    Returns:
        Email address or empty string
    """
    if not affiliation:
        return ""
    
    # Pattern for email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, affiliation)
    
    if matches:
        return matches[0]  # Return first email found
    
    return ""
