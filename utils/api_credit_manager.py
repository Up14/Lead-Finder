"""
API Credit Manager
Tracks API usage and remaining credits to prevent waste during testing
"""

import json
import os
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

CREDIT_FILE = "data/cache/api_credits.json"


class APICreditManager:
    """
    Manages API credit tracking and quota enforcement
    """
    
    def __init__(self, credit_file: str = CREDIT_FILE):
        self.credit_file = credit_file
        self.credit_dir = os.path.dirname(credit_file)
        self._ensure_credit_dir()
        self.credits = self._load_credits()
    
    def _ensure_credit_dir(self):
        """Ensure credit directory exists"""
        os.makedirs(self.credit_dir, exist_ok=True)
    
    def _load_credits(self) -> Dict:
        """Load credit data from file"""
        if not os.path.exists(self.credit_file):
            return {}
        
        try:
            with open(self.credit_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading credit data: {e}")
            return {}
    
    def _save_credits(self):
        """Save credit data to file"""
        try:
            with open(self.credit_file, 'w', encoding='utf-8') as f:
                json.dump(self.credits, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving credit data: {e}")
    
    def initialize_api(self, api_name: str, quota_limit: int = 100):
        """
        Initialize API credit tracking
        
        Args:
            api_name: Name of API (e.g., 'apollo', 'hunter')
            quota_limit: Total quota/credits available
        """
        if api_name not in self.credits:
            self.credits[api_name] = {
                'calls_made': 0,
                'calls_remaining': quota_limit,
                'quota_limit': quota_limit,
                'last_updated': datetime.now().isoformat()
            }
            self._save_credits()
    
    def can_make_call(self, api_name: str) -> bool:
        """
        Check if API call can be made (credits available)
        
        Args:
            api_name: Name of API
        
        Returns:
            True if credits available, False otherwise
        """
        if api_name not in self.credits:
            return True  # Not initialized, assume available
        
        remaining = self.credits[api_name].get('calls_remaining', 0)
        return remaining > 0
    
    def record_api_call(self, api_name: str, calls_used: int = 1):
        """
        Record API call usage
        
        Args:
            api_name: Name of API
            calls_used: Number of calls/credits used (default: 1)
        
        Returns:
            True if recorded successfully, False if credits exhausted
        """
        if api_name not in self.credits:
            self.initialize_api(api_name)
        
        current_remaining = self.credits[api_name].get('calls_remaining', 0)
        
        if current_remaining < calls_used:
            logger.warning(f"Not enough credits for {api_name}. Remaining: {current_remaining}, Needed: {calls_used}")
            return False
        
        self.credits[api_name]['calls_made'] = self.credits[api_name].get('calls_made', 0) + calls_used
        self.credits[api_name]['calls_remaining'] = current_remaining - calls_used
        self.credits[api_name]['last_updated'] = datetime.now().isoformat()
        
        self._save_credits()
        return True
    
    def get_credit_info(self, api_name: str) -> Dict:
        """
        Get credit information for an API
        
        Args:
            api_name: Name of API
        
        Returns:
            Dictionary with credit information
        """
        if api_name not in self.credits:
            return {
                'calls_made': 0,
                'calls_remaining': 0,
                'quota_limit': 0,
                'last_updated': None
            }
        
        return self.credits[api_name].copy()
    
    def get_all_credits(self) -> Dict:
        """
        Get credit information for all APIs
        
        Returns:
            Dictionary with all API credit information
        """
        return self.credits.copy()
    
    def reset_credits(self, api_name: Optional[str] = None):
        """
        Reset credits for an API or all APIs
        
        Args:
            api_name: Name of API to reset, or None to reset all
        """
        if api_name:
            if api_name in self.credits:
                quota = self.credits[api_name].get('quota_limit', 100)
                self.credits[api_name] = {
                    'calls_made': 0,
                    'calls_remaining': quota,
                    'quota_limit': quota,
                    'last_updated': datetime.now().isoformat()
                }
                self._save_credits()
        else:
            # Reset all
            for api in self.credits:
                quota = self.credits[api].get('quota_limit', 100)
                self.credits[api] = {
                    'calls_made': 0,
                    'calls_remaining': quota,
                    'quota_limit': quota,
                    'last_updated': datetime.now().isoformat()
                }
            self._save_credits()
    
    def update_quota(self, api_name: str, new_quota: int):
        """
        Update quota limit for an API
        
        Args:
            api_name: Name of API
            new_quota: New quota limit
        """
        if api_name not in self.credits:
            self.initialize_api(api_name, new_quota)
        else:
            current_remaining = self.credits[api_name].get('calls_remaining', 0)
            calls_made = self.credits[api_name].get('calls_made', 0)
            
            # Adjust remaining based on new quota
            new_remaining = new_quota - calls_made
            if new_remaining < 0:
                new_remaining = 0
            
            self.credits[api_name]['quota_limit'] = new_quota
            self.credits[api_name]['calls_remaining'] = new_remaining
            self.credits[api_name]['last_updated'] = datetime.now().isoformat()
            self._save_credits()

