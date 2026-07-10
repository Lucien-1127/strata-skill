---
name: vertex-ai-web-integration
description: "Integrate Google Cloud AI services (Gemini/Vertex AI) into web applications — authentication, API calls, and frontend integration."
---
# vertex-ai-web-integration

## 📖 Description

>-

---

# Vertex AI Web Integration

## When to use

- Building a React + Node.js web app that uses Gemini models via **Google Cloud Vertex AI** (enterprise mode, not Developer API key).
- You received a Vertex AI Studio "Get Code" export and need to make it production-ready instead of running the fragile fetch-interceptor pattern.
- You want to stream Gemini responses as SSE from Express without a browser-side SDK.

## The Vertex AI Studio Export Problem

Vertex AI Studio's "Get Code" generates this architecture:

```
React (@google/genai SDK) → vertex-ai-proxy-interceptor.js (global fetch/WS patch)
    → Express proxy (/api-proxy) → Vertex AI
```

**Why it's fragile:**

| Issue | Risk |
|-------|------|
| `vertex-ai-proxy-interceptor.js` patches `window.fetch` + `WebSocket` | Any other library doing async I/O can be affected |
| SDK version bumps can change internal URL patterns | Interceptor misses, request goes directly to Google with a fake API key → silent failure |
| `PROXY_HEADER` hardcoded in frontend, read from env in backend | Desync = permanent 403 |
| `@google/genai` SDK bundled in browser (~150KB) | Mostly dead weight; you only need `fetch()` |
| `node-fetch` as a dependency | Unnecessary on Node.js 18+ |

## Clean Architecture

```
React (plain fetch + SSE reader) → Express → @google/genai SDK (Node.js) → Vertex AI
```

### 1. Backend — initialize SDK

```js
import { GoogleGenAI } from '@google/genai';

const PROJECT = process.env.GOOGLE_CLOUD_PROJECT;
const LOCATION_RAW = process.env.GOOGLE_CLOUD_LOCATION || 'us-central1';

// "global" is NOT a valid Vertex AI region — resolve based on model generation:
//   - Gemini 2.x → us-central1
//   - Gemini 3.x → multi-region "us" (required by 3.5 Flash)
const MODEL = 'gemini-3.5-flash';
const isGemini3 = MODEL.startsWith('gemini-3');
const LOCATION = LOCATION_RAW === 'global'
  ? (isGemini3 ? 'us' : 'us-central1')
  : LOCATION_RAW;

const ai = new GoogleGenAI({
  enterprise: true,       // NOT vertexai: true — that property is invalid in v2.x
  project: PROJECT,
  location: LOCATION,
  apiVersion: 'v1',
});
```

- `enterprise: true` tells the SDK to use Vertex AI endpoints + ADC (Application Default Credentials).
- No `apiKey` is passed — the SDK picks up `gcloud auth application-default login` credentials automatically.
- No `dotenv` needed if using Express 5's `--env-file=.env.local` flag.

### 2. Backend — SSE streaming endpoint

```js
app.post('/api/chat', async (req, res) => {
  const { message, history } = req.body;
  if (!message?.trim()) return res.status(400).json({ error: 'message required' });

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  try {
    const chat = ai.chats.create({
      model: 'gemini-3.5-flash',
      config: {
        systemInstruction: 'You are a helpful assistant.',
        temperature: 0.3,
      },
      history: history ?? [],
    });

    const stream = await chat.sendMessageStream({ message: message.trim() });
    for await (const chunk of stream) {
      if (chunk.text) {
        res.write(`data: ${JSON.stringify({ text: chunk.text })}\n\n`);
      }
    }
    res.write(`data: ${JSON.stringify({ done: true })}\n\n`);
    res.end();
  } catch (err) {
    if (res.headersSent) {
      res.write(`data: ${JSON.stringify({ error: err.message })}\n\n`);
      res.end();
    } else {
      res.status(500).json({ error: err.message });
    }
  }
});
```

**Key detail:** `chunk.text` from `sendMessageStream` returns **incremental deltas**, not the full accumulated text. The frontend should append each chunk.

### 3. Frontend — plain fetch + SSE reader

Remove `@google/genai` from `package.json` and delete `vertex-ai-proxy-interceptor.js`. Replace with:

```ts
export async function* sendChatMessage(
  message: string,
  history?: Array<{ role: string; parts: Array<{ text: string }> }>,
) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history: history ?? [] }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    yield { error: body.error || `HTTP ${response.status}` };
    return;
  }
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split('\n\n');
    buffer = events.pop() ?? '';
    for (const event of events) {
      for (const line of event.split('\n')) {
        if (line.startsWith('data: ')) {
          yield JSON.parse(line.slice(6));
        }
      }
    }
  }
}
```

### 4. Vite dev proxy

```ts
// vite.config.ts
server: {
  proxy: {
    '/api': { target: 'http://localhost:5000', changeOrigin: true },
  },
}
```

No `/api-proxy` or `/ws-proxy` rules needed anymore.

## Conversation History

- Frontend keeps a `Message[]` state array.
- On each send, convert to SDK Content format and pass as `history`.
- The backend creates a fresh `Chat` session each time with the supplied history.
- This avoids server-side session state and works with serverless/containerized deployments.

