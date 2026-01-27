import os
from typing import List, Optional

class InMemoryRetriever:
    """
    Simulates a Vector Database Retriever.
    Reads markdown files from `rag/samples` into memory.
    """
    def __init__(self):
        self.documents = {}
        # Pre-load samples
        base_path = os.path.dirname(os.path.abspath(__file__))
        samples_dir = os.path.join(base_path, "samples")
        
        if os.path.exists(samples_dir):
            for filename in os.listdir(samples_dir):
                if filename.endswith(".md"):
                    with open(os.path.join(samples_dir, filename), "r") as f:
                        self.documents[filename] = f.read()

    def retrieve_protocol(self, query: str, tags: Optional[List[str]] = None) -> str:
        """
        Retrieves relevant protocols based on query semantic overlap or strict tag matching.
        
        FUTURE INTEGRATION:
        -------------------
        This function will eventually connect to Cloud SQL (pgvector).
        Sql:
            SELECT content, 1 - (embedding <=> :query_embedding) as similarity
            FROM documents
            WHERE similarity > 0.7
            ORDER BY similarity DESC
        """
        results = []
        tags = tags or []
        query_terms = query.lower().split()
        
        for name, content in self.documents.items():
            content_lower = content.lower()
            
            # Simple keyword matching heuristic
            score = 0
            if any(t in content_lower for t in tags):
                score += 5
            
            matches = sum(1 for w in query_terms if w in content_lower)
            score += matches
            
            if score > 0:
                results.append((score, f"Source: {name}\n\n{content}"))
                
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        if results:
            return "\n\n---\n\n".join([r[1] for r in results[:2]])
            
        return "No specific Legendary protocols found for this context."

# Singleton instance
retriever = InMemoryRetriever()
