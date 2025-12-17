"""
Lead Finder: 3D In-Vitro Models for Toxicology
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
from stages.stage1_identification import run_stage1

# Page configuration
st.set_page_config(
    page_title="Lead Finder - 3D In-Vitro Models",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'stage1_data' not in st.session_state:
    st.session_state.stage1_data = None
if 'stage2_data' not in st.session_state:
    st.session_state.stage2_data = None
if 'stage3_data' not in st.session_state:
    st.session_state.stage3_data = None
if 'stage4_data' not in st.session_state:
    st.session_state.stage4_data = None

# Title and description
st.title("🔬 Lead Finder: 3D In-Vitro Models for Toxicology")
st.markdown("**Identify, Enrich, Rank, and Visualize High-Probability Leads**")
st.markdown("---")

# Sidebar for input criteria
with st.sidebar:
    st.header("⚙️ Search Criteria")
    
    # Job title keywords (for future use with LinkedIn)
    role_keywords = st.text_input(
        "Target Roles (comma-separated)",
        value="Director of Toxicology, Head of Preclinical Safety, VP Toxicology",
        help="Job titles to search for (currently for reference, will be used in future stages)",
        key="sidebar_role_keywords"
    )
    
    # Company keywords (optional)
    company_keywords = st.text_input(
        "Company Keywords (optional)",
        value="",
        help="Filter by specific companies (leave blank for all companies)",
        key="sidebar_company_keywords"
    )
    
    # Location preferences
    location_hubs = st.multiselect(
        "Preferred Hub Locations",
        options=["Boston/Cambridge", "Bay Area", "Basel", "UK Golden Triangle", "Any"],
        default=["Any"],
        help="Preferred locations (currently for reference, will be used in future stages)"
    )
    
    # Scientific keywords
    scientific_keywords = st.text_input(
        "Scientific Keywords (comma-separated)",
        value="Drug-Induced Liver Injury, 3D cell culture, Organ-on-chip, Hepatic spheroids, Investigative Toxicology",
        help="Keywords to search in PubMed papers (Title/Abstract)",
        key="sidebar_scientific_keywords"
    )
    
    # Results per keyword
    results_per_keyword = st.number_input(
        "Results per Keyword",
        min_value=10,
        max_value=200,
        value=50,
        step=10,
        help="Maximum number of papers to fetch per keyword"
    )
    
    # Years back
    years_back = st.number_input(
        "Years Back",
        min_value=1,
        max_value=5,
        value=2,
        step=1,
        help="Number of years to look back for publications"
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ About Stage 1")
    st.info(
        "Stage 1 searches PubMed for papers matching your scientific keywords "
        "and extracts Corresponding/First Authors. Results are cached to avoid repeated API calls."
    )
    
    st.markdown("---")
    st.markdown("### 📧 Stage 2: API Configuration")
    
    # Important notice about Apollo.io free plan
    st.info("ℹ️ **Note**: Apollo.io free plan has limited endpoints. For full functionality, consider upgrading or using alternative APIs like Hunter.io for email finding.")
    
    # API Keys (using Streamlit secrets or user input)
    st.markdown("#### API Keys")
    apollo_key = st.text_input(
        "Apollo.io API Key",
        value="",
        type="password",
        help="Enter your Apollo.io API key. Note: Free plan has limited access to search endpoints.",
        key="sidebar_apollo_key"
    )
    
    hunter_key = st.text_input(
        "Hunter.io API Key (optional)",
        value="",
        type="password",
        help="Enter your Hunter.io API key (optional, fallback for email)",
        key="sidebar_hunter_key"
    )
    
    clearbit_key = st.text_input(
        "Clearbit API Key (optional)",
        value="",
        type="password",
        help="Enter your Clearbit API key (optional, for company data)",
        key="sidebar_clearbit_key"
    )
    
    contactout_key = st.text_input(
        "ContactOut API Key (optional)",
        value="",
        type="password",
        help="Enter your ContactOut API key (optional, requires LinkedIn URL for email/phone finding)",
        key="sidebar_contactout_key"
    )
    
    # Leads to enrich
    st.markdown("#### Enrichment Settings")
    leads_to_enrich = st.number_input(
        "Leads to Enrich",
        min_value=1,
        max_value=100,
        value=5,
        step=1,
        help="Number of leads to enrich (default: 5 to conserve API credits)"
    )
    
    enrichment_priority = st.radio(
        "Enrichment Priority",
        options=['first_n', 'corresponding_first'],
        index=0,
        format_func=lambda x: 'First N Leads' if x == 'first_n' else 'Corresponding Authors First',
        help="Which leads to prioritize for enrichment"
    )
    
    # API Credit Display
    st.markdown("#### API Credits")
    from stages.stage2_enrichment import get_api_credit_info
    credit_info = get_api_credit_info()
    
    if credit_info:
        for api_name, credits in credit_info.items():
            remaining = credits.get('calls_remaining', 0)
            total = credits.get('quota_limit', 0)
            used = credits.get('calls_made', 0)
            
            if total > 0:
                percentage = (remaining / total) * 100
                color = "🟢" if percentage > 50 else "🟡" if percentage > 20 else "🔴"
                st.caption(f"{color} {api_name.capitalize()}: {remaining}/{total} remaining ({used} used)")
    else:
        st.info("ℹ️ No API credits tracked yet")
    
    st.markdown("---")
    st.markdown("### 🗑️ Cache Management")
    
    # Get cache information
    from stages.stage1_identification import get_cache_info, clear_cache
    cache_info = get_cache_info()
    
    if cache_info['exists']:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Cache Size", f"{cache_info['file_size_mb']:.2f} MB")
        with col2:
            st.metric("Cached Queries", cache_info['total_queries'])
        
        st.info(f"📅 Cache expires after {cache_info['expiry_days']} days | "
                f"Max size: {cache_info['max_size_mb']} MB | "
                f"Max entries: {cache_info['max_entries']}")
        
        if cache_info.get('last_cleanup'):
            st.caption(f"Last cleanup: {cache_info['last_cleanup']}")
        
        if st.button("🗑️ Clear All Cache", use_container_width=True, type="secondary"):
            if clear_cache():
                st.success("✅ Cache cleared successfully!")
                st.rerun()
            else:
                st.error("❌ Error clearing cache. Please try again.")
    else:
        st.info("ℹ️ No cache file found")

# Main content area
st.header("📊 Pipeline Stages")

# Stage 1: Identification
st.subheader("Stage 1: Identification 🔍")
col1, col2 = st.columns([1, 4])

with col1:
    stage1_button = st.button("▶️ Run Stage 1", type="primary", use_container_width=True)

with col2:
    if st.session_state.stage1_data is not None:
        st.success(f"✅ Stage 1 Complete: {len(st.session_state.stage1_data)} leads identified")
    else:
        st.info("ℹ️ Click the button to start Stage 1")

if stage1_button:
    # Parse input criteria
    if not scientific_keywords:
        st.error("❌ Please enter scientific keywords in the sidebar")
    else:
        criteria = {
            'role_keywords': [r.strip() for r in role_keywords.split(',')] if role_keywords else [],
            'company_keywords': company_keywords.strip(),
            'location_hubs': location_hubs,
            'scientific_keywords': [s.strip() for s in scientific_keywords.split(',') if s.strip()],
            'results_per_keyword': int(results_per_keyword),
            'years_back': int(years_back)
        }
        
        if not criteria['scientific_keywords']:
            st.error("❌ Please enter at least one scientific keyword")
        else:
            try:
                stage1_result = run_stage1(criteria)
                st.session_state.stage1_data = stage1_result
                
                if stage1_result:
                    st.success(f"✅ Stage 1 Complete: {len(stage1_result)} leads identified")
                else:
                    st.warning("⚠️ Stage 1 completed but no leads were found")
            except Exception as e:
                st.error(f"❌ Error in Stage 1: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# Display Stage 1 results
if st.session_state.stage1_data is not None and len(st.session_state.stage1_data) > 0:
    with st.expander("📋 View Stage 1 Results", expanded=True):
        df_stage1 = pd.DataFrame(st.session_state.stage1_data)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Leads", len(df_stage1))
        with col2:
            unique_companies = df_stage1['company'].nunique()
            st.metric("Unique Companies", unique_companies)
        with col3:
            with_email = len(df_stage1[df_stage1['email'].notna() & (df_stage1['email'] != '')])
            st.metric("Leads with Email", with_email)
        with col4:
            corresponding_authors = len(df_stage1[df_stage1['author_position'] == 'Corresponding Author'])
            st.metric("Corresponding Authors", corresponding_authors)
        
        # Source breakdown
        st.markdown("### 📊 Source Breakdown")
        source_counts = df_stage1['source'].value_counts()
        st.bar_chart(source_counts)
        
        # Data table
        st.markdown("### 📋 Lead Details")
        
        # Column selection
        default_cols = ['name', 'title', 'company', 'location', 'email', 'author_position', 
                       'publication_title', 'publication_date', 'publication_journal']
        available_cols = df_stage1.columns.tolist()
        selected_cols = st.multiselect(
            "Select columns to display",
            options=available_cols,
            default=default_cols
        )
        
        if selected_cols:
            display_df = df_stage1[selected_cols]
        else:
            display_df = df_stage1
        
        # Search/filter functionality
        search_term = st.text_input(
            "🔍 Search in results (name, company, etc.)", 
            "",
            key="stage1_search_term"
        )
        if search_term:
            mask = display_df.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            display_df = display_df[mask]
            st.info(f"Showing {len(display_df)} results matching '{search_term}'")
        
        # Display table
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Download button
        csv_data = df_stage1.to_csv(index=False)
        st.download_button(
            label="📥 Download Stage 1 Data (CSV)",
            data=csv_data,
            file_name="stage1_identification.csv",
            mime="text/csv",
            use_container_width=True
        )

# Divider
st.divider()

# Stage 2: Enrichment
st.subheader("Stage 2: Enrichment 📧")
col1, col2 = st.columns([1, 4])

with col1:
    stage2_button = st.button("▶️ Run Stage 2", type="primary", use_container_width=True,
                              disabled=st.session_state.stage1_data is None)

with col2:
    if st.session_state.stage1_data is None:
        st.warning("⚠️ Please complete Stage 1 first")
    elif st.session_state.stage2_data is not None:
        st.success(f"✅ Stage 2 Complete: {len(st.session_state.stage2_data)} leads enriched")
    else:
        st.info("ℹ️ Click the button to start enrichment")

if stage2_button and st.session_state.stage1_data is not None:
    # Get API keys and settings from sidebar
    # Store in session state for access across reruns
    if 'apollo_key' not in st.session_state:
        st.session_state['apollo_key'] = ''
    if 'hunter_key' not in st.session_state:
        st.session_state['hunter_key'] = ''
    if 'clearbit_key' not in st.session_state:
        st.session_state['clearbit_key'] = ''
    if 'leads_to_enrich' not in st.session_state:
        st.session_state['leads_to_enrich'] = 5
    if 'enrichment_priority' not in st.session_state:
        st.session_state['enrichment_priority'] = 'first_n'
    
    # Update from sidebar inputs (these are accessible)
    api_keys = {
        'apollo': apollo_key,
        'hunter': hunter_key,
        'clearbit': clearbit_key,
        'contactout': contactout_key
    }
    
    if not any(api_keys.values()):
        st.error("❌ Please enter at least one API key in the sidebar (Apollo.io recommended)")
    else:
        try:
            from stages.stage2_enrichment import run_stage2
            stage2_result = run_stage2(
                stage1_data=st.session_state.stage1_data,
                leads_to_enrich=leads_to_enrich,
                api_keys=api_keys,
                priority=enrichment_priority
            )
            st.session_state.stage2_data = stage2_result
            
            if stage2_result:
                st.success(f"✅ Stage 2 Complete: {len(stage2_result)} leads enriched")
        except Exception as e:
            st.error(f"❌ Error in Stage 2: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Display Stage 2 results
if st.session_state.stage2_data is not None and len(st.session_state.stage2_data) > 0:
    with st.expander("📋 View Stage 2 Results", expanded=False):
        import pandas as pd
        df_stage2 = pd.DataFrame(st.session_state.stage2_data)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Enriched", len(df_stage2))
        with col2:
            success_count = len(df_stage2[df_stage2['enrichment_status'] == 'success'])
            st.metric("Success", success_count)
        with col3:
            with_email = len(df_stage2[df_stage2['email'].notna() & (df_stage2['email'] != '')])
            st.metric("With Email", with_email)
        with col4:
            with_linkedin = len(df_stage2[df_stage2['linkedin_url'].notna() & (df_stage2['linkedin_url'] != '')])
            st.metric("With LinkedIn", with_linkedin)
        
        # Data table
        st.markdown("### 📋 Enriched Lead Details")
        st.dataframe(df_stage2, use_container_width=True, height=400)
        
        # Download button
        csv_data = df_stage2.to_csv(index=False)
        st.download_button(
            label="📥 Download Stage 2 Data (CSV)",
            data=csv_data,
            file_name="stage2_enrichment.csv",
            mime="text/csv",
            use_container_width=True
        )

# Divider
st.divider()

# Stage 3: Ranking
st.subheader("Stage 3: Ranking 🎯")
col1, col2 = st.columns([1, 4])

with col1:
    stage3_button = st.button("▶️ Run Stage 3", type="primary", use_container_width=True,
                              disabled=st.session_state.stage2_data is None)

with col2:
    if st.session_state.stage2_data is None:
        st.warning("⚠️ Please complete Stage 2 first")
    elif st.session_state.stage3_data is not None:
        st.success(f"✅ Stage 3 Complete: {len(st.session_state.stage3_data)} leads ranked")
    else:
        st.info("ℹ️ Click the button to calculate Propensity to Buy scores")

if stage3_button and st.session_state.stage2_data is not None:
    try:
        from stages.stage3_ranking import run_stage3
        stage3_result = run_stage3(st.session_state.stage2_data)
        st.session_state.stage3_data = stage3_result
        
        if stage3_result:
            st.success(f"✅ Stage 3 Complete: {len(stage3_result)} leads ranked")
    except Exception as e:
        st.error(f"❌ Error in Stage 3: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

# Display Stage 3 results
if st.session_state.stage3_data is not None and len(st.session_state.stage3_data) > 0:
    with st.expander("📋 View Stage 3 Results", expanded=True):
        import pandas as pd
        df_stage3 = pd.DataFrame(st.session_state.stage3_data)
        
        # Summary statistics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Ranked", len(df_stage3))
        with col2:
            high_priority = len(df_stage3[df_stage3['priority_level'] == 'High'])
            st.metric("High Priority (80+)", high_priority)
        with col3:
            medium_priority = len(df_stage3[df_stage3['priority_level'] == 'Medium'])
            st.metric("Medium Priority (50-79)", medium_priority)
        with col4:
            low_priority = len(df_stage3[df_stage3['priority_level'] == 'Low'])
            st.metric("Low Priority (<50)", low_priority)
        with col5:
            avg_score = df_stage3['propensity_score'].mean()
            st.metric("Average Score", f"{avg_score:.1f}")
        
        # Score distribution chart
        st.markdown("### 📊 Score Distribution")
        score_counts = pd.cut(df_stage3['propensity_score'], 
                              bins=[0, 50, 80, 100], 
                              labels=['Low (0-49)', 'Medium (50-79)', 'High (80-100)'])
        st.bar_chart(score_counts.value_counts().sort_index())
        
        # Priority level breakdown
        st.markdown("### 🎯 Priority Level Breakdown")
        priority_counts = df_stage3['priority_level'].value_counts()
        st.bar_chart(priority_counts)
        
        # Data table with filters
        st.markdown("### 📋 Ranked Lead Details")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            priority_filter = st.multiselect(
                "Filter by Priority",
                options=['High', 'Medium', 'Low'],
                default=['High', 'Medium', 'Low']
            )
        with col2:
            min_score = st.slider("Minimum Score", 0, 100, 0)
        
        # Apply filters
        df_filtered = df_stage3[df_stage3['priority_level'].isin(priority_filter)]
        df_filtered = df_filtered[df_filtered['propensity_score'] >= min_score]
        
        # Sort by rank
        df_filtered = df_filtered.sort_values('rank', ascending=True)
        
        # Column selection
        default_cols = ['rank', 'propensity_score', 'priority_level', 'name', 'title', 
                       'company', 'email', 'linkedin_url', 'company_hq', 'location']
        available_cols = df_filtered.columns.tolist()
        selected_cols = st.multiselect(
            "Select columns to display",
            options=available_cols,
            default=default_cols
        )
        
        if selected_cols:
            display_df = df_filtered[selected_cols]
        else:
            display_df = df_filtered
        
        # Search functionality
        search_term = st.text_input(
            "🔍 Search in results (name, company, etc.)", 
            "",
            key="stage3_search_term"
        )
        if search_term:
            mask = display_df.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            display_df = display_df[mask]
            st.info(f"Showing {len(display_df)} results matching '{search_term}'")
        
        # Display table
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Score breakdown for top leads
        if len(df_filtered) > 0:
            st.markdown("### 📈 Top 10 Leads Score Breakdown")
            top_10 = df_filtered.head(10)
            for idx, lead in top_10.iterrows():
                with st.expander(f"Rank {lead['rank']}: {lead.get('name', 'Unknown')} - Score: {lead['propensity_score']}"):
                    breakdown = lead.get('score_breakdown', {})
                    if isinstance(breakdown, dict):
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Role Fit", breakdown.get('role_fit', 0))
                        with col2:
                            st.metric("Scientific", breakdown.get('scientific_intent', 0))
                        with col3:
                            st.metric("Company", breakdown.get('company_intent', 0))
                        with col4:
                            st.metric("Technographic", breakdown.get('technographic', 0))
                        with col5:
                            st.metric("Location", breakdown.get('location', 0))
        
        # Download button
        csv_data = df_filtered.to_csv(index=False)
        st.download_button(
            label="📥 Download Stage 3 Data (CSV)",
            data=csv_data,
            file_name="stage3_ranking.csv",
            mime="text/csv",
            use_container_width=True
        )

# Divider
st.divider()

# Stage 4: Dashboard
st.subheader("Stage 4: Dashboard 📊")
col1, col2 = st.columns([1, 4])

with col1:
    stage4_button = st.button("▶️ Run Stage 4", type="primary", use_container_width=True,
                              disabled=st.session_state.stage3_data is None)

with col2:
    if st.session_state.stage3_data is None:
        st.warning("⚠️ Please complete Stage 3 first")
    elif st.session_state.stage4_data is not None:
        st.success(f"✅ Stage 4 Complete: {len(st.session_state.stage4_data)} leads in dashboard")
    else:
        st.info("ℹ️ Click the button to generate the final dashboard")

if stage4_button and st.session_state.stage3_data is not None:
    with st.spinner("Running Stage 4: Generating dashboard..."):
        try:
            from stages.stage4_dashboard import run_stage4
            stage4_result = run_stage4(st.session_state.stage3_data)
            st.session_state.stage4_data = stage4_result
            if stage4_result:
                st.success(f"✅ Stage 4 Complete: {len(stage4_result)} leads in dashboard")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error in Stage 4: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Display Stage 4 Dashboard
if st.session_state.stage4_data is not None and len(st.session_state.stage4_data) > 0:
    st.markdown("---")
    st.markdown("## 📊 Lead Generation Dashboard")
    
    # Convert to DataFrame
    df_dashboard = pd.DataFrame(st.session_state.stage4_data)
    
    # Summary Statistics
    st.markdown("### 📈 Summary Statistics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Leads", len(df_dashboard))
    
    with col2:
        high_priority = len(df_dashboard[df_dashboard['probability'] >= 80])
        st.metric("High Priority (80+)", high_priority)
    
    with col3:
        avg_score = df_dashboard['probability'].mean()
        st.metric("Average Score", f"{avg_score:.1f}")
    
    with col4:
        has_email = len(df_dashboard[df_dashboard['email'] != 'N/A'])
        st.metric("Leads with Email", has_email)
    
    with col5:
        has_linkedin = len(df_dashboard[df_dashboard['linkedin'] != 'N/A'])
        st.metric("Leads with LinkedIn", has_linkedin)
    
    with col6:
        # Top location (most common)
        valid_locations = df_dashboard[df_dashboard['location'] != 'N/A']['location']
        if len(valid_locations) > 0:
            top_location = valid_locations.mode()
            top_loc_str = top_location.iloc[0] if len(top_location) > 0 else "N/A"
            # Truncate if too long for display
            display_str = top_loc_str if len(top_loc_str) <= 20 else top_loc_str[:17] + "..."
        else:
            display_str = "N/A"
        st.metric("Top Location", display_str)
    
    st.markdown("---")
    
    # Filters Section
    st.markdown("### 🔍 Filters & Search")
    
    # Search bar
    search_term = st.text_input(
        "🔍 Global Search (Name, Title, Company, Location, HQ)",
        "",
        help="Search across all fields",
        key="stage4_global_search"
    )
    
    # Filter controls in columns
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    
    with filter_col1:
        min_score = st.slider("Minimum Probability", 0, 100, 0)
        priority_filter = st.multiselect(
            "Priority Level",
            options=['High (80+)', 'Medium (50-79)', 'Low (<50)'],
            default=['High (80+)', 'Medium (50-79)', 'Low (<50)']
        )
    
    with filter_col2:
        # Location filter - hub cities
        from utils.dashboard_utils import get_hub_cities, extract_hub_locations
        hub_cities = get_hub_cities()
        all_locations = df_dashboard[df_dashboard['location'] != 'N/A']['location'].unique().tolist()
        hub_locations = extract_hub_locations(all_locations, hub_cities)
        location_options = ['All'] + sorted(set(hub_cities + hub_locations))
        location_filter = st.selectbox("Location (Hub Cities)", options=location_options)
        
        company_filter = st.text_input(
            "Company Filter", 
            "", 
            help="Filter by company name",
            key="stage4_company_filter"
        )
    
    with filter_col3:
        has_email_filter = st.checkbox("Has Email Only", False)
        has_linkedin_filter = st.checkbox("Has LinkedIn Only", False)
    
    with filter_col4:
        # Sort options
        sort_by = st.selectbox(
            "Sort By",
            options=['rank', 'probability', 'name', 'company', 'location'],
            index=0
        )
        sort_order = st.radio("Sort Order", ['Ascending', 'Descending'], horizontal=True)
    
    # Apply filters
    df_filtered = df_dashboard.copy()
    
    # Search filter
    if search_term:
        mask = df_filtered.astype(str).apply(
            lambda x: x.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        df_filtered = df_filtered[mask]
    
    # Score filter
    df_filtered = df_filtered[df_filtered['probability'] >= min_score]
    
    # Priority filter
    from utils.dashboard_utils import calculate_priority_ranges, filter_by_priority_range
    priority_ranges = calculate_priority_ranges(priority_filter)
    df_filtered = filter_by_priority_range(df_filtered, priority_ranges)
    
    # Location filter
    if location_filter != 'All':
        df_filtered = df_filtered[
            df_filtered['location'].astype(str).str.contains(location_filter, case=False, na=False)
        ]
    
    # Company filter
    if company_filter:
        df_filtered = df_filtered[
            df_filtered['company'].astype(str).str.contains(company_filter, case=False, na=False)
        ]
    
    # Has email filter
    if has_email_filter:
        df_filtered = df_filtered[df_filtered['email'] != 'N/A']
    
    # Has LinkedIn filter
    if has_linkedin_filter:
        df_filtered = df_filtered[df_filtered['linkedin'] != 'N/A']
    
    # Sort
    ascending = sort_order == 'Ascending'
    df_filtered = df_filtered.sort_values(sort_by, ascending=ascending).reset_index(drop=True)
    
    # Display results count
    st.info(f"📊 Showing {len(df_filtered)} of {len(df_dashboard)} leads")
    
    st.markdown("---")
    
    # Dashboard Table
    st.markdown("### 📋 Lead Dashboard Table")
    
    # Make LinkedIn URLs clickable
    df_display = df_filtered.copy()
    if 'linkedin' in df_display.columns:
        def make_linkedin_clickable(url: str) -> str:
            """Convert LinkedIn URL to clickable markdown link."""
            if url and url != 'N/A' and (url.startswith('http://') or url.startswith('https://')):
                return f"[View Profile]({url})"
            return url
        df_display['linkedin'] = df_display['linkedin'].apply(make_linkedin_clickable)
    
    # Select columns in exact order
    column_order = ['rank', 'probability', 'name', 'title', 'company', 'location', 'hq', 'email', 'linkedin', 'action']
    available_cols = [col for col in column_order if col in df_display.columns]
    
    # Display table with exact columns
    st.dataframe(
        df_display[available_cols],
        use_container_width=True,
        height=500,
        hide_index=True
    )
    
    # Export Section
    st.markdown("---")
    st.markdown("### 💾 Export Data")
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        # CSV Export
        csv_data = df_filtered[available_cols].to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="lead_dashboard.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with export_col2:
        # Excel Export
        from utils.dashboard_utils import export_to_excel
        excel_buffer = export_to_excel(df_filtered[available_cols], sheet_name='Leads')
        
        if excel_buffer:
            excel_data = excel_buffer.getvalue()
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name="lead_dashboard.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("💡 Install openpyxl for Excel export: `pip install openpyxl`")
    
    # Additional Visualizations
    st.markdown("---")
    st.markdown("### 📊 Additional Insights")
    
    viz_col1, viz_col2 = st.columns(2)
    
    with viz_col1:
        st.markdown("#### Score Distribution")
        st.bar_chart(df_filtered['probability'].value_counts().sort_index())
    
    with viz_col2:
        st.markdown("#### Top Companies")
        top_companies = df_filtered[df_filtered['company'] != 'N/A']['company'].value_counts().head(10)
        st.bar_chart(top_companies)

