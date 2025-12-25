"""
Document Processing Utilities for ReguLens
"""
import re
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def extract_requirements(text: str, pages_data: list = None, 
                        document_name: str = "Document") -> List[Dict]:
    """
    Extract compliance requirements from text with page tracking
    
    Args:
        text: Document text
        pages_data: List of page info from PDF extraction
        document_name: Name of document for reference
    
    Returns:
        List of requirements with metadata including page numbers
    """
    requirements = []
    req_id = 1
    
    # Keywords indicating mandatory requirements
    mandatory_patterns = [
        r'\bmust\b', r'\bshall\b', r'\brequired\b', 
        r'\bmandatory\b', r'\bobligation\b'
    ]
    
    # Split into sentences
    sentences = re.split(r'[.!?]\n', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        
        # Skip short sentences
        if len(sentence) < 20:
            continue
        
        # Check if contains mandatory keywords
        has_mandatory = any(
            re.search(pattern, sentence, re.IGNORECASE) 
            for pattern in mandatory_patterns
        )
        
        if has_mandatory:
            # Determine criticality based on keywords
            if any(word in sentence.lower() for word in ['critical', 'essential', 'immediately']):
                criticality = 'HIGH'
            else:
                criticality = 'MEDIUM'
            
            keywords = extract_key_phrases(sentence)
            
            # Find page number if available
            page_num = None
            if pages_data:
                from utils.pdf_extractor import find_page_number
                page_num = find_page_number(sentence, pages_data)
            
            requirements.append({
                'id': f'REQ-{req_id:03d}',
                'text': sentence,
                'criticality': criticality,
                'keywords': keywords,
                'section': 'Unknown',
                'page_number': page_num,
                'document_name': document_name
            })
            req_id += 1
    
    return requirements


def extract_key_phrases(text: str) -> List[str]:
    """
    Extract important keywords/phrases from text
    
    Args:
        text: Input text
    
    Returns:
        List of key phrases
    """
    # Simple keyword extraction
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'been',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                  'can', 'could', 'may', 'might', 'must', 'shall'}
    
    # Extract words (alphanumeric sequences)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter out stop words
    keywords = [w for w in words if w not in stop_words]
    
    # Return unique keywords (first 10)
    return list(dict.fromkeys(keywords))[:10]


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two texts
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity score (0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    try:
        vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except:
        # Fallback: simple word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0


def categorize_risk(gap_status: str, criticality: str) -> str:
    """
    Determine risk level based on gap and criticality
    
    Args:
        gap_status: MISSING, PARTIAL, or COMPLIANT
        criticality: HIGH, MEDIUM, or LOW
    
    Returns:
        Risk level: CRITICAL, HIGH, MEDIUM, or LOW
    """
    risk_matrix = {
        ('MISSING', 'HIGH'): 'CRITICAL',
        ('MISSING', 'MEDIUM'): 'HIGH',
        ('MISSING', 'LOW'): 'MEDIUM',
        ('PARTIAL', 'HIGH'): 'HIGH',
        ('PARTIAL', 'MEDIUM'): 'MEDIUM',
        ('PARTIAL', 'LOW'): 'LOW',
        ('COMPLIANT', 'HIGH'): 'LOW',
        ('COMPLIANT', 'MEDIUM'): 'LOW',
        ('COMPLIANT', 'LOW'): 'LOW',
    }
    
    return risk_matrix.get((gap_status, criticality), 'MEDIUM')


def generate_recommendation(gap_status: str, requirement_text: str, 
                          matched_control: str = None, match_score: float = 0.0,
                          gemini_client=None, 
                          req_page: int = None, ctrl_page: int = None,
                          req_doc: str = "Regulation", ctrl_doc: str = "Policy") -> dict:
    """
    Generate two-tier recommendations: simple summary + detailed remediation
    
    Returns:
        dict with 'quick_summary' and 'detailed_plan' keys
    """
    
    if gemini_client:
        try:
            if gap_status == 'MISSING':
                page_ref = f" (Regulation page {req_page})" if req_page else ""
                
                # TIER 1: Quick Summary
                quick_prompt = f"""You are explaining a compliance gap to a business executive (non-technical).

REGULATORY REQUIREMENT{page_ref}:
{requirement_text}

STATUS: This requirement is MISSING from the company policy.

Generate a simple 2-3 sentence explanation in plain language:
- What's missing
- Why it matters (consequences)
- What needs to happen (high-level action)

Keep it simple and direct. No jargon. Start with emoji and severity: 🔴 CRITICAL or 🟠 HIGH."""

                quick_response = gemini_client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=quick_prompt
                )
                quick_summary = quick_response.text.strip()
                
                # TIER 2: Detailed Remediation
                detailed_prompt = f"""You are a compliance expert advising a CA firm's compliance officer.

REGULATORY REQUIREMENT{page_ref}:
{requirement_text}

This requirement is MISSING from the user's internal policy document.

Generate a detailed, structured remediation plan in this EXACT format:

**COMPLIANCE GAP ANALYSIS:**
[Technical explanation of what's missing and regulatory implications]

**REGULATORY REQUIREMENT:**
[Quote exact requirement with numbers/timelines/thresholds]

**IMPLEMENTATION STEPS:**
1. [Specific action - e.g., "Add new section 3.2 titled 'PAN Card Collection Requirements'"]
2. [Next action - e.g., "Update threshold in system from ₹X to ₹Y"]
3. [Documentation - e.g., "Document procedure in operations manual"]
4. [Training - e.g., "Conduct training session for operations team"]
5. [Verification - e.g., "Internal audit to verify implementation"]

**SUGGESTED POLICY LANGUAGE:**
[Draft 3-4 sentences that can be directly added to policy document]

**SYSTEM/PROCESS CHANGES REQUIRED:**
- [Specific system configuration change]
- [Form/template update needed]
- [Workflow modification]

**RESPONSIBLE PARTIES:**
- Policy Update: [Compliance Team]
- System Changes: [IT/Operations]
- Training: [HR/Compliance]

**IMPLEMENTATION TIMELINE:** [Realistic timeline with milestones]

**REGULATORY RISK IF NOT ADDRESSED:** 
[Specific penalties, amounts, legal consequences]

**EVIDENCE OF COMPLIANCE:**
[What documentation/proof will demonstrate compliance]"""

                detailed_response = gemini_client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=detailed_prompt
                )
                detailed_plan = detailed_response.text.strip()

            elif gap_status == 'PARTIAL':
                req_page_ref = f" (Regulation page {req_page})" if req_page else ""
                ctrl_page_ref = f" (Your policy page {ctrl_page})" if ctrl_page else ""
                
                # TIER 1: Quick Summary
                quick_prompt = f"""You are explaining a compliance gap to a business executive.

WHAT REGULATION REQUIRES{req_page_ref}:
{requirement_text}

WHAT CURRENT POLICY SAYS{ctrl_page_ref}:
{matched_control}

MATCH LEVEL: {match_score:.0%}

Generate a simple 2-3 sentence explanation:
- What's the mismatch (be specific about numbers/thresholds if any)
- Where to fix it (page number, section)
- What to change (the exact update needed)

Plain language. Start with emoji: 🟡 UPDATE or 🟠 ENHANCE."""

                quick_response = gemini_client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=quick_prompt
                )
                quick_summary = quick_response.text.strip()
                
                # TIER 2: Detailed Remediation
                detailed_prompt = f"""You are a compliance expert.

REGULATORY REQUIREMENT{req_page_ref}:
{requirement_text}

CURRENT POLICY CONTROL{ctrl_page_ref} (Match: {match_score:.0%}):
{matched_control}

Generate a detailed remediation plan in this format:

**GAP ANALYSIS:**
[Detailed comparison of regulation vs current policy - highlight specific differences]

**WHAT REGULATION REQUIRES:**
[Quote exact text with numbers/dates/thresholds]

**WHAT YOUR POLICY CURRENTLY STATES:**
[Quote current policy text showing the gap]

**SPECIFIC CHANGES REQUIRED:**
1. Page {ctrl_page if ctrl_page else '[X]'}, Section [X.X]: Change "[current text]" to "[new text]"
2. [Next specific change with location]
3. [Additional modifications needed]

**REVISED POLICY LANGUAGE:**
[Provide corrected paragraph that replaces current text]

**SIDE-BY-SIDE COMPARISON:**
| Aspect | Regulation | Your Policy | Action |
|--------|-----------|-------------|--------|
| [e.g., Threshold] | [₹50,000] | [₹2,00,000] | [Reduce to ₹50,000] |

**IMPLEMENTATION STEPS:**
1. [Update policy document]
2. [System configuration changes]
3. [Staff communication]
4. [Training updates]

**TIMELINE:** [With milestones]

**VALIDATION:** [How to verify the update is complete]"""

                detailed_response = gemini_client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=detailed_prompt
                )
                detailed_plan = detailed_response.text.strip()

            else:  # COMPLIANT
                quick_summary = "✅ **COMPLIANT** - No action needed. Your policy addresses this requirement."
                detailed_plan = """**COMPLIANCE STATUS: ✅ COMPLIANT**

Your policy adequately addresses this regulatory requirement. 

**RECOMMENDED ACTIONS:**
- Continue periodic monitoring (quarterly review recommended)
- Document compliance status in audit trail
- Monitor for regulatory updates or amendments

**NEXT REVIEW DATE:** [Next quarter]"""

            return {
                'quick_summary': quick_summary.replace('**', '').replace('*', ''),
                'detailed_plan': detailed_plan.replace('###', '').replace('####', '')
            }
            
        except Exception as e:
            print(f"⚠️ Gemini recommendation failed: {e}")
    
    # Fallback recommendations
    page_info = f" on page {req_page}" if req_page else ""
    ctrl_page_info = f" (Update page {ctrl_page})" if ctrl_page else ""
    
    if gap_status == 'MISSING':
        quick = f"🔴 CRITICAL: Your policy is missing this requirement{page_info}. Add control section immediately."
        detailed = f"""**CRITICAL: MISSING REQUIREMENT**

**GAP:** Requirement not found in policy{page_info}

**REQUIREMENT:**
{requirement_text[:200]}...

**ACTIONS:**
1. Add new section to policy{ctrl_page_info}
2. Define procedures
3. Train staff

**TIMELINE:** Immediate"""
    
    elif gap_status == 'PARTIAL':
        quick = f"🟡 UPDATE NEEDED: Policy partially complies ({match_score:.0%} match){ctrl_page_info}. Align thresholds/procedures."
        detailed = f"""**PARTIAL COMPLIANCE**

**GAP:** {match_score:.0%} match - alignment needed

**REGULATION{page_info}:**
{requirement_text[:150]}...

**YOUR POLICY{ctrl_page_info}:**
{matched_control[:150] if matched_control else 'Exists but incomplete'}...

**ACTIONS:**
1. Compare requirements
2. Update policy
3. Verify changes"""
    
    else:
        quick = "✅ COMPLIANT - No changes needed."
        detailed = "**COMPLIANT** - Continue monitoring."
    
    return {
        'quick_summary': quick,
        'detailed_plan': detailed
    }


# Quick test
if __name__ == "__main__":
    test_text = "All customers must provide PAN card. Companies shall maintain records."
    reqs = extract_requirements(test_text)
    print(f"✅ Found {len(reqs)} requirements")