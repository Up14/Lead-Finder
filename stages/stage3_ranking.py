"""
Stage 3: Ranking
Calculates Propensity to Buy scores and ranks leads
"""

import logging
from typing import List, Dict
import streamlit as st
from utils.scoring import calculate_propensity_score

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def run_stage3(stage2_data: List[Dict]) -> List[Dict]:
    """
    Stage 3: Ranking
    Calculates Propensity to Buy scores and ranks leads
    
    Args:
        stage2_data: List of enriched lead dictionaries from Stage 2
    
    Returns:
        List of ranked lead dictionaries with scores
    """
    if not stage2_data:
        st.warning("⚠️ No Stage 2 data available. Please run Stage 2 first.")
        return []
    
    st.info(f"🔄 Calculating Propensity to Buy scores for {len(stage2_data)} leads...")
    
    ranked_results = []
    progress_bar = st.progress(0)
    
    # Calculate scores for each lead
    for idx, lead in enumerate(stage2_data):
        try:
            # Calculate propensity score
            score_data = calculate_propensity_score(lead)
            
            # Add score data to lead
            ranked_lead = lead.copy()
            ranked_lead.update(score_data)
            
            ranked_results.append(ranked_lead)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error calculating score for lead {lead.get('name', 'Unknown')}: {error_msg}")
            # Add lead with zero score if calculation fails
            ranked_lead = lead.copy()
            ranked_lead.update({
                'propensity_score': 0,
                'score_breakdown': {
                    'role_fit': 0,
                    'scientific_intent': 0,
                    'company_intent': 0,
                    'technographic': 0,
                    'location': 0
                },
                'priority_level': 'Low'
            })
            ranked_results.append(ranked_lead)
        
        # Update progress
        progress_bar.progress((idx + 1) / len(stage2_data))
    
    # Sort by propensity_score (descending)
    ranked_results.sort(key=lambda x: x.get('propensity_score', 0), reverse=True)
    
    # Assign ranks (handle ties properly)
    ranked_results = _assign_ranks(ranked_results)
    
    # Show summary
    high_priority = sum(1 for r in ranked_results if r.get('priority_level') == 'High')
    medium_priority = sum(1 for r in ranked_results if r.get('priority_level') == 'Medium')
    low_priority = sum(1 for r in ranked_results if r.get('priority_level') == 'Low')
    
    avg_score = sum(r.get('propensity_score', 0) for r in ranked_results) / len(ranked_results) if ranked_results else 0
    
    st.success(f"✅ Stage 3 Complete: {len(ranked_results)} leads ranked")
    st.info(f"📊 Score Summary: High ({high_priority}), Medium ({medium_priority}), Low ({low_priority}) | Avg Score: {avg_score:.1f}")
    
    return ranked_results


def _assign_ranks(ranked_results: List[Dict]) -> List[Dict]:
    """
    Assign rank numbers to leads, handling ties properly
    
    Args:
        ranked_results: List of leads sorted by score (descending)
    
    Returns:
        List of leads with rank assigned
    """
    if not ranked_results:
        return []
    
    current_rank = 1
    current_score = None
    rank_count = 0
    
    for lead in ranked_results:
        score = lead.get('propensity_score', 0)
        
        # If score changes, update rank
        if current_score is None or score != current_score:
            # If we had ties, skip ranks appropriately
            if current_score is not None:
                current_rank += rank_count
            current_score = score
            rank_count = 1
        else:
            # Same score as previous (tie)
            rank_count += 1
        
        # Assign rank
        lead['rank'] = current_rank
    
    return ranked_results

