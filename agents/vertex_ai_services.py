import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Vertex AI Embeddings Service - Enhanced with better error handling
"""
import os
from dotenv import load_dotenv
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Force reload environment
load_dotenv(override=True)

# Global flag
VERTEX_AVAILABLE = False
VERTEX_ERROR = None

try:
    import vertexai
    from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
    VERTEX_AVAILABLE = True
    print("   ✅ Vertex AI packages imported")
except ImportError as e:
    VERTEX_ERROR = f"Import failed: {e}"
    print(f"   ⚠️ Vertex AI packages not available: {e}")


class VertexAIEmbeddings:
    """Vertex AI text embeddings for semantic matching"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.model = None
        self.vertex_enabled = False
        self.error_message = None
        
        print(f"\n   🔍 Initializing Vertex AI...")
        print(f"      Project ID: {self.project_id}")
        print(f"      Credentials: {self.creds_path}")
        
        if not VERTEX_AVAILABLE:
            self.error_message = VERTEX_ERROR
            print(f"      ❌ Vertex AI unavailable: {VERTEX_ERROR}")
            return
        
        if not self.project_id:
            self.error_message = "GOOGLE_CLOUD_PROJECT not set"
            print(f"      ❌ {self.error_message}")
            return
        
        if not self.creds_path:
            self.error_message = "GOOGLE_APPLICATION_CREDENTIALS not set"
            print(f"      ❌ {self.error_message}")
            return
        
        if not os.path.exists(self.creds_path):
            self.error_message = f"Credentials file not found: {self.creds_path}"
            print(f"      ❌ {self.error_message}")
            return
        
        try:
            print(f"      Initializing project: {self.project_id}")
            vertexai.init(project=self.project_id, location="us-central1")
            
            print(f"      Loading model: text-embedding-004")
            self.model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            
            self.vertex_enabled = True
            print("      ✅ Vertex AI Embeddings ACTIVE")
            
        except Exception as e:
            self.error_message = str(e)
            print(f"      ❌ Vertex AI initialization failed: {e}")
            print(f"      Will use TF-IDF fallback")
    
    def get_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity"""
        if not self.vertex_enabled or not self.model:
            # Fallback
            from utils.document_utils import calculate_similarity
            return calculate_similarity(text1, text2)
        
        try:
            # Use Vertex AI
            inputs = [
                TextEmbeddingInput(text=text1, task_type="SEMANTIC_SIMILARITY"),
                TextEmbeddingInput(text=text2, task_type="SEMANTIC_SIMILARITY")
            ]
            
            embeddings = self.model.get_embeddings(inputs)
            
            vec1 = np.array(embeddings[0].values).reshape(1, -1)
            vec2 = np.array(embeddings[1].values).reshape(1, -1)
            
            similarity = cosine_similarity(vec1, vec2)[0][0]
            
            # Normalize to 0-1
            similarity = (similarity + 1) / 2
            
            return float(similarity)
            
        except Exception as e:
            print(f"      ⚠️ Vertex AI error during similarity: {e}")
            from utils.document_utils import calculate_similarity
            return calculate_similarity(text1, text2)
    
    def is_enabled(self) -> bool:
        """Check if Vertex AI is enabled"""
        return self.vertex_enabled
    
    def get_status(self) -> dict:
        """Get status information"""
        return {
            'enabled': self.vertex_enabled,
            'error': self.error_message,
            'project': self.project_id
        }


# Test
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Testing VertexAIEmbeddings Class")
    print("=" * 60)
    
    service = VertexAIEmbeddings()
    status = service.get_status()
    
    print(f"\nStatus: {status}")
    
    if service.is_enabled():
        print("\n✅ Testing similarity calculation...")
        score = service.get_similarity(
            "Customer must provide PAN card", 
            "PAN card is mandatory for all customers"
        )
        print(f"   Similarity score: {score:.3f}")
        print("\n✅ Vertex AI service working perfectly!")
    else:
        print(f"\n⚠️ Vertex AI not enabled")
        print(f"   Reason: {status['error']}")
        print("   App will use TF-IDF fallback")