# User Dashboard Manual

This manual explains how to interact with the admin user interface of **AI Gateway Pro**.

---

## 1. Login Screen

Access the dashboard in your browser (`http://localhost:8080/` or `http://localhost:5173/` during dev).
- **Default Username:** `admin`
- **Default Password:** `admin123`
- *Note:* Change your credentials after your first login inside the settings panel.

---

## 2. Dashboard Hub

The main screen aggregates your real-time performance metrics:
- **Active status panels:** Displays active providers, healthy keys counts, total accumulated tokens, and running scheduling states.
- **Request Timelines:** Visualizes hourly throughput of completions.
- **Latency Charts:** Compares average response speed across loaded engine formats.

---

## 3. Managing Providers

To add a new LLM provider:
1. Navigate to the **Providers** tab.
2. Click **Add Provider**.
3. Input the provider name, format plugin (OpenAI, Anthropic, Gemini, Ollama), and base URL.
4. Click **Save**.
5. Select **Test Connection** on the provider card to check routing validity.

---

## 4. Managing API Keys

To add a credential key:
1. Navigate to the **API Keys** tab.
2. Click **Add API Key**.
3. Select the matching Provider.
4. Input the raw key secret token value.
5. Configure the key priority weight (smaller numbers indicate higher priority).
6. Click **Save**.
7. Click the **Eye icon** on the table row to reveal the decrypted preview.

---

## 5. Backups & Restores

To backup or restore the SQLite configuration database:
1. Navigate to the **Settings** tab.
2. Under **Database Snapshots**, click **Create Snapshot** to trigger a manual compression backup.
3. To roll back state, locate a backup in the list and click **Restore**. The backend database engine will re-initialize automatically.
