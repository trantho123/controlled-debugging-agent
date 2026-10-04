# Baseline Evidence — Controlled Debugging Agent POC

## 1. Regression Test Results
All individual service test suites execute and pass cleanly:

| Service | Test File | Results | Status |
| :--- | :--- | :--- | :--- |
| Weather REST | `services/weather-rest/test_app.py` | 2 passed | **PASS** |
| GraphQL Service | `services/graphql-service/test_app.py` | 1 passed | **PASS** |
| MCP Server | `services/mcp-server/test_app.py` | 2 passed | **PASS** |

Total: **5 passed / 5 tests (100%)**

---

## 2. Docker Container Status
All services are containerized and running under Docker Compose:

| Service | Container Image | Status | Published Ports |
| :--- | :--- | :--- | :--- |
| `jaeger` | `jaegertracing/all-in-one:latest` | `Up` | `16686:16686`, `4318:4318` |
| `weather-rest` | `controlled-debugging-agent-weather-rest` | `Up` | `8003:8000` |
| `graphql-service` | `controlled-debugging-agent-graphql-service` | `Up` | `8002:8000` |
| `mcp-server` | `controlled-debugging-agent-mcp-server` | `Up` | `8000:8000` |

---

## 3. Live MCP Request & Response

### Request
- **Protocol**: MCP Streamable HTTP (`http://localhost:8000/mcp`)
- **Tool**: `get_weather`
- **Arguments**:
```json
{
  "city": "Da Nang"
}
```

### Response
```json
{
  "city": "Da Nang",
  "temperature": 30,
  "condition": "Sunny"
}
```

---

## 4. Distributed Tracing Evidence (Jaeger)

- **Trace ID**: `4f6ecbb96794e4be5bb01f1aafdebe31`
- **Participating Services**:
  1. `weather-mcp-server`
  2. `weather-graphql-service`
  3. `weather-rest-service`
- **Span Count**: 11 spans
- **End-to-End Span Hierarchy**:
  - `weather-mcp-server`: `tools/call get_weather` (Root Span)
    - `weather-mcp-server`: `get_weather`
      - `weather-mcp-server`: `POST` (HTTP client to `graphql-service:8000/graphql`)
        - `weather-graphql-service`: `POST /graphql` (FastAPI server)
          - `weather-graphql-service`: `GET` (HTTP client to `weather-rest:8000/weather/Da%20Nang`)
            - `weather-rest-service`: `GET /weather/{city}` (FastAPI server)

---

## 5. Final Status
**Status**: `KNOWN_GOOD`
The baseline system is stable, fully tested, reproducible via Docker Compose, and observably verified via distributed tracing across all three microservices.
