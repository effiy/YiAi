# YiAi Contracts

## Authentication

- Header: `X-Token: <token>`
- Enabled via `middleware.auth_enabled` config
- Applied via Auth middleware in stack: Auth → CORS → Throttle → Sampler

## Execution API

```
POST /execution
Body: { module_path, function_name, parameters }
Response: { code, data, message }
```
- Whitelist controlled via `module.allowlist`
- Supports sync/async, generators (SSE streaming)

## State Store API

```
POST   /state/records        — Create record, body: { key, data, tags, ttl }
GET    /state/records         — Query records, params: ?key=&tag=&limit=
GET    /state/records/{key}   — Get single record
PUT    /state/records/{key}   — Update record
DELETE /state/records/{key}   — Delete record
```

## WeWork Bot

```
POST /wework/send-message
Body: { webhook_url, content }
Headers: X-Token
```

## File Operations

All file endpoints accept `{ path, content? }` body.
Paths are sandboxed (SandboxMiddleware).

## Error Response

```json
{ "code": <error_code>, "message": "<description>", "data": null }
```
Error codes defined in `src/core/error_codes.py`.
