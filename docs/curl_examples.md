# 16. cURL Cookbook

## Non-stream
```bash
curl -s -X POST http://127.0.0.1:8000/chat   -H "Content-Type: application/json"   -d '{"message":"say hello","agent":"general","stream":false}'
```

## Stream (show headers)
```bash
curl -N -i -s -X POST http://127.0.0.1:8000/chat   -H "Content-Type: application/json"   -d '{"message":"count to five","agent":"general","stream":true}'
```

## Reuse conversation
```bash
curl -N -s -X POST http://127.0.0.1:8000/chat   -H "Content-Type: application/json"   -d '{"message":"continue","agent":"general","stream":true,"conversation_id":"<uuid>"}'
```
