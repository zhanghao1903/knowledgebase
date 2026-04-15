from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "知识库系统 / Knowledge Base"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = "postgresql+asyncpg://kb_user:kb_password@localhost:5432/knowledgebase"

    STORAGE_DIR: str = "./storage"

    # Embedding config
    EMBEDDING_API_URL: str = "http://localhost:8080/v1/embeddings"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536

    # LLM config
    LLM_API_URL: str = "http://localhost:8080/v1/chat/completions"
    LLM_MODEL: str = "gpt-3.5-turbo"

    OPENAI_API_KEY: str = "sk-placeholder"

    # Chunk config
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Retrieval config
    RETRIEVAL_TOP_K: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
