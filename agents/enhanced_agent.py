# """
# Enhanced Compliance Agent with Gemini + Vertex AI
# """
# import os
# from dotenv import load_dotenv
# from google import genai
# from utils.document_utils import (
#     extract_requirements, 
#     calculate_similarity, 
#     categorize_risk,
#     generate_recommendation
# )

# load_dotenv()


# class EnhancedComplianceAgent:
#     """
#     Enhanced agent using Gemini AI for analysis
#     """
    
#     def __init__(self):
#         """Initialize with Gemini"""
#         self.gemini_key = os.getenv('GEMINI_API_KEY')
#         self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
#         # Initialize Gemini
#         if self.gemini_key:
#             self.gemini_client = genai.Client(api_key=self.gemini_key)
#             print("✅ Gemini AI initialized")
#         else:
#             self.gemini_client = None
#             print("⚠️ Running without Gemini (rule-based mode)")
    
#     def analyze_regulation(self, text: str) -> dict:
#         """Extract requirements from regulation"""
#         print("\n🔍 [Step 1] Analyzing Regulatory Document...")
        
#         requirements = extract_requirements(text)
        
#         print(f"   ✅ Extracted {len(requirements)} requirements")
        
#         return {
#             'requirements': requirements,
#             'total': len(requirements)
#         }
    
#     def analyze_policy(self, text: str) -> dict:
#         """Extract controls from policy"""
#         print("\n📋 [Step 2] Analyzing Internal Policy...")
        
#         controls = extract_requirements(text)
        
#         print(f"   ✅ Extracted {len(controls)} controls")
        
#         return {
#             'controls': controls,
#             'total': len(controls)
#         }
    
#     def map_gaps(self, regulation_result: dict, policy_result: dict) -> list:
#         """Map regulatory requirements to policy controls"""
#         print("\n🔗 [Step 3] Mapping Compliance Gaps...")
        
#         requirements = regulation_result['requirements']
#         controls = policy_result['controls']
        
#         # Try to use Vertex AI for better matching
#         try:
#             from agents.vertex_ai_service import VertexAIEmbeddings
#             vertex_service = VertexAIEmbeddings()
#             use_vertex = vertex_service.is_enabled()
            
#             if use_vertex:
#                 print("   Using Vertex AI embeddings for semantic matching...")
#             else:
#                 print("   Using TF-IDF similarity (Vertex AI unavailable)...")
#         except:
#             print("   Using TF-IDF similarity (fallback mode)...")
#             vertex_service = None
#             use_vertex = False
        
#         gaps = []
        
#         for req in requirements:
#             # Find best matching control
#             best_score = 0.0
#             best_match = None
            
#             for ctrl in controls:
#                 # Use Vertex AI if available, otherwise fallback
#                 if use_vertex and vertex_service:
#                     score = vertex_service.get_similarity(req['text'], ctrl['text'])
#                 else:
#                     score = calculate_similarity(req['text'], ctrl['text'])
                
#                 if score > best_score:
#                     best_score = score
#                     best_match = ctrl
            
#             # Determine gap status (higher thresholds for Vertex AI)
#             if use_vertex:
#                 # Vertex AI is more accurate, can use higher thresholds
#                 if best_score >= 0.7:
#                     gap_status = 'COMPLIANT'
#                 elif best_score >= 0.4:
#                     gap_status = 'PARTIAL'
#                 else:
#                     gap_status = 'MISSING'
#             else:
#                 # TF-IDF needs lower thresholds
#                 if best_score >= 0.6:
#                     gap_status = 'COMPLIANT'
#                 elif best_score >= 0.3:
#                     gap_status = 'PARTIAL'
#                 else:
#                     gap_status = 'MISSING'
            
#             # Calculate risk
#             risk_level = categorize_risk(gap_status, req['criticality'])
            
#             # Generate recommendation
#             recommendation = generate_recommendation(gap_status, req['text'])
            
