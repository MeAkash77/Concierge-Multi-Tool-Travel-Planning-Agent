import time
import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-01-3e01eedce187"
LOCATION = "us-central1"
GCS_PATH = "gs://smart-travel-concierge-media-qwiklabs-gcp-01-3e01eedce187/rag/pg49513.txt"

PARSING_PROMPT = (
    "Extract the individual useful facts, plant descriptions, and herbal remedies described in this text. "
    "Ignore and omit all metadata, license boilerplate, and headers. "
    "Output clean, self-contained prose."
)

print(f"Initializing Vertex AI for project {PROJECT_ID} in {LOCATION}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# 1. Switch region RAG managed DB to serverless mode
cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
print("Setting RAG Engine Config to Serverless mode...")
rag.update_rag_engine_config(
    rag_engine_config=rag.RagEngineConfig(
        name=cfg,
        rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
    )
)

# 2. Create the corpus
print("Creating serverless RAG corpus...")
corpus = rag.create_corpus(
    display_name="smart-travel-gutenberg-corpus",
    embedding_model_config=rag.EmbeddingModelConfig(
        publisher_model="publishers/google/models/text-embedding-005"
    ),
)
print(f"✅ Created Corpus: {corpus.name}")

# 3. Import + parse + chunk + embed
print(f"Importing and indexing file {GCS_PATH}...")
resp = rag.import_files(
    corpus_name=corpus.name,
    paths=[GCS_PATH],
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
    ),
    llm_parser=rag.LlmParserConfig(
        model_name="gemini-2.5-flash",
        custom_parsing_prompt=PARSING_PROMPT,
    ),
)
print(f"✅ Imported files count: {getattr(resp, 'imported_rag_files_count', 'done')}")

print("\nWaiting 10 seconds for indexing...")
time.sleep(10)

print("\nTesting retrieval query...")
try:
    retrieval_resp = rag.retrieval_query(
        text="What are the medicinal uses of peppermint or mint?",
        rag_resources=[rag.RagResource(rag_corpus=corpus.name)],
        rag_retrieval_config=rag.RagRetrievalConfig(top_k=3),
    )
    print("Retrieval results:")
    contexts = getattr(retrieval_resp.contexts, "contexts", [])
    for idx, c in enumerate(contexts):
        print(f"\n--- Context {idx+1} ---")
        print(c.text[:300])
except Exception as e:
        print(f"Retrieval test error: {e}")

print(f"\nFINAL_CORPUS_NAME={corpus.name}")
