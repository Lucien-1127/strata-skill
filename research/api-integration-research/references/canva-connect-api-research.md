# Canva Connect API + MCP Server — Research Reference

> Researched 2026-07-06 via api-integration-research methodology. This is a concrete example of the skill's output.

## Canva Connect API Overview

- **Version**: 2024-06-18
- **Total endpoints**: 58
- **Auth**: OAuth 2.0 Authorization Code + PKCE (SHA-256)
- **OpenAPI spec**: https://www.canva.dev/sources/connect/api/latest/api.yml

## Authentication Flow

1. Developer registers in [Developer Portal](https://www.canva.dev/developers/), gets `client_id` + `client_secret`
2. User visits `https://www.canva.com/api/oauth/authorize` with PKCE challenge, authorizes, receives `authorization_code` at redirect URL
3. Backend exchanges `authorization_code` + `code_verifier` for `access_token` + `refresh_token`
4. All API calls use `access_token` as Bearer token
5. `refresh_token` is **one-time use**; each refresh returns a new one

### ⚠️ Key constraint: initial authorization **requires** browser interaction. Afterward, refresh tokens keep working server-side indefinitely.

## OAuth Scopes (18 total)

`asset:read`, `asset:write`, `brandtemplate:content:read`, `brandtemplate:content:write`, `brandtemplate:meta:read`, `collaboration:event`, `comment:read`, `comment:write`, `design:content:read`, `design:content:write`, `design:meta:read`, `email`, `folder:permission:write`, `folder:read`, `folder:write`, `openid`, `profile`, `profile:read`

Scopes are explicit — `asset:write` does NOT imply `asset:read`.

## Endpoint Categories

| Category | Count | Key Endpoints |
|----------|-------|---------------|
| Designs | 7 | CRUD, pages, dataset, export-formats |
| Assets | 6 | Upload (file+URL async), get/update/delete |
| Exports | 2 | Create export job, poll status |
| Autofill | 2 | Fill brand template, poll job |
| Brand Templates | 4 | List, create, get, get dataset |
| Comments | 6 | Threads, replies on designs |
| Folders | 7 | CRUD, move items, list contents |
| Merges | 2 | Merge designs (async) |
| Resizes | 2 | Resize designs (async) |
| Analytics | 4 | Page views, viewers, views-over-time, links |
| Users | 3 | Get user, profile, capabilities |
| OAuth/OIDC | 5 | Token, introspect, revoke, userinfo, jwks |
| Imports | 4 | Import design (file+URL async) |

## Canva Dev MCP Server

- **Package**: `@canva/cli` (npm), latest v2.6.0
- **MCP command**: `npx -y @canva/cli@latest mcp`
- **Transport**: stdio (local only)
- **MCP SDK**: `@modelcontextprotocol/sdk` 1.27.1
- **Clients**: Cursor, Claude Desktop, Claude Code, VS Code

**⚠️ Important**: The MCP server is a **development aid** (docs lookup, App UI Kit queries), NOT a Connect API execution layer. You cannot create designs or upload assets through the MCP server — those require direct REST API calls.

### MCP Config Example (Cursor)
```json
// .cursor/mcp.json
{
  "mcpServers": {
    "canva-dev": {
      "command": "npx",
      "args": ["-y", "@canva/cli@latest", "mcp"]
    }
  }
}
```

## Hermes Integration Options

1. **MCP Plugin only** — Zero dev effort, but only provides doc-query capability
2. **Hermes Skill (REST)** — Full CRUD via Connect API, needs OAuth token management
3. **Hybrid (recommended)** — MCP for docs + Skill for operations, shared token layer

## Key Links

| Resource | URL |
|----------|-----|
| Developer Portal | https://www.canva.dev/developers/ |
| Quickstart | https://www.canva.dev/docs/connect/quickstart/ |
| Auth docs | https://www.canva.dev/docs/connect/authentication/ |
| MCP Server | https://www.canva.dev/docs/connect/mcp-server/ |
| Scopes | https://www.canva.dev/docs/connect/appendix/scopes/ |
| Starter Kit | https://github.com/canva-sdks/canva-connect-api-starter-kit |
| npm pkg | `@canva/cli` |
