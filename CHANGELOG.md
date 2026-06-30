# Changelog

All notable changes to the **AI Gateway Pro** project will be documented in this file.

---

## [1.0.0] - 2026-06-30

### Added
- **Core Infrastructure**: SQLModel entities, database migrations, and repository structures.
- **Provider Plugin System**: Built-in support for OpenAI, Gemini, Anthropic, Ollama, DeepSeek, and custom models.
- **API Key Management**: AES-256-GCM encryption at rest with master password validation.
- **Failover & Key Rotation**: Configurable priority, round-robin, least-used, and fastest latency-based rotators.
- **Background Scheduler**: Health checks monitoring, automatic DB snapshots management, and statistics aggregations.
- **Web App Dashboard**: React + TypeScript frontend UI for admin KPI charts, key status management, and backup restores.
- **Desktop System Tray**: Startup registry triggers, single-instance socket locks, and window wrapper.
- **PyInstaller & Inno Setup**: Installer packaging configurations and portable builds support.
- **Comprehensive QA Suite**: Mock provider connections test suites and executable smoke verification tests.
- **Documentation**: Exhaustive architectural plans, installation steps, and API specs under `docs/`.
