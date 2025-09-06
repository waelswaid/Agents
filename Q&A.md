# Q&A

## 1) 
---
- **Q:what's a namespace?**
- A: it's like a box that holds variables or objects so their names won't collide with variables or objects living in other boxes with the same name. example:
```python
class A:
    x = 10
class B:
    x = 20
print(A.x) #10
print(B.x)#20
```
- here both classes have a variable called x but A.x and B.x don't collide because they live in different namespaces (A and B)
---
## 2) 
---
- **Q: in main.py what does this do "app.state.memory_store = MemoryStore()", what are .state.memory_store? where did they come from?**

- A: FastAPI gives you app.state as a central container to hold data that the entire app might need to access.
Let's say your app has:
   - A database connection,
   - A cache client,
   - A memory store for short-term data.
instead of this:
```python
# BAD: passing db, cache, memory everywhere
def route_handler(db, cache, memory):
    ...
```
you can do this:
```python
from fastapi import FastAPI
app = FastAPI()
# Create the shared objects
db = "DatabaseConnectionObject"
cache = "RedisClient"
memory = {}
# Store them in app.state
app.state.db = db
app.state.cache = cache
app.state.memory = memory
```
now anywhere in the app you can:
```python
@app.get("/status")
def status_check():
    return {
        "db": str(app.state.db),
        "cache": str(app.state.cache)
    }

```
---

---
- **Q: **
- A:
---

---
- Q:
- A:
---

---
- Q:
- A:
---

---
- Q:
- A:
---

---
- Q:
- A:
---

---
- Q:
- A:
---

---
- Q:
- A:
---

---
- Q:
- A:
---

---
- Q:
- A:
---

---
- Q:
- A:
---

---
- Q:
- A:
---

