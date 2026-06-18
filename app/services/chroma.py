import os
import chromadb
from langchain_chroma import Chroma
from langchain_pinecone import PineconeVectorStore
import google.generativeai as genai
from app.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# 1. Setup the Gemini Embedding Model
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

genai.configure(api_key=GEMINI_API_KEY)

class NativeGeminiEmbeddings:
    """A custom bridge that bypasses LangChain to use Google's native API directly."""
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Used by Pinecone when you save new house rules."""
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=texts,
            task_type="retrieval_document", # Optimizes the vector for storage
            output_dimensionality=1024      # Natively requests the 1024 Matryoshka slice
        )
        # Google's SDK returns a dictionary; Pinecone expects a raw list of lists
        return result['embedding']

    def embed_query(self, text: str) -> list[float]:
        """Used by Pinecone when searching the diff text."""
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_query",    # Optimizes the vector for searching
            output_dimensionality=1024
        )
        return result['embedding']

# Initialize our custom native bridge
embeddings = NativeGeminiEmbeddings()

# 2. Dynamic Vector Store Router
def get_vector_store(repo_name: str):
    """Dynamically routes to a repo-specific isolated partition."""
    
    if ENVIRONMENT == "production":
        # Pinecone natively isolates data using the 'namespace' parameter
        return PineconeVectorStore(
            index_name="code-review-copilot", 
            embedding=embeddings,
            namespace=repo_name # <-- DATA ISOLATION ACHIEVED
        )
    else:
        # ChromaDB isolates data using separate 'collections'
        # Chroma requires alphanumeric collection names without slashes
        safe_repo_name = repo_name.replace("/", "_").replace("-", "_")
        chroma_client = chromadb.HttpClient(host="chromadb", port=8000)
        
        return Chroma(
            client=chroma_client,
            collection_name=safe_repo_name, # <-- DATA ISOLATION ACHIEVED
            embedding_function=embeddings
        )

def learn_convention(rule: str, repo_name: str):
    """Embeds and saves a new coding rule to the repo's specific namespace.
    
    Args:
        rule: Coding convention to store
        repo_name: Repository name for isolation
        
    Returns:
        True if successful
    """
    logger.info(
        "Learning new coding convention",
        extra={
            "repo_name": repo_name,
            "rule_length": len(rule),
            "environment": ENVIRONMENT
        }
    )
    
    try:
        vector_store = get_vector_store(repo_name)
        vector_store.add_texts(texts=[rule])
        
        logger.info(
            "Coding convention learned successfully",
            extra={
                "repo_name": repo_name,
                "environment": ENVIRONMENT
            }
        )
        
        return True
        
    except Exception as e:
        logger.error(
            "Failed to learn coding convention",
            exc_info=True,
            extra={
                "repo_name": repo_name,
                "rule_length": len(rule),
                "environment": ENVIRONMENT
            }
        )
        raise

def retrieve_relevant_rules(diff_text: str, repo_name: str) -> str:
    """Finds the top 3 most relevant rules exclusively for this repo.
    
    Args:
        diff_text: PR diff to search against
        repo_name: Repository name for isolation
        
    Returns:
        Formatted string of relevant rules or "None"
    """
    logger.debug(
        "Retrieving relevant coding rules",
        extra={
            "repo_name": repo_name,
            "diff_length": len(diff_text),
            "environment": ENVIRONMENT,
            "vector_store": "Pinecone" if ENVIRONMENT == "production" else "ChromaDB"
        }
    )
    
    try:
        vector_store = get_vector_store(repo_name)
        results = vector_store.similarity_search(query=diff_text, k=3)
        
        if not results:
            logger.info(
                "No relevant rules found in vector store",
                extra={
                    "repo_name": repo_name,
                    "environment": ENVIRONMENT
                }
            )
            return "None"
        
        logger.info(
            "Retrieved relevant coding rules",
            extra={
                "repo_name": repo_name,
                "rule_count": len(results),
                "environment": ENVIRONMENT,
                "vector_store": "Pinecone" if ENVIRONMENT == "production" else "ChromaDB"
            }
        )
        
        return "\n".join([f"- {doc.page_content}" for doc in results])
        
    except Exception as e:
        logger.error(
            "Error retrieving rules from vector store",
            exc_info=True,
            extra={
                "repo_name": repo_name,
                "diff_length": len(diff_text),
                "environment": ENVIRONMENT,
                "vector_store": "Pinecone" if ENVIRONMENT == "production" else "ChromaDB"
            }
        )
        return "None"