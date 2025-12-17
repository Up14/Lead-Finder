# Lead Finder: 3D In-Vitro Models for Toxicology

A comprehensive Streamlit application for identifying, enriching, ranking, and visualizing high-probability leads in the toxicology and preclinical safety space. This tool helps sales and marketing teams find decision-makers who are actively researching 3D in-vitro models, organ-on-chip technologies, and related toxicology solutions.

## Table of Contents

1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Stage-by-Stage Guide](#stage-by-stage-guide)
4. [Ranking Algorithm Deep Dive](#ranking-algorithm-deep-dive)
5. [Apollo.io Free Tier Limitations](#apolloio-free-tier-limitations)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)
8. [Project Structure](#project-structure)

---

## Overview

### What This Application Does

The Lead Finder application automates the process of finding and prioritizing potential customers in the toxicology and preclinical safety market. It:

1. **Identifies** leads from scientific publications (PubMed)
2. **Enriches** leads with contact information, LinkedIn profiles, and company data
3. **Ranks** leads by "Propensity to Buy" score (0-100)
4. **Visualizes** results in an interactive dashboard

### Target Audience

- Sales teams looking for qualified leads
- Marketing teams identifying target accounts
- Business development professionals in life sciences
- Anyone selling 3D in-vitro models, organ-on-chip, or toxicology solutions

### Key Features

- ✅ **PubMed Integration**: Free, unlimited searches of scientific publications
- ✅ **Multi-API Enrichment**: Apollo.io, Hunter.io, Clearbit support
- ✅ **Intelligent Scoring**: Weighted algorithm calculates buying probability
- ✅ **Smart Caching**: Saves API credits and speeds up searches
- ✅ **Interactive Dashboard**: Filter, search, and export leads
- ✅ **Export Options**: CSV and Excel formats

---

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Internet connection (for API calls)
- (Optional) API keys for enrichment services

### Installation Steps

1. **Navigate to the project directory:**
   ```bash
   cd "Lead Finder"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

4. **Access the application:**
   - The app will automatically open in your browser at `http://localhost:8501`
   - If not, navigate to the URL manually

### Configuration

No initial configuration required! The app works out of the box with:
- **PubMed API**: Free
- **Enrichment APIs**: add API keys in the sidebar when ready

---

## Stage-by-Stage Guide

### Stage 1: Identification 🔍

#### What It Does

Stage 1 searches PubMed (NCBI database) for scientific papers matching your keywords and extracts lead information from the authors.

#### How It Works

1. **Keyword Search**: Takes your scientific keywords (e.g., "Drug-Induced Liver Injury", "3D cell culture") and searches PubMed's Title/Abstract fields
2. **Paper Retrieval**: Fetches papers published within your specified time window (default: last 2 years)
3. **Author Extraction**: Extracts all authors from each paper, with special focus on:
   - **Corresponding Authors**: Usually the Principal Investigator (PI) or budget holder
   - **First Authors**: Often the actual user/influencer of the technology
4. **Data Parsing**: Extracts from each author:
   - Name
   - Affiliation (institution/company)
   - Email (if provided in paper)
   - Location (from affiliation text)
   - Company name (parsed from affiliation)
5. **Deduplication**: Uses fuzzy matching to merge duplicate leads (same person from multiple papers)

#### Example Input

```
Scientific Keywords: "Drug-Induced Liver Injury, 3D cell culture, Organ-on-chip"
Results per Keyword: 50
Years Back: 2
```

#### Example Output

```json
{
  "name": "Dr. Jane Smith",
  "title": "Director of Toxicology",
  "company": "Pfizer Inc.",
  "location": "Cambridge, MA",
  "email": "jane.smith@pfizer.com",
  "author_position": "Corresponding Author",
  "publication_title": "3D Hepatic Spheroids for Drug-Induced Liver Injury Assessment",
  "publication_date": "2023-06-15",
  "source": "PubMed"
}
```

#### Caching Mechanism

- Results are cached in `data/cache/pubmed_results.json`
- Cache expires after 30 days (configurable)
- Same keyword searches return cached results instantly
- Saves API calls and speeds up subsequent searches

#### Key Points

- ✅ **Free**: PubMed API is completely free, no limits
- ✅ **Fast**: Cached results load instantly
- ✅ **Comprehensive**: Searches Title AND Abstract fields
- ✅ **Recent**: Focuses on recent publications (last 2 years by default)

---

### Stage 2: Enrichment 📧

#### What It Does

Stage 2 enriches the leads from Stage 1 with additional contact information, verified company data, LinkedIn profiles, and location details using external APIs.

#### How It Works

1. **Lead Selection**: Chooses which leads to enrich based on priority:
   - **First N Leads**: Enriches the first N leads (default: 5)
   - **Corresponding Authors First**: Prioritizes corresponding authors
2. **API Enrichment**: For each lead, calls multiple APIs:
   - **LinkedIn Finder** (Apollo.io): Finds LinkedIn profile and verified job title
   - **Email Finder** (Apollo.io → Hunter.io fallback): Finds business email
   - **Phone Finder** (Apollo.io): Finds phone number
   - **Company Enricher** (Apollo.io → Clearbit fallback): Gets company HQ, funding stage, industry
3. **Data Merging**: Combines all enrichment data with original lead data
4. **Caching**: Saves enrichment results to avoid re-enriching the same leads

#### APIs Used

| API | Purpose | Free Tier | Limitations |
|-----|---------|-----------|-------------|
| **Apollo.io** | LinkedIn, Email, Phone, Company | Limited | See [Apollo.io Free Tier](#apolloio-free-tier-limitations) |
| **Hunter.io** | Email (fallback) | 25 searches/month | Limited to email finding |
| **Clearbit** | Company data (fallback) | 50 requests/month | Basic company info only |

#### Example: Before Enrichment

```json
{
  "name": "Dr. Jane Smith",
  "company": "Pfizer Inc.",
  "email": "jane.smith@pfizer.com",
  "location": "Cambridge, MA"
}
```

#### Example: After Enrichment

```json
{
  "name": "Dr. Jane Smith",
  "linkedin_title": "Director of Preclinical Safety",
  "linkedin_url": "https://linkedin.com/in/jane-smith",
  "company": "Pfizer Inc.",
  "company_name_verified": "Pfizer Inc.",
  "company_hq": "New York, NY",
  "company_industry": "Pharmaceuticals",
  "company_funding_stage": "Public",
  "email": "jane.smith@pfizer.com",
  "phone": "+1-617-555-0123",
  "person_location": "Cambridge, MA",
  "enrichment_status": "success"
}
```

#### What Happens When APIs Fail?

- **Graceful Degradation**: If an API fails, the app continues with available data
- **Fallback APIs**: Automatically tries alternative APIs (e.g., Hunter.io if Apollo fails)
- **Partial Enrichment**: Leads are saved even if only some fields are enriched
- **Error Logging**: All failures are logged for debugging

#### Key Points

- ⚠️ **API Credits**: Free tiers have limits - use "Leads to Enrich" setting to conserve credits
- ✅ **Caching**: Enriched results are cached to save API calls
- ✅ **Multiple Sources**: Tries multiple APIs for better data coverage
- ⚠️ **Apollo.io Free Tier**: Has significant limitations (see detailed section below)

---

### Stage 3: Ranking 🎯

#### What It Does

Stage 3 calculates a "Propensity to Buy" score (0-100) for each enriched lead and ranks them from highest to lowest probability.

#### How It Works

1. **Score Calculation**: For each lead, calculates score based on 5 weighted criteria
2. **Ranking**: Sorts leads by score (highest first)
3. **Priority Classification**: Categorizes leads as High (80+), Medium (50-79), or Low (<50)
4. **Score Breakdown**: Stores detailed breakdown showing points from each criterion

#### Scoring Criteria (Total: 115 points, capped at 100)

| Criterion | Points | Weight | Description |
|-----------|--------|--------|-------------|
| **Role Fit** | 30 | High | Job title matches target roles |
| **Scientific Intent** | 40 | Highest | Published on DILI/liver toxicity recently |
| **Company Intent** | 20 | Medium | Company raised Series A/B funding |
| **Technographic** | 15 | Medium | Company uses similar technology |
| **Location** | 10 | Low | Located in biotech hub city |

#### Detailed Scoring Logic

See [Ranking Algorithm Deep Dive](#ranking-algorithm-deep-dive) for complete details.

#### Example Output

```json
{
  "name": "Dr. Jane Smith",
  "rank": 1,
  "propensity_score": 95,
  "priority_level": "High",
  "score_breakdown": {
    "role_fit": 30,
    "scientific_intent": 40,
    "company_intent": 20,
    "technographic": 15,
    "location": 10
  }
}
```

#### Key Points

- ✅ **Weighted Algorithm**: More important factors (scientific intent) get higher weights
- ✅ **Transparent**: Score breakdown shows exactly why each lead scored what it did
- ✅ **Actionable**: High priority leads (80+) are ready for immediate outreach

---

### Stage 4: Dashboard 📊

#### What It Does

Stage 4 creates an interactive, searchable dashboard with all ranked leads in a final format ready for outreach.

#### Features

1. **Summary Statistics**:
   - Total leads
   - High priority count
   - Average score
   - Leads with email/LinkedIn
   - Top location

2. **Advanced Filtering**:
   - Minimum probability score
   - Priority level (High/Medium/Low)
   - Location (hub cities)
   - Company name
   - Has email/LinkedIn filters

3. **Search Functionality**:
   - Global search across all fields
   - Real-time filtering
   - Case-insensitive

4. **Sorting**:
   - Sort by rank, probability, name, company, location
   - Ascending/descending order

5. **Export Options**:
   - CSV export (all data)
   - Excel export (formatted)

#### Dashboard Columns

| Column | Description |
|--------|-------------|
| **Rank** | Ranking number (1, 2, 3...) |
| **Probability** | Propensity to Buy score (0-100) |
| **Name** | Lead's full name |
| **Title** | Job title (from LinkedIn or PubMed) |
| **Company** | Company name (verified) |
| **Location** | Person's location |
| **HQ** | Company headquarters |
| **Email** | Business email address |
| **LinkedIn** | LinkedIn profile URL (clickable) |
| **Action** | Default: "Contact" |

#### Key Points

- ✅ **Ready for Outreach**: All contact information in one place
- ✅ **Filterable**: Find exactly the leads you need
- ✅ **Exportable**: Download for CRM import
- ✅ **Interactive**: Real-time search and filtering

---

## Ranking Algorithm Deep Dive

### Complete Scoring Formula

The Propensity to Buy score is calculated as:

```
Total Score = Role Fit + Scientific Intent + Company Intent + Technographic + Location
Final Score = min(Total Score, 100)  // Capped at 100
```

### Criterion 1: Role Fit (+30 points)

**Purpose**: Identifies if the person's job title indicates they're a decision-maker or influencer in toxicology/safety.

**Logic**:
- Checks if job title contains any of these keywords:
  - `toxicology`, `safety`, `hepatic`, `3d`, `preclinical`
  - `pre-clinical`, `drug safety`, `safety assessment`
  - `preclinical safety`, `toxicologist`, `safety scientist`
- Case-insensitive matching
- Checks both LinkedIn title and PubMed title

**Why 30 Points?**
- High weight because job title is a strong indicator of relevance
- But not highest because title alone doesn't guarantee buying intent

**Example**:
```
Title: "Director of Preclinical Safety"
→ Contains "preclinical" and "safety"
→ Score: +30 points
```

**Example (No Match)**:
```
Title: "Research Scientist"
→ No matching keywords
→ Score: +0 points
```

---

### Criterion 2: Scientific Intent (+40 points)

**Purpose**: Identifies if the person has recently published on topics directly related to your solution (DILI, liver toxicity, 3D models).

**Logic**:
1. Checks if publication title contains scientific keywords:
   - `dili`, `drug-induced liver injury`, `liver toxicity`
   - `hepatic`, `liver injury`, `drug-induced`
   - `hepatotoxicity`, `liver damage`
2. Verifies publication is recent (within last 2 years)
3. Both conditions must be met

**Why 40 Points?**
- **Highest weight** because recent publication on relevant topic = active research = high buying intent
- Shows the person is actively working on problems your solution solves

**Example**:
```
Publication: "3D Hepatic Spheroids for Drug-Induced Liver Injury Assessment"
Date: "2023-06-15" (within last 2 years)
→ Contains "drug-induced liver injury" AND recent
→ Score: +40 points
```

**Example (Old Publication)**:
```
Publication: "Drug-Induced Liver Injury in 2D Cultures"
Date: "2020-01-15" (more than 2 years ago)
→ Contains keyword but too old
→ Score: +0 points
```

**Example (Wrong Topic)**:
```
Publication: "Cardiac Toxicity Assessment"
Date: "2023-06-15" (recent)
→ Recent but not relevant topic
→ Score: +0 points
```

---

### Criterion 3: Company Intent (+20 points)

**Purpose**: Identifies if the company has budget (recently raised funding = has money to spend).

**Logic**:
- Checks `company_funding_stage` field from enrichment
- Awards points based on funding stage:
  - **Series A or B**: +20 points (highest - actively growing, has budget)
  - **Series C or IPO**: +15 points (still growing but more established)
  - **Other/Unknown**: +0 points

**Why 20 Points?**
- Medium-high weight because funding = budget = ability to buy
- Series A/B companies are actively scaling and need solutions

**Example**:
```
Company: "ToxiTech Solutions"
Funding Stage: "Series B"
→ Series B detected
→ Score: +20 points
```

**Example (No Funding Info)**:
```
Company: "Large Pharma Inc."
Funding Stage: "Public" (or empty)
→ No Series A/B/C detected
→ Score: +0 points
```

---

### Criterion 4: Technographic (+15 points)

**Purpose**: Identifies if the company already uses similar technology (shows they understand the value).

**Logic**:
- Checks if company industry or publication title contains technology keywords:
  - `3d`, `in-vitro`, `in vitro`, `organ-on-chip`, `organ on chip`
  - `spheroid`, `cell culture`, `nam`, `new approach methodology`
  - `organoid`, `microphysiological`, `mps`
- If found, indicates company is already in the space

**Why 15 Points?**
- Medium weight because existing tech use = easier sale (they understand the value)
- But not highest because they might already have a solution

**Example**:
```
Company Industry: "Biotechnology - 3D Cell Culture"
Publication: "Organ-on-Chip Models for Toxicology"
→ Contains "3d", "organ-on-chip"
→ Score: +15 points
```

---

### Criterion 5: Location (+10 points)

**Purpose**: Identifies if the person/company is in a biotech hub (easier to reach, more likely to be innovative).

**Logic**:
- Checks if location matches any hub city:
  - **Boston/Cambridge**: Boston, Cambridge, Cambridge MA
  - **Bay Area**: San Francisco, Palo Alto, South San Francisco, etc.
  - **Basel**: Basel, Switzerland
  - **UK Golden Triangle**: London, Oxford, Cambridge UK
- Checks both person location and company HQ

**Why 10 Points?**
- Lowest weight because location is nice-to-have, not critical
- Hub cities have more biotech activity, but remote work is common

**Example**:
```
Location: "Cambridge, MA"
→ Matches Boston/Cambridge hub
→ Score: +10 points
```

**Example (Non-Hub)**:
```
Location: "Austin, TX"
→ Not a recognized hub
→ Score: +0 points
```

---

### Complete Score Calculation Example

Let's calculate the score for a real lead:

**Lead Data**:
```json
{
  "name": "Dr. Sarah Johnson",
  "linkedin_title": "Director of Toxicology",
  "publication_title": "3D Hepatic Models for Drug-Induced Liver Injury",
  "publication_date": "2023-08-20",
  "company_funding_stage": "Series A",
  "company_industry": "Biotechnology - Organ-on-Chip",
  "person_location": "Cambridge, MA"
}
```

**Score Calculation**:

1. **Role Fit**: "Director of Toxicology" → Contains "toxicology" → **+30 points**
2. **Scientific Intent**: "3D Hepatic Models for Drug-Induced Liver Injury" (2023) → Contains "drug-induced liver injury" AND recent → **+40 points**
3. **Company Intent**: "Series A" → Series A detected → **+20 points**
4. **Technographic**: "Organ-on-Chip" in industry → Contains "organ-on-chip" → **+15 points**
5. **Location**: "Cambridge, MA" → Hub city → **+10 points**

**Total**: 30 + 40 + 20 + 15 + 10 = **115 points**
**Final Score**: min(115, 100) = **100 points** (capped)
**Priority Level**: High (≥80)

---

### Why Scores Look This Way

The scoring system is designed to prioritize leads who:

1. **Have the Right Role** (30 pts): They're decision-makers or influencers
2. **Show Active Research** (40 pts): They're actively working on problems you solve
3. **Have Budget** (20 pts): Their company can afford your solution
4. **Understand the Tech** (15 pts): They already use similar solutions
5. **Are Accessible** (10 pts): They're in locations where you can reach them

**The weights reflect buying probability**:
- Scientific Intent (40) > Role Fit (30) because recent research = immediate need
- Company Intent (20) > Technographic (15) because budget > existing tech
- Location (10) is lowest because it's least critical

**Score Ranges**:
- **80-100 (High)**: Ready for immediate outreach - strong match on multiple criteria
- **50-79 (Medium)**: Good prospects - worth following up
- **0-49 (Low)**: Weak matches - may need more qualification

---

## Apollo.io Free Tier Limitations

### Overview

Apollo.io offers a free tier, but it has **significant limitations** that affect the Lead Finder application. Understanding these limitations helps you plan your enrichment strategy.

### Blocked Endpoints

The following Apollo.io API endpoints are **NOT available** on the free plan:

1. **`/v1/mixed_people/search`** - Person search endpoint
   - Used for: Finding LinkedIn profiles, emails, phone numbers
   - Error: `403 - "api/v1/mixed_people/search is not accessible with this api_key on a free plan"`

2. **`/v1/organizations/search`** - Company search endpoint
   - Used for: Finding company data, funding stage, HQ location
   - Error: `403 - "api/v1/organizations/search is not accessible with this api_key on a free plan"`

### What This Means

If you're using Apollo.io's free tier, you will experience:

#### ❌ Issues You'll Encounter

1. **No LinkedIn Profile Finding**
   - The app cannot find LinkedIn profiles using Apollo.io
   - You'll see warnings: `"Apollo.io API error 403: This endpoint may not be accessible on a free plan"`

2. **No Email Finding via Apollo**
   - Email enrichment via Apollo.io will fail
   - The app automatically falls back to Hunter.io (if you have a key)

3. **No Company Data Enrichment**
   - Company HQ, funding stage, industry won't be enriched via Apollo
   - Falls back to Clearbit (if you have a key)

4. **No Phone Number Finding**
   - Phone enrichment will fail

#### ✅ What Still Works

- The app **continues to work** - it just skips Apollo.io and uses fallback APIs
- PubMed data (Stage 1) is **unaffected**
- Scoring (Stage 3) still works (uses available data)
- Dashboard (Stage 4) still works

### Error Messages You'll See

When Apollo.io free tier limitations are hit, you'll see:

```
⚠️ Apollo.io API error 403: {"error":"api/v1/mixed_people/search is not accessible with this api_key on a free plan."}
ℹ️ Apollo.io's free plan does not support the 'mixed_people/search' and 'organizations/search' endpoints.
```

### Workarounds

#### Option 1: Use Alternative APIs (Recommended)

The app supports multiple APIs with automatic fallback:

1. **For Email**:
   - Primary: Apollo.io (fails on free tier)
   - Fallback: Hunter.io (25 free searches/month)
   - **Solution**: Add Hunter.io API key in sidebar

2. **For Company Data**:
   - Primary: Apollo.io (fails on free tier)
   - Fallback: Clearbit (50 free requests/month)
   - **Solution**: Add Clearbit API key in sidebar

3. **For LinkedIn**:
   - Primary: Apollo.io (fails on free tier)
   - **Solution**: LinkedIn data comes from PubMed affiliations (Stage 1) if available

#### Option 2: Upgrade Apollo.io Plan

- Upgrade to a paid Apollo.io plan to access all endpoints
- Pricing varies - check Apollo.io website for current plans
- Once upgraded, all enrichment features work fully

#### Option 3: Manual Enrichment

- Export leads from Stage 1 (CSV)
- Manually enrich using Kaspr browser extension or other tools
- Import enriched data back (future feature)

### Impact on Scoring

Apollo.io free tier limitations **do affect scoring**:

| Criterion | Impact | Workaround |
|-----------|--------|------------|
| **Role Fit** | ⚠️ Reduced | Uses PubMed title if LinkedIn unavailable |
| **Company Intent** | ❌ Lost | No funding stage data (0 points) |
| **Technographic** | ⚠️ Reduced | Uses publication title only |
| **Location** | ⚠️ Reduced | Uses PubMed location if company HQ unavailable |

**Example**: A lead that would score 95 with full enrichment might score 65-75 with free tier limitations.

### Best Practice

1. **Start with Free APIs**: Use Hunter.io and Clearbit free tiers
2. **Test with Small Batches**: Enrich 5 leads at a time to conserve credits
3. **Upgrade When Ready**: Once you validate the tool, upgrade Apollo.io for full functionality
4. **Combine Sources**: Use multiple APIs for best coverage

---

## Examples

### Example 1: Complete Lead Journey

#### Stage 1 Output (Identification)

```json
{
  "name": "Dr. Michael Chen",
  "title": "Senior Scientist",
  "company": "Biotech Innovations Inc.",
  "location": "Boston, MA",
  "email": "m.chen@biotechinnovations.com",
  "author_position": "Corresponding Author",
  "publication_title": "Advanced 3D Hepatic Spheroid Models for Drug-Induced Liver Injury Assessment",
  "publication_date": "2023-09-10",
  "publication_journal": "Toxicology in Vitro",
  "source": "PubMed"
}
```

#### Stage 2 Output (Enrichment)

```json
{
  "name": "Dr. Michael Chen",
  "linkedin_title": "Director of Preclinical Safety",
  "linkedin_url": "https://linkedin.com/in/michael-chen",
  "company": "Biotech Innovations Inc.",
  "company_name_verified": "Biotech Innovations Inc.",
  "company_hq": "Cambridge, MA",
  "company_industry": "Biotechnology - 3D Cell Culture",
  "company_funding_stage": "Series B",
  "email": "m.chen@biotechinnovations.com",
  "phone": "+1-617-555-0198",
  "person_location": "Boston, MA",
  "enrichment_status": "success"
}
```

#### Stage 3 Output (Ranking)

```json
{
  "name": "Dr. Michael Chen",
  "rank": 1,
  "propensity_score": 100,
  "priority_level": "High",
  "score_breakdown": {
    "role_fit": 30,
    "scientific_intent": 40,
    "company_intent": 20,
    "technographic": 15,
    "location": 10
  }
}
```

**Score Explanation**:
- ✅ Role Fit (30): "Director of Preclinical Safety" contains "preclinical" and "safety"
- ✅ Scientific Intent (40): Published on "Drug-Induced Liver Injury" in 2023 (recent)
- ✅ Company Intent (20): Company is Series B (has budget)
- ✅ Technographic (15): Company industry contains "3D Cell Culture"
- ✅ Location (10): Boston/Cambridge is a hub city
- **Total: 115 → Capped at 100**

#### Stage 4 Output (Dashboard)

| Rank | Probability | Name | Title | Company | Location | HQ | Email | LinkedIn | Action |
|------|-------------|------|-------|---------|----------|-----|--------|----------|--------|
| 1 | 100 | Dr. Michael Chen | Director of Preclinical Safety | Biotech Innovations Inc. | Boston, MA | Cambridge, MA | m.chen@biotechinnovations.com | [View Profile](https://linkedin.com/in/michael-chen) | Contact |

---

### Example 2: Score Calculation Walkthrough

**Lead**: Dr. Emily Rodriguez

**Data**:
- Title: "Research Scientist" (no match)
- Publication: "Cardiac Toxicity in 2D Cultures" (wrong topic, old)
- Company Funding: "Seed" (not Series A/B)
- Industry: "Pharmaceuticals" (no tech keywords)
- Location: "Austin, TX" (not a hub)

**Score Calculation**:

1. **Role Fit**: "Research Scientist" → No keywords → **0 points**
2. **Scientific Intent**: Wrong topic + old → **0 points**
3. **Company Intent**: "Seed" → Not Series A/B → **0 points**
4. **Technographic**: No tech keywords → **0 points**
5. **Location**: "Austin, TX" → Not a hub → **0 points**

**Total Score**: 0 + 0 + 0 + 0 + 0 = **0 points**
**Priority Level**: Low

**Why Low Score?**
- No role match (not a decision-maker)
- No relevant research (wrong topic)
- No budget signal (early stage funding)
- No tech alignment
- Not in a hub

---

### Example 3: Medium Priority Lead

**Lead**: Dr. James Wilson

**Data**:
- Title: "Toxicology Manager" (contains "toxicology") → **+30**
- Publication: "Liver Toxicity Assessment" (2022, within 2 years) → **+40**
- Company Funding: "Series C" → **+15** (not A/B, but has funding)
- Industry: "Pharmaceuticals" (no tech keywords) → **0**
- Location: "Chicago, IL" (not a hub) → **0**

**Total Score**: 30 + 40 + 15 + 0 + 0 = **85 points**
**Priority Level**: High (≥80)

**Why High Score Despite Missing Some Criteria?**
- Strong scientific intent (40 points) - actively researching relevant topic
- Good role fit (30 points) - decision-maker
- Some budget signal (15 points) - company has funding
- Missing tech and location, but core criteria are strong

---

## Troubleshooting

### Common Issues

#### Issue 1: "No leads found in Stage 1"

**Symptoms**: Stage 1 completes but returns 0 leads

**Possible Causes**:
1. Keywords too specific or misspelled
2. No papers published in the time window
3. Internet connection issues

**Solutions**:
- Try broader keywords (e.g., "liver" instead of "hepatic spheroid toxicity")
- Increase "Years Back" to 3 or 4
- Check internet connection
- Verify keywords are relevant to your domain

---

#### Issue 2: "Apollo.io API error 403"

**Symptoms**: See error message about free plan limitations

**Cause**: Apollo.io free tier doesn't support the endpoints used

**Solutions**:
- Add Hunter.io API key for email (fallback)
- Add Clearbit API key for company data (fallback)
- Upgrade Apollo.io plan
- Continue with available data (app still works)

---

#### Issue 3: "No email found for leads"

**Symptoms**: Enriched leads have no email addresses

**Possible Causes**:
1. Apollo.io free tier limitation (no email endpoint)
2. Hunter.io credits exhausted
3. Email not available in databases

**Solutions**:
- Add Hunter.io API key (25 free searches/month)
- Check Hunter.io credit status in sidebar
- Some leads simply don't have emails in databases (normal)

---

#### Issue 4: "Low scores for all leads"

**Symptoms**: All leads score below 50

**Possible Causes**:
1. Leads don't match target criteria
2. Missing enrichment data (Apollo.io free tier)
3. Publications too old

**Solutions**:
- Check score breakdown to see which criteria are missing
- Ensure enrichment completed successfully
- Try different keywords to find better-matched leads
- Review scoring criteria to understand requirements

---

#### Issue 5: "Cache not clearing"

**Symptoms**: Old results keep appearing

**Solutions**:
- Click "Clear All Cache" button in sidebar
- Manually delete `data/cache/` directory
- Cache expires after 30 days automatically

---

#### Issue 6: "Import errors"

**Symptoms**: `ModuleNotFoundError` or import errors

**Solutions**:
```bash
pip install -r requirements.txt
```

Make sure all dependencies are installed.

---

### API Error Codes

| Error Code | Meaning | Solution |
|------------|---------|----------|
| **403** | Free tier limitation (Apollo.io) | Use alternative APIs or upgrade |
| **401** | Invalid API key | Check API key in sidebar |
| **429** | Rate limit exceeded | Wait a few minutes, reduce batch size |
| **500** | API server error | Try again later |

---

## Project Structure

```
Lead Finder/
├── app.py                          # Main Streamlit application
├── stages/
│   ├── __init__.py
│   ├── stage1_identification.py   # Stage 1: PubMed search & extraction
│   ├── stage2_enrichment.py        # Stage 2: API enrichment
│   ├── stage3_ranking.py           # Stage 3: Score calculation & ranking
│   ├── stage4_dashboard.py         # Stage 4: Dashboard transformation
│   └── cache_manager.py            # Caching system
├── utils/
│   ├── __init__.py
│   ├── pubmed_api.py               # PubMed/NCBI API wrapper
│   ├── data_processing.py          # Deduplication & data cleaning
│   ├── email_finder.py             # Email finding (Apollo, Hunter)
│   ├── phone_finder.py             # Phone finding (Apollo)
│   ├── linkedin_finder.py          # LinkedIn finding (Apollo)
│   ├── company_enricher.py         # Company data (Apollo, Clearbit)
│   ├── scoring.py                  # Ranking algorithm
│   ├── api_credit_manager.py       # API credit tracking
│   └── dashboard_utils.py          # Dashboard utilities
├── data/
│   └── cache/
│       ├── pubmed_results.json     # Stage 1 cache
│       └── stage2_enrichment.json  # Stage 2 cache
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

---

## Data Sources

### Currently Implemented

- **PubMed API** (NCBI E-utilities)
  - Free, unlimited searches
  - No authentication required
  - Searches Title and Abstract fields
  - Extracts author information

- **Apollo.io API**
  - LinkedIn profiles
  - Email addresses
  - Phone numbers
  - Company data
  - ⚠️ Free tier has limitations

- **Hunter.io API**
  - Email addresses (fallback)
  - 25 free searches/month

- **Clearbit API**
  - Company data (fallback)
  - 50 free requests/month

---

## Requirements

- Python 3.8+
- See `requirements.txt` for all dependencies:
  - streamlit
  - pandas
  - requests
  - beautifulsoup4
  - lxml
  - fuzzywuzzy
  - python-Levenshtein
  - openpyxl (for Excel export)
  - altair (for charts)

---

## License

This project is for internal use.

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review API documentation for specific services
3. Check application logs for detailed error messages

---

**Last Updated**: 2024
**Version**: 1.0
