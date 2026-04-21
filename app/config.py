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

    # --- URL ingestion (single-page fetching) ---
    # Timeout covers the full request (connect + read). 20s comfortably fits
    # most global technical blogs/docs while still failing fast on dead hosts.
    URL_FETCH_TIMEOUT_SEC: float = 20.0
    # 10 MiB is enough for >99% of HTML pages (images/fonts are not downloaded);
    # prevents memory blow-up from huge or malicious responses.
    URL_FETCH_MAX_BYTES: int = 10 * 1024 * 1024
    # Browsers follow up to ~20; 5 is plenty for legitimate redirects and
    # minimizes SSRF-via-redirect surface.
    URL_FETCH_MAX_REDIRECTS: int = 5
    # Polite, identifiable UA so site owners can contact/block us if needed.
    URL_FETCH_USER_AGENT: str = "KnowledgeBaseBot/0.1 (+https://github.com/)"
    # Comma-separated whitelist. Parsed lazily into a set where needed.
    URL_FETCH_ALLOWED_CONTENT_TYPES: str = (
        "text/html,application/xhtml+xml,text/plain"
    )
    # Must remain False in production to prevent SSRF into internal networks.
    # Tests flip this on via monkeypatch when mocking httpx.
    URL_FETCH_ALLOW_PRIVATE_NETWORK: bool = False

    @property
    def url_fetch_allowed_content_types(self) -> set[str]:
        return {
            ct.strip().lower()
            for ct in self.URL_FETCH_ALLOWED_CONTENT_TYPES.split(",")
            if ct.strip()
        }

    @property
    def effective_embedding_api_key(self) -> str:
        """Use dedicated embedding key if set, otherwise fall back to OpenRouter key."""
        return self.EMBEDDING_API_KEY or self.OPENROUTER_API_KEY

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