```ts
function toSdkHistory(messages: Message[]) {
  return messages.map(m => ({
    role: m.role === 'user' ? 'user' : 'model',
    parts: [{ text: m.text }],
  }));
}
```

## Pitfalls

- **Old server process hangs onto port 5000**: If the SSE endpoint returns only `{"done":true}` with no text, kill ALL node processes (`taskkill /F /IM node.exe` on Windows) and restart.
- **`global` location requires generation-aware mapping**: Vertex AI API routing doesn't accept `global`. Gemini 3.x (e.g. `gemini-3.5-flash`) requires multi-region `us`, while Gemini 2.x uses `us-central1`. Using the wrong region → 404 `Publisher model not found`. Resolve dynamically:
  ```
  const isGemini3 = MODEL.startsWith('gemini-3');
  const LOCATION = LOCATION_RAW === 'global'
    ? (isGemini3 ? 'us' : 'us-central1')
    : LOCATION_RAW;
  ```
- **Don't pass `apiKey` with `enterprise: true`**: The two modes are mutually exclusive. `enterprise` uses ADC; `apiKey` uses the Developer API key. Passing both is ignored but confusing.
- **Express 5 async**: Unlike Express 4, Express 5 natively catches promise rejections from async handlers. No need for `express-async-errors`.
- **`sendMessageStream` vs `generateContentStream`**: Both work, but `sendMessageStream` (via `chats.create`) handles the conversation history and turn tracking automatically. `generateContentStream` is stateless — you must pass all history via `contents` yourself.
- **IAM role required**: The authenticated account needs **Vertex AI User** (`roles/aiplatform.user`) on the project. Without it, you get `Permission 'aiplatform.endpoints.predict' denied` (HTTP 403). Check IAM at `https://console.cloud.google.com/iam-admin/iam?project=<PROJECT_ID>`. The Vertex AI API itself must also be enabled: `gcloud services enable aiplatform.googleapis.com`.
- **`.env.local` from Vertex AI Studio export uses a fake project ID**: The exported `.env.local` contains a sample project like `project-322e33f2-...`. Your real GCP project ID is different — find it in Google Cloud Console and update `.env.local` before running.
- **Windows auth: use CMD or git-bash, not PowerShell**: PowerShell's ExecutionPolicy blocks `gcloud.ps1`. From CMD or git-bash, `gcloud auth login --launch-browser` works fine.
- **ADC refresh needed after switching accounts**: `gcloud auth login` updates the CLI account but NOT the ADC file. Run `gcloud auth application-default login --launch-browser` separately to refresh ADC credentials.
- **IAM roles via CLI**: `gcloud projects add-iam-policy-binding` lets you grant Vertex AI User without the browser. The user prefers CLI over browser for GCP admin tasks.
- **Service account for production**: Replace personal ADC with a dedicated service account:
  ```bash
  gcloud iam service-accounts create sa-<app-name> --project=<PROJECT_ID>
  gcloud projects add-iam-policy-binding <PROJECT_ID> \\
    --member="serviceAccount:sa-<app-name>@<PROJECT_ID>.iam.gserviceaccount.com" \\
    --role="roles/aiplatform.user"
  gcloud projects add-iam-policy-binding <PROJECT_ID> \\
    --member="serviceAccount:sa-<app-name>@<PROJECT_ID>.iam.gserviceaccount.com" \\
    --role="roles/logging.logWriter"
  gcloud iam service-accounts keys create ./vertex-sa-key.json \\
    --iam-account=sa-<app-name>@<PROJECT_ID>.iam.gserviceaccount.com
  ```
  Then set `GOOGLE_APPLICATION_CREDENTIALS=vertex-sa-key.json` in `.env.local` and add the key file to `.gitignore`.

## Deployment: Service Account Auth

Replace personal ADC with a dedicated service account before deploying beyond local dev:

```bash
# 1. Create service account
gcloud iam service-accounts create sa-<app-name> --project=<PROJECT_ID>

# 2. Grant minimal roles
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:sa-<app-name>@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:sa-<app-name>@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# 3. Download key
gcloud iam service-accounts keys create ./vertex-sa-key.json \
  --iam-account=sa-<app-name>@<PROJECT_ID>.iam.gserviceaccount.com
```

Then in `.env.local`:
```
GOOGLE_APPLICATION_CREDENTIALS="vertex-sa-key.json"
```

And add to `.gitignore`:
```
backend/vertex-sa-key.json
.env.local
```

This limits blast radius if the key leaks — the service account can only call Vertex AI and write logs, nothing else.

## Overlap notice

This skill and `google-cloud-ai` (mlops category) cover the same territory (Vertex AI web integration, SDK setup, auth, Studio export refactoring). Consolidation recommended: this skill (`vertex-ai-web-integration`) has the deeper refactoring recipe; `google-cloud-ai` has the broader GCP context. Merge into one.

## Cross-references

- `google-cloud-ai` skill → references — Auth setup, troubleshooting, cost optimization, service audit.
- `gcp-cost-optimization` skill (devops) — Cost reduction playbook for ongoing infrastructure management.
- `project-architecture-audit` skill — Methodology for deep codebase + cloud infrastructure audits.
