import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""
ReguLens - AI Compliance Copilot
Powered by Gemini AI + Vertex AI
"""
import streamlit as st
from agents.enhanced_agent import EnhancedComplianceAgent
import plotly.graph_objects as go
import pandas as pd
from utils.pdf_extractor import extract_text_from_pdf, is_pdf

# Page config
st.set_page_config(
    page_title="ReguLens - AI Compliance Copilot",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🔍 ReguLens</h1>', unsafe_allow_html=True)
st.markdown("### AI-Powered Compliance Copilot for CA Firms")
st.markdown("**Analyze compliance gaps in minutes, not hours**")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.info("💡 Using AI-powered analysis with Gemini")
    
    st.markdown("---")
    st.markdown("### 📊 About")
    st.markdown("""
    **ReguLens** helps CA firms:
    - ✅ Analyze regulatory compliance
    - ✅ Identify critical gaps
    - ✅ Generate audit reports
    - ✅ Save 15-20 hours per analysis
    """)
    
    st.markdown("---")
    st.markdown("**Technology Stack:**")
    st.markdown("- 🤖 Gemini AI")
    st.markdown("- ☁️ Vertex AI")
    st.markdown("- 🎨 Streamlit")

# Main area
st.markdown("---")

# Document upload section
st.markdown("## 📤 Upload Documents")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**📜 Regulatory Document**")
    reg_option = st.radio(
        "Choose source:",
        ["Sample RBI Document", "Upload Custom"],
        key="reg_option",
        label_visibility="collapsed"
    )
    
    if reg_option == "Sample RBI Document":
        st.success("✅ Using: RBI AML/KYC Master Direction 2024")
        use_sample_reg = True
        uploaded_reg = None
    else:
        uploaded_reg = st.file_uploader(
            "Upload Regulation (.txt or .pdf)", 
            type=['txt', 'pdf'], 
            key="reg_upload"
        )
        use_sample_reg = False
        
        # Show file info if uploaded
        if uploaded_reg:
            file_type = "PDF" if is_pdf(uploaded_reg.name) else "Text"
            st.info(f"📎 {uploaded_reg.name} ({file_type}, {uploaded_reg.size / 1024:.1f} KB)")

with col2:
    st.markdown("**📋 Internal Policy Document**")
    policy_option = st.radio(
        "Choose source:",
        ["Sample Company Policy", "Upload Custom"],
        key="policy_option",
        label_visibility="collapsed"
    )
    
    if policy_option == "Sample Company Policy":
        st.success("✅ Using: FinTech Company AML Policy 2023")
        use_sample_policy = True
        uploaded_policy = None
    else:
        uploaded_policy = st.file_uploader(
            "Upload Policy (.txt or .pdf)", 
            type=['txt', 'pdf'], 
            key="policy_upload"
        )
        use_sample_policy = False
        
        # Show file info if uploaded
        if uploaded_policy:
            file_type = "PDF" if is_pdf(uploaded_policy.name) else "Text"
            st.info(f"📎 {uploaded_policy.name} ({file_type}, {uploaded_policy.size / 1024:.1f} KB)")

st.markdown("---")

# Analyze button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    analyze_button = st.button(
        "🚀 Analyze Compliance", 
        type="primary", 
        use_container_width=True
    )

if analyze_button:
    st.cache_data.clear()
    # Check if documents are ready
    reg_ready = use_sample_reg or uploaded_reg is not None
    policy_ready = use_sample_policy or uploaded_policy is not None
    
    if not reg_ready or not policy_ready:
        st.error("⚠️ Please select or upload both documents!")
    else:
        with st.spinner("🔄 Running AI-powered compliance analysis..."):
            try:
                # Load regulation document
                reg_pages_data = None
                if use_sample_reg:
                    with open('data/regulations/rbi_regulation.txt', 'r', encoding='utf-8') as f:
                        reg_text = f.read()
                else:
                    if is_pdf(uploaded_reg.name):
                        st.info("📄 Extracting text from PDF with page tracking...")
                        result = extract_text_from_pdf(uploaded_reg, track_pages=True)
                        reg_text = result['text']
                        reg_pages_data = result['pages']
                        st.success(f"✅ Extracted {result['total_pages']} pages")
                    else:
                        reg_text = uploaded_reg.read().decode('utf-8')
                
                # Load policy document with page tracking
                policy_pages_data = None
                if use_sample_policy:
                    with open('data/policies/company_policy.txt', 'r', encoding='utf-8') as f:
                        policy_text = f.read()
                else:
                    if is_pdf(uploaded_policy.name):
                        st.info("📄 Extracting text from PDF with page tracking...")
                        result = extract_text_from_pdf(uploaded_policy, track_pages=True)
                        policy_text = result['text']
                        policy_pages_data = result['pages']
                        st.success(f"✅ Extracted {result['total_pages']} pages")
                    else:
                        policy_text = uploaded_policy.read().decode('utf-8')
                
                # Run analysis with page data
                agent = EnhancedComplianceAgent()
                report = agent.run_full_analysis(
                    reg_text, 
                    policy_text,
                    reg_pages_data=reg_pages_data,
                    policy_pages_data=policy_pages_data
                )
                
                # Store in session
                st.session_state.report = report
                
                st.success("✅ Analysis Complete!")
                
            except FileNotFoundError:
                st.error("❌ Sample documents not found! Please upload custom documents.")
            except Exception as e:
                st.error(f"❌ Error during analysis: {e}")
                st.exception(e)

# Display results
if 'report' in st.session_state:
    st.markdown("---")
    st.markdown("## 📊 Compliance Dashboard")
    
    report = st.session_state.report
    summary = report['summary']
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Compliance Score",
            f"{summary['compliance_score']:.1f}%",
            delta=None
        )
    
    with col2:
        st.metric(
            "Total Requirements",
            summary['total_requirements']
        )
    
    with col3:
        st.metric(
            "Critical Risks",
            summary['critical_risks'],
            delta=None,
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "Missing Controls",
            summary['missing'],
            delta=None,
            delta_color="inverse"
        )
    
    # Executive Summary
    st.markdown("---")
    st.markdown("### 📝 Executive Summary")
    st.info(report['executive_summary'])
    # Charts
    st.markdown("---")
    st.markdown("### 📈 Compliance Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart - Compliance Status
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Compliant', 'Partial', 'Missing'],
            values=[summary['compliant'], summary['partial'], summary['missing']],
            marker=dict(colors=['#28a745', '#ffc107', '#dc3545']),
            hole=0.4
        )])
        fig_pie.update_layout(
            title="Compliance Status Distribution",
            height=400
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Bar chart - Risk Levels
        risk_counts = {
            'CRITICAL': summary['critical_risks'],
            'HIGH': summary['high_risks'],
            'MEDIUM': summary['total_requirements'] - summary['critical_risks'] - summary['high_risks']
        }
        
        fig_bar = go.Figure(data=[go.Bar(
            x=list(risk_counts.keys()),
            y=list(risk_counts.values()),
            marker=dict(color=['#dc3545', '#fd7e14', '#ffc107'])
        )])
        fig_bar.update_layout(
            title="Risk Level Distribution",
            xaxis_title="Risk Level",
            yaxis_title="Count",
            height=400
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Detailed Gap Analysis
    st.markdown("---")
    st.markdown("### 🎯 Detailed Gap Analysis")
    
    # Filter controls
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_status = st.multiselect(
            "Filter by Status:",
            ['MISSING', 'PARTIAL', 'COMPLIANT'],
            default=['MISSING', 'PARTIAL']
        )
    with col2:
        sort_by = st.selectbox(
            "Sort by:",
            ['Risk Level', 'Match Score', 'Requirement ID']
        )
    
    # Filter gaps
    filtered_gaps = [g for g in report['all_gaps'] if g['gap_status'] in filter_status]
    
    # Sort gaps
    if sort_by == 'Risk Level':
        filtered_gaps = sorted(
            filtered_gaps,
            key=lambda x: (['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].index(x['risk_level']))
        )
    elif sort_by == 'Match Score':
        filtered_gaps = sorted(filtered_gaps, key=lambda x: x['match_score'])
    
    # Display gaps
    st.markdown(f"**Showing {len(filtered_gaps)} gaps**")
    
    for i, gap in enumerate(filtered_gaps[:10]):  # Show top 10
        # Color code by risk
        if gap['risk_level'] == 'CRITICAL':
            badge_color = '🔴'
        elif gap['risk_level'] == 'HIGH':
            badge_color = '🟠'
        elif gap['risk_level'] == 'MEDIUM':
            badge_color = '🟡'
        else:
            badge_color = '🟢'
        
        with st.expander(
            f"{badge_color} **{gap['risk_level']}** - {gap['requirement_text'][:80]}...",
            expanded=(i < 3)  # Expand first 3
        ):
            st.markdown(f"**Requirement ID:** `{gap['requirement_id']}`")
            st.markdown(f"**Criticality:** {gap['requirement_criticality']}")
            st.markdown(f"**Gap Status:** {gap['gap_status']}")
            st.markdown(f"**Match Score:** {gap['match_score']:.0%}")
            
            st.markdown("---")
            st.markdown("**📋 Regulatory Requirement:**")
            st.info(gap['requirement_text'])
            
            if gap['matched_control']:
                st.markdown("**✅ Matched Policy Control:**")
                st.success(gap['matched_control'])
            else:
                st.warning("❌ No matching policy control found")
            
            st.markdown("---")
            
            # TIER 1: Quick Summary (Collapsible, shown by default)
            st.markdown("### 📌 Quick Action Summary")
            st.markdown("*For executives and decision-makers*")
            
            quick_summary = gap.get('quick_summary', gap.get('recommendation', 'No summary available'))
            
            # Display with appropriate color based on severity
            if '🔴 CRITICAL' in quick_summary or 'CRITICAL' in quick_summary:
                st.error(quick_summary)
            elif '🟠' in quick_summary or 'HIGH' in quick_summary or 'ENHANCE' in quick_summary:
                st.warning(quick_summary)
            elif '🟡' in quick_summary or 'UPDATE' in quick_summary:
                st.info(quick_summary)
            else:
                st.success(quick_summary)
            
            # TIER 2: Detailed Remediation Plan (Expandable)
            with st.expander("📋 **Detailed Remediation Plan** *(For compliance officers)*", expanded=False):
                detailed_plan = gap.get('detailed_plan', gap.get('recommendation', 'No detailed plan available'))
                
                st.markdown(detailed_plan)
                
                # Add copy button for suggested policy wording if present
                if "**SUGGESTED POLICY LANGUAGE:**" in detailed_plan or "**SUGGESTED POLICY WORDING:**" in detailed_plan:
                    import re
                    match = re.search(r'\*\*SUGGESTED POLICY (?:LANGUAGE|WORDING):\*\*\s*\n(.*?)(?:\n\*\*|$)', 
                                     detailed_plan, re.DOTALL)
                    if match:
                        suggested_text = match.group(1).strip()
                        st.markdown("---")
                        st.markdown("#### 📝 Copy-Paste Ready Policy Text:")
                        st.code(suggested_text, language=None)
                        st.caption("↑ Copy this text directly into your policy document")
    
    # Export section
    st.markdown("---")
    st.markdown("### 📥 Export Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export as CSV
        df = pd.DataFrame(report['all_gaps'])
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Report (CSV)",
            data=csv,
            file_name="regulens_compliance_report.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Export summary as text
        summary_text = f"""
REGULENS COMPLIANCE REPORT
==========================

Compliance Score: {summary['compliance_score']:.1f}%

Summary:
- Total Requirements: {summary['total_requirements']}
- Compliant: {summary['compliant']}
- Partial: {summary['partial']}
- Missing: {summary['missing']}
- Critical Risks: {summary['critical_risks']}
- High Risks: {summary['high_risks']}

Executive Summary:
{report['executive_summary']}

Generated by ReguLens - AI Compliance Copilot
"""
        st.download_button(
            label="📥 Download Summary (TXT)",
            data=summary_text,
            file_name="regulens_summary.txt",
            mime="text/plain",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>ReguLens</strong> - Built with ❤️ for CA Firms</p>
    <p>Powered by Google Gemini AI & Vertex AI | Hackathon Processing Unit</p>
</div>
""", unsafe_allow_html=True)