from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure OpenAI
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_api_version: str = "2024-08-01-preview"

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # OCR
    ocr_provider: str = "azure"
    ocr_model: str = "gpt-4o"
    ocr_dpi: int = 200
    pdf_engine: str = "mistral-ocr"

    # Limits
    max_file_size_mb: int = 20
    max_files_per_job: int = 50
    temp_dir: str = "/tmp/ocr_jobs"
    result_ttl_seconds: int = 3600

    # Output path security
    allowed_output_base_dirs: str = ""
    create_output_folder_if_missing: bool = False

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def temp_path(self) -> Path:
        return Path(self.temp_dir)

    @property
    def allowed_base_dirs(self) -> list[Path]:
        if not self.allowed_output_base_dirs.strip():
            return []
        return [Path(p.strip()).resolve() for p in self.allowed_output_base_dirs.split(",") if p.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def azure_endpoint_normalized(self) -> str:
        endpoint = self.azure_openai_endpoint
        if "/api/projects/" in endpoint:
            endpoint = endpoint.split("/api/projects/")[0]
        return endpoint

    @property
    def effective_model(self) -> str:
        if self.ocr_provider == "azure":
            return self.azure_openai_deployment_name or self.ocr_model
        return self.ocr_model


settings = Settings()
