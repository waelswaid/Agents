# 08. Pydantic (Validation & 422s)

- Input models (`ChatRequest`) enforce required fields and constraints.
- On invalid input, FastAPI returns `422 Unprocessable Entity` with details:
```json
{
  "detail": [
    {"type":"string_too_short","loc":["body","message"],"msg":"String should have at least 1 characters","input":""}
  ]
}
```
- Output models (`ChatResponse`) document your non-stream response schema.

**Tip:** You can add **custom validators** for fields like `agent` to restrict to supported values.
