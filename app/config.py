from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "知识库系统 / Knowledge Base"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = "postgresql+asyncpg://kb_user:kb_password@localhost:5432/knowledgebase"

    STORAGE_DIR: str = "./storage"

    # --- OpenRouter (LLM) ---
    OPENROUTER_API_KEY: str = "sk-placeholder"
    LLM_API_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    LLM_MODEL: str = "openai/gpt-4o-mini"

    # --- Embedding (separate provider — OpenRouter does not serve embeddings) ---
    EMBEDDING_API_KEY: str = ""  # falls back to OPENROUTER_API_KEY if empty
    EMBEDDING_API_URL: str = "https://api.openai.com/v1/embeddings"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536

    # Chunk config
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Retrieval config
    RETRIEVAL_TOP_K: int = 5

    @property
    def effective_embedding_api_key(self) -> str:
        """Use dedicated embedding key if set, otherwise fall back to OpenRouter key."""
        return self.EMBEDDING_API_KEY or self.OPENROUTER_API_KEY

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
