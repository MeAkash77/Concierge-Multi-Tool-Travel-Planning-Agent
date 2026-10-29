import vertexai
from vertexai.preview import rag

CORPUS_NAME = "projects/813594678577/locations/us-central1/ragCorpora/3862777862423576576"
PROJECT_ID = "qwiklabs-gcp-01-3e01eedce187"
LOCATION = "us-central1"

def consult_herbal_knowledge(query: str) -> str:
    """Search Culpeper's Complete Herbal RAG corpus and return relevant passages about plants, herbs, remedies, and wellness.

    Args:
        query: What to look up (a plant, herb, ailment, remedy, or health recommendation).
    Returns:
        The matched passages from Culpeper's Complete Herbal corpus, or a note if none found.
    """
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
        contexts = getattr(resp.contexts, "contexts", [])
        passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
        return "\n\n---\n\n".join(passages) or "No relevant passage found in herbal corpus."
    except Exception as e:
        return f"Herbal knowledge retrieval failed: {e}"
