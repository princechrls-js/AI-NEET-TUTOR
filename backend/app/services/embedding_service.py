import os
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core.logger import get_logger

# Disable tokenizer parallelism to prevent multiprocessing crashes on Windows
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

logger = get_logger(__name__)

_embedding_model = None

def _get_model() -> SentenceTransformer:
    """Lazily loads the embedding model on first use."""
    global _embedding_model
    if _embedding_model is None:
        model_name = settings.EMBEDDING_MODEL
        logger.info(f"Loading embedding model: {model_name}")
        try:
            # Using an absolute project-local cache path to avoid Windows Errno 22 issues with spaces in user profile paths.
            cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".hf_cache"))
            os.makedirs(cache_dir, exist_ok=True)
            _embedding_model = SentenceTransformer(model_name, cache_folder=cache_dir)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Could not load embedding model '{model_name}': {e}") from e
    return _embedding_model

def get_embedding(text: str) -> list[float]:
    """
    Returns the vector embedding for a single string.
    """
    return _get_model().encode(text).tolist()

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Returns vector embeddings for a list of strings.
    """
    return _get_model().encode(texts).tolist()
