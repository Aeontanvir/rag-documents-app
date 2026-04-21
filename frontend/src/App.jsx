import { useEffect, useState } from "react";

const defaultApiBase = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;
const API_BASE = import.meta.env.VITE_API_URL ?? defaultApiBase;

async function readJson(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail ?? "Request failed.");
  }
  return payload;
}

function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [question, setQuestion] = useState("");
  const [selectedDocumentId, setSelectedDocumentId] = useState("all");
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [status, setStatus] = useState("Upload documents and start asking questions.");

  useEffect(() => {
    void loadDocuments();
  }, []);

  async function loadDocuments() {
    setLoadingDocuments(true);
    try {
      const data = await readJson(await fetch(`${API_BASE}/documents`));
      setDocuments(data);
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoadingDocuments(false);
    }
  }

  async function handleUpload(event) {
    event.preventDefault();
    if (!selectedFiles.length) {
      setStatus("Choose at least one file to upload.");
      return;
    }

    setUploading(true);
    setStatus("Uploading and chunking documents...");
    try {
      const formData = new FormData();
      selectedFiles.forEach((file) => formData.append("files", file));

      const data = await readJson(
        await fetch(`${API_BASE}/documents/upload`, {
          method: "POST",
          body: formData,
        }),
      );

      setSelectedFiles([]);
      setStatus(data.items.map((item) => item.message).join(" "));
      await loadDocuments();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleAsk(event) {
    event.preventDefault();
    if (!question.trim()) {
      setStatus("Enter a prompt before querying.");
      return;
    }

    setAsking(true);
    setStatus("Searching the vector store and generating an answer...");
    try {
      const payload = {
        question,
        document_ids: selectedDocumentId === "all" ? null : [selectedDocumentId],
      };

      const data = await readJson(
        await fetch(`${API_BASE}/chat/query`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }),
      );

      setAnswer(data.answer);
      setSources(data.sources);
      setStatus("Answer ready.");
    } catch (error) {
      setAnswer("");
      setSources([]);
      setStatus(error.message);
    } finally {
      setAsking(false);
    }
  }

  async function handleDelete(documentId) {
    setStatus("Removing document from the collection...");
    try {
      await readJson(
        await fetch(`${API_BASE}/documents/${documentId}`, {
          method: "DELETE",
        }),
      );

      if (selectedDocumentId === documentId) {
        setSelectedDocumentId("all");
      }
      await loadDocuments();
      setStatus("Document removed.");
    } catch (error) {
      setStatus(error.message);
    }
  }

  return (
    <div className="app-shell">
      <div className="glow glow-one" />
      <div className="glow glow-two" />

      <header className="hero">
        <p className="eyebrow">FastAPI + LangChain + Chroma</p>
        <h1>Doc AI Workspace</h1>
        <p className="hero-copy">
          Upload PDFs, Word files, text, markdown, and more. The backend chunks
          them into retrieval-friendly context and answers questions with RAG.
        </p>
      </header>

      <main className="grid">
        <section className="panel">
          <h2>Ingest Documents</h2>
          <form onSubmit={handleUpload} className="stack">
            <label className="upload-zone">
              <span>Drop files here or browse from disk</span>
              <input
                type="file"
                multiple
                onChange={(event) =>
                  setSelectedFiles(Array.from(event.target.files ?? []))
                }
              />
            </label>

            <div className="file-list">
              {selectedFiles.length ? (
                selectedFiles.map((file) => (
                  <div key={`${file.name}-${file.size}`} className="pill">
                    {file.name}
                  </div>
                ))
              ) : (
                <p className="muted">No files selected yet.</p>
              )}
            </div>

            <button type="submit" disabled={uploading}>
              {uploading ? "Uploading..." : "Upload and Index"}
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Knowledge Base</h2>
            <button
              type="button"
              className="ghost-button"
              onClick={() => void loadDocuments()}
              disabled={loadingDocuments}
            >
              Refresh
            </button>
          </div>

          <div className="document-list">
            {documents.length ? (
              documents.map((document) => (
                <article key={document.document_id} className="document-card">
                  <div>
                    <h3>{document.filename}</h3>
                    <p className="muted">
                      {document.chunk_count} chunks • {document.file_type.toUpperCase()}
                    </p>
                  </div>
                  <button
                    type="button"
                    className="danger-button"
                    onClick={() => void handleDelete(document.document_id)}
                  >
                    Remove
                  </button>
                </article>
              ))
            ) : (
              <p className="muted">
                {loadingDocuments ? "Loading documents..." : "No indexed documents yet."}
              </p>
            )}
          </div>
        </section>

        <section className="panel panel-wide">
          <h2>Ask Questions</h2>
          <form onSubmit={handleAsk} className="stack">
            <label className="field">
              <span>Document scope</span>
              <select
                value={selectedDocumentId}
                onChange={(event) => setSelectedDocumentId(event.target.value)}
              >
                <option value="all">All documents</option>
                {documents.map((document) => (
                  <option key={document.document_id} value={document.document_id}>
                    {document.filename}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Prompt</span>
              <textarea
                rows="5"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Summarize the contract terms, extract key deadlines, or answer grounded questions."
              />
            </label>

            <button type="submit" disabled={asking}>
              {asking ? "Thinking..." : "Ask the Assistant"}
            </button>
          </form>
        </section>

        <section className="panel panel-wide answer-panel">
          <div className="panel-header">
            <h2>Response</h2>
            <p className="status">{status}</p>
          </div>

          <div className="answer-block">
            {answer ? <p>{answer}</p> : <p className="muted">Answers will appear here.</p>}
          </div>

          <div className="sources">
            {sources.map((source) => (
              <article key={source.chunk_id} className="source-card">
                <div className="source-meta">
                  <strong>{source.filename}</strong>
                  <span>
                    {source.page ? `Page ${source.page}` : "Chunk"} • Score{" "}
                    {typeof source.score === "number" ? source.score.toFixed(3) : "n/a"}
                  </span>
                </div>
                <p>{source.content}</p>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
