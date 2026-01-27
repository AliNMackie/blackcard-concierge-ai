# RAG and Vision Notes

## RAG (Retrieval Augmented Generation)

### Overview
This system uses a simplified RAG approach for the MVP.
1.  **Source**: "Legendary" Framework documents stored in `backend/rag/samples/*.md`.
2.  **Retriever**: `backend/rag/retriever.py` implements an in-memory search.
3.  **Integration**: The `Biometric Sentry` agent retrieves context when recovery scores are low.

### Current Implementation (MVP)
*   **Storage**: In-memory dictionary.
*   **Search**: Simple keyword + tag overlap score.
*   **Interface**: `retriever.retrieve_protocol(query, tags=[])`

### Production Strategy (Phase 3+)
*   **Vector Database**: Cloud SQL (PostgreSQL) with `pgvector` extension.
*   **Pipeline**:
    1.  Ingest markdown files.
    2.  Chunk textual content.
    3.  Generate Embeddings using `vertexai.language_models.TextEmbeddingModel`.
    4.  Store in `document_embeddings` table.
*   **Query**: Cosine similarity search via SQL.

## Vision Interface

### Overview
Located at `backend/app/vision_interface.py`.
Currently mocks the response of `gemini-3-pro-image-preview`.

### Contract
*   **Input**: Raw bytes (image buffer).
*   **Output**: `GymEquipmentDescription` (TypedDict: `detected_equipment: List[str]`, `confidence: float`).

### Future Integration (Gemini Vision)
We will use the Vertex AI Multimodal SDK.

```python
from vertexai.generative_models import GenerativeModel, Image

model = GenerativeModel("gemini-1.5-pro-vision") # Target: gemini-3-vision
response = model.generate_content(["Describe current gym equipment", Image.load_from_file(path)])
```

### Flow
1.  **Client**: Uploads image to `/events/vision`.
2.  **Concierge**: Routes to `Vision Agent`.
3.  **Vision Agent Node**:
    *   Checks if `image_url` or bytes are present.
    *   Calls `vision_interface.describe_gym_equipment(bytes)`.
    *   Receives structured list of equipment.
    *   Passes list + User Query to LLM for workout generation.
