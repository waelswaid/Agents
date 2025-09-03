# 15. Client Examples

## Python (non-stream)
```python
import httpx
r = httpx.post("http://127.0.0.1:8000/chat", json={"message":"hi","agent":"general","stream":False})
print(r.json())
```

## Python (stream)
```python
import httpx
with httpx.stream("POST", "http://127.0.0.1:8000/chat", json={"message":"hi","agent":"general","stream":True}) as r:
    print("convo id:", r.headers.get("X-Conversation-Id"))
    for line in r.iter_lines():
        print(line)
```

## Browser (chunked)
```html
<script>
fetch("/chat", {
  method: "POST",
  headers: {"Content-Type":"application/json"},
  body: JSON.stringify({message:"hi",agent:"general",stream:true})
}).then(res => {
  console.log("X-Conversation-Id:", res.headers.get("X-Conversation-Id"));
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  function read() {
    reader.read().then(({done, value}) => {
      if (done) return;
      console.log(decoder.decode(value));
      read();
    });
  }
  read();
});
</script>
```