#             gaps.append({
#                 'requirement_id': req['id'],
#                 'requirement_text': req['text'],
#                 'requirement_criticality': req['criticality'],
#                 'matched_control': best_match['text'] if best_match else None,
#                 'match_score': round(best_score, 2),
#                 'gap_status': gap_status,
#                 'risk_level': risk_level,
#                 'recommendation': recommendation,
#                 'matching_method': 'vertex-ai-embeddings' if use_vertex else 'tfidf-fallback'
#             })
        
#         print(f"   ✅ Analyzed {len(gaps)} requirement-control pairs")
#         if use_vertex:
#             print("   ✅ Used Vertex AI embeddings for enhanced accuracy")
        
#         return gaps
    
#     def generate_report(self, gaps: list) -> dict:
#         """Generate compliance report with Gemini-powered summary"""
#         print("\n📊 [Step 4] Generating Compliance Report...")
        
#         # Calculate statistics
#         total = len(gaps)
#         compliant = len([g for g in gaps if g['gap_status'] == 'COMPLIANT'])
#         partial = len([g for g in gaps if g['gap_status'] == 'PARTIAL'])
#         missing = len([g for g in gaps if g['gap_status'] == 'MISSING'])
        
#         critical_risks = len([g for g in gaps if g['risk_level'] == 'CRITICAL'])
#         high_risks = len([g for g in gaps if g['risk_level'] == 'HIGH'])
        
#         score = (compliant + partial * 0.5) / total * 100 if total > 0 else 0
        
#         # Generate executive summary with Gemini
#         executive_summary = self._generate_executive_summary(
#             score, total, compliant, partial, missing, critical_risks, high_risks, gaps
#         )
        
#         print(f"   ✅ Compliance Score: {score:.1f}%")
#         print(f"   ✅ Critical Risks: {critical_risks}")

#         vertex_used = any(
#             g.get('matching_method') == 'vertex-ai-embeddings' 
#             for g in gaps
#         ) if gaps else False
        
#         return {
#             'summary': {
#                 'total_requirements': total,
#                 'compliant': compliant,
#                 'partial': partial,
#                 'missing': missing,
#                 'compliance_score': round(score, 1),
#                 'critical_risks': critical_risks,
#                 'high_risks': high_risks
#             },
#             'executive_summary': executive_summary,
#             'all_gaps': gaps,
#             'technology_used': {
#                 'gemini_ai': self.gemini_client is not None,
#                 'vertex_ai': vertex_used  # Will add later
#             }
#         }
    
#     def _generate_executive_summary(self, score, total, compliant, partial, 
#                                     missing, critical, high, gaps):
#         """Generate AI-powered executive summary"""
        
#         if not self.gemini_client:
#             # Fallback template
#             return f"Compliance score of {score:.1f}% indicates {'strong' if score >= 80 else 'moderate' if score >= 60 else 'weak'} compliance. Out of {total} requirements, {missing} are missing and {critical} pose critical risks requiring immediate action."
        
#         try:
#             # Get top 3 critical gaps
#             priority_gaps = sorted(
#                 [g for g in gaps if g['gap_status'] in ['MISSING', 'PARTIAL']],
#                 key=lambda x: (x['risk_level'] == 'CRITICAL', x['risk_level'] == 'HIGH'),
#                 reverse=True
#             )[:3]
            
#             gap_descriptions = "\n".join([
#                 f"- {g['requirement_text'][:100]}" 
#                 for g in priority_gaps
#             ])
            
#             prompt = f"""Generate a professional executive summary for a compliance report.

#                         Compliance Score: {score:.1f}%
#                         Total Requirements: {total}
#                         Compliant: {compliant} | Partial: {partial} | Missing: {missing}
#                         Critical Risks: {critical} | High Risks: {high}

#                         Top Priority Gaps:
#                         {gap_descriptions}

#                         Write 3-4 concise sentences for CA firm executives:
#                         1. Overall compliance assessment
#                         2. Key risk areas
#                         3. Recommended actions

#                         Be direct and professional."""

#             response = self.gemini_client.models.generate_content(
#                 model='gemini-2.0-flash-exp',
#                 contents=prompt
#             )
            
#             print("   ✅ Gemini-generated executive summary")
#             return response.text.strip()
            
#         except Exception as e:
#             print(f"   ⚠️ Gemini summary failed: {e}")
#             return f"Compliance score of {score:.1f}% with {critical} critical risks requiring immediate attention."
    
#     def run_full_analysis(self, regulation_text: str, policy_text: str) -> dict:
#         """
#         Execute complete compliance analysis
        
#         Args:
#             regulation_text: Regulatory document
#             policy_text: Internal policy document
        
#         Returns:
#             Complete compliance report
#         """
#         print("\n" + "="*60)
#         print("🚀 ReguLens Enhanced Compliance Analysis")
#         print("   Powered by: Gemini AI")
#         print("="*60)
        
#         # Step 1: Analyze regulation
#         reg_result = self.analyze_regulation(regulation_text)
        
#         # Step 2: Analyze policy
#         policy_result = self.analyze_policy(policy_text)
        
#         # Step 3: Map gaps
#         gaps = self.map_gaps(reg_result, policy_result)
        
#         # Step 4: Generate report
#         report = self.generate_report(gaps)
        
#         print("\n" + "="*60)
#         print("✨ Analysis Complete!")
#         print("="*60 + "\n")
        
#         return report


# # Quick test
# if __name__ == "__main__":
#     agent = EnhancedComplianceAgent()
#     print("✅ Enhanced agent initialized!")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Enhanced Compliance Agent with Gemini + Vertex AI
"""
import os
from dotenv import load_dotenv
from google import genai
from utils.document_utils import (
    extract_requirements,
    calculate_similarity,  # TF-IDF fallback
    categorize_risk,
    generate_recommendation
)

# Import Vertex AI service with multiple path attempts
VERTEX_SERVICE_AVAILABLE = False
VertexAIEmbeddings = None  # ← ADD THIS LINE

load_dotenv()


class EnhancedComplianceAgent:
    """
    Enhanced agent using Gemini AI + Vertex AI
    """
    
    def __init__(self):
        """Initialize with Gemini + Vertex AI"""
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        # Initialize Gemini
        if self.gemini_key:
            self.gemini_client = genai.Client(api_key=self.gemini_key)
            print("✅ Gemini AI initialized")
        else:
            self.gemini_client = None
            print("⚠️ Running without Gemini (rule-based mode)")
        
        
        if VERTEX_SERVICE_AVAILABLE and VertexAIEmbeddings is not None:
            print("🔍 DEBUG: Attempting to create VertexAIEmbeddings instance...")
            try:
                self.vertex_service = VertexAIEmbeddings()
                self.vertex_enabled = self.vertex_service.is_enabled()
                print(f"🔍 DEBUG: vertex_service.is_enabled() = {self.vertex_enabled}")
                
                if self.vertex_enabled:
                    print("✅ Vertex AI fully initialized and enabled")
                else:
                    print("⚠️ Vertex AI service created but not enabled")
                    status = self.vertex_service.get_status()
                    print(f"   Status: {status}")
            except Exception as e:
                print(f"❌ Error creating Vertex AI service: {e}")
                import traceback
                traceback.print_exc()
                self.vertex_service = None
                self.vertex_enabled = False
        else:
            self.vertex_service = None
            self.vertex_enabled = False
            print(f"⚠️ Vertex AI service not available")
            print(f"   VERTEX_SERVICE_AVAILABLE: {VERTEX_SERVICE_AVAILABLE}")
            print(f"   VertexAIEmbeddings: {VertexAIEmbeddings}")
        
        # Initialize Enhanced Similarity (placeholder for future)
        self.enhanced_similarity = False
        self.similarity_service = None
        print(f"🔍 Semantic Matching: TF-IDF")
    
    def analyze_regulation(self, text: str, pages_data: list = None) -> dict:
        """Extract requirements from regulation"""
        print("\n🔍 [Step 1] Analyzing Regulatory Document...")
        
        requirements = extract_requirements(
            text, 
            pages_data=pages_data,
            document_name="Regulation"
        )
        
        print(f"   ✅ Extracted {len(requirements)} requirements")
        
        return {
            'requirements': requirements,
            'total': len(requirements),
            'pages_data': pages_data
        }
    
    def analyze_policy(self, text: str, pages_data: list = None) -> dict:
        """Extract controls from policy"""
        print("\n📋 [Step 2] Analyzing Internal Policy...")
        
        controls = extract_requirements(
            text,
            pages_data=pages_data,
            document_name="Internal Policy"
        )
        
        print(f"   ✅ Extracted {len(controls)} controls")
        
        return {
            'controls': controls,
            'total': len(controls),
            'pages_data': pages_data
        }
    
    def map_gaps(self, regulation_result: dict, policy_result: dict) -> list:
        """Map regulatory requirements to policy controls"""
        print("\n🔗 [Step 3] Mapping Compliance Gaps...")
        
        requirements = regulation_result['requirements']
        controls = policy_result['controls']
        
        # Determine which similarity method to use
        if self.vertex_enabled:
            print("   Using Vertex AI embeddings for semantic matching...")
            use_vertex = True
        else:
            print("   Using TF-IDF similarity (fallback mode)...")
            use_vertex = False
        
        gaps = []
        
        for req in requirements:
            # Find best matching control
            best_score = 0.0
            best_match = None
            
            for ctrl in controls:
                # Use Vertex AI if enabled, otherwise TF-IDF
                if use_vertex:
                    score = self.vertex_service.get_similarity(req['text'], ctrl['text'])
                else:
                    score = calculate_similarity(req['text'], ctrl['text'])
                
                if score > best_score:
                    best_score = score
                    best_match = ctrl
            
            # Determine gap status (different thresholds for Vertex AI vs TF-IDF)
            if use_vertex:
                # Vertex AI is more accurate, use higher thresholds
                if best_score >= 0.7:
                    gap_status = 'COMPLIANT'
                elif best_score >= 0.4:
                    gap_status = 'PARTIAL'
                else:
                    gap_status = 'MISSING'
            else:
                # TF-IDF needs lower thresholds
                if best_score >= 0.6:
                    gap_status = 'COMPLIANT'
                elif best_score >= 0.3:
                    gap_status = 'PARTIAL'
                else:
                    gap_status = 'MISSING'
            
            # Calculate risk
            risk_level = categorize_risk(gap_status, req['criticality'])
            
            # Generate AI-powered recommendation using Gemini
            # Generate two-tier recommendations
            recommendations = generate_recommendation(
                gap_status=gap_status,
                requirement_text=req['text'],
                matched_control=best_match['text'] if best_match else None,
                match_score=best_score,
                gemini_client=self.gemini_client,
                req_page=req.get('page_number'),
                ctrl_page=best_match.get('page_number') if best_match else None,
                req_doc="Regulation",
                ctrl_doc="Your Policy"
            )

            # Handle both dict (new) and str (old fallback) formats
            if isinstance(recommendations, dict):
                quick_summary = recommendations.get('quick_summary', '')
                detailed_plan = recommendations.get('detailed_plan', '')
            else:
                # Old format fallback
                quick_summary = recommendations
                detailed_plan = recommendations
            
            gaps.append({
                'requirement_id': req['id'],
                'requirement_text': req['text'],
                'requirement_criticality': req['criticality'],
                'matched_control': best_match['text'] if best_match else None,
                'match_score': round(best_score, 2),
                'gap_status': gap_status,
                'risk_level': risk_level,
                'quick_summary': quick_summary,
                'detailed_plan': detailed_plan,
                'matching_method': 'sentence-transformers' if self.enhanced_similarity else 'tfidf'
            })
        
        print(f"   ✅ Analyzed {len(gaps)} requirement-control pairs")
        if use_vertex:
            print("   ✅ Using Vertex AI text-embedding-004 model")
        
        return gaps
    
    def generate_report(self, gaps: list) -> dict:
        """Generate compliance report with Gemini-powered summary"""
        print("\n📊 [Step 4] Generating Compliance Report...")
        
        # Calculate statistics
        total = len(gaps)
        compliant = len([g for g in gaps if g['gap_status'] == 'COMPLIANT'])
        partial = len([g for g in gaps if g['gap_status'] == 'PARTIAL'])
        missing = len([g for g in gaps if g['gap_status'] == 'MISSING'])
        
        critical_risks = len([g for g in gaps if g['risk_level'] == 'CRITICAL'])
        high_risks = len([g for g in gaps if g['risk_level'] == 'HIGH'])
        
        score = (compliant + partial * 0.5) / total * 100 if total > 0 else 0
        
        # Generate executive summary with Gemini
        executive_summary = self._generate_executive_summary(
            score, total, compliant, partial, missing, critical_risks, high_risks, gaps
        )
        
        print(f"   ✅ Compliance Score: {score:.1f}%")
        print(f"   ✅ Critical Risks: {critical_risks}")
        
        # Check if Vertex AI was actually used
        vertex_used = any(
            g.get('matching_method') == 'vertex-ai'
            for g in gaps
        ) if gaps else False
        
        return {
            'summary': {
                'total_requirements': total,
                'compliant': compliant,
                'partial': partial,
                'missing': missing,
                'compliance_score': round(score, 1),
                'critical_risks': critical_risks,
                'high_risks': high_risks
            },
            'executive_summary': executive_summary,
            'all_gaps': gaps,
            'technology_used': {
                'gemini_ai': self.gemini_client is not None,
                'vertex_ai': vertex_used,
                'matching_engine': 'Vertex AI text-embedding-004' if vertex_used else 'TF-IDF'
            }
        }
    
    def _generate_executive_summary(self, score, total, compliant, partial, 
                                    missing, critical, high, gaps):
        """Generate AI-powered executive summary"""
        
        if not self.gemini_client:
            # Fallback template
            return f"Compliance score of {score:.1f}% indicates {'strong' if score >= 80 else 'moderate' if score >= 60 else 'weak'} compliance. Out of {total} requirements, {missing} are missing and {critical} pose critical risks requiring immediate action."
        
        try:
            # Get top 3 critical gaps
            priority_gaps = sorted(
                [g for g in gaps if g['gap_status'] in ['MISSING', 'PARTIAL']],
                key=lambda x: (x['risk_level'] == 'CRITICAL', x['risk_level'] == 'HIGH'),
                reverse=True
            )[:3]
            
            gap_descriptions = "\n".join([
                f"- {g['requirement_text'][:100]}" 
                for g in priority_gaps
            ])
            
            prompt = f"""Generate a professional executive summary for a compliance report.

Compliance Score: {score:.1f}%
Total Requirements: {total}
Compliant: {compliant} | Partial: {partial} | Missing: {missing}
Critical Risks: {critical} | High Risks: {high}

Top Priority Gaps:
{gap_descriptions}

Write 3-4 concise sentences for CA firm executives:
1. Overall compliance assessment
2. Key risk areas
3. Recommended actions

Be direct and professional."""

            response = self.gemini_client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            
            print("   ✅ Gemini-generated executive summary")
            return response.text.strip()
            
        except Exception as e:
            print(f"   ⚠️ Gemini summary failed: {e}")
            return f"Compliance score of {score:.1f}% with {critical} critical risks requiring immediate attention."
    
    def run_full_analysis(self, regulation_text: str, policy_text: str,
                     reg_pages_data: list = None, policy_pages_data: list = None) -> dict:
        """Execute complete compliance analysis"""
        print("\n" + "="*60)
        print("🚀 ReguLens Enhanced Compliance Analysis")
        print("   Powered by: Gemini AI")
        print("="*60)
        
        # Step 1: Analyze regulation
        reg_result = self.analyze_regulation(regulation_text, reg_pages_data)
        
        # Step 2: Analyze policy
        policy_result = self.analyze_policy(policy_text, policy_pages_data)
        
        # Step 3: Map gaps
        gaps = self.map_gaps(reg_result, policy_result)
        
        # Step 4: Generate report
        report = self.generate_report(gaps)
        
        print("\n" + "="*60)
        print("✨ Analysis Complete!")
        print("="*60 + "\n")
        
        return report


# Quick test
if __name__ == "__main__":
    agent = EnhancedComplianceAgent()
    print("✅ Enhanced agent initialized!")