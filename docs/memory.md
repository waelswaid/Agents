# Memory Module Documentation

### Turns
- A turn is a single message in the conversation, either from the user or from the assistant.
- In code, a turn is represented as a dictionary (or TypedDict):
Example conversation with multiple turns:
```python
[
  {"role": "user", "content": "Hi!", "ts": ...},
  {"role": "assistant", "content": "Hello!", "ts": ...},
  {"role": "user", "content": "How are you?", "ts": ...}
]

```
### why is deque used for turns?
- deque allows us to append at end in O(1) and pop from start in O(1)
- in a chat we frequently add new turns (append to the end).
- we sometimes remove oldest turns when hitting a limit or when expired
- deque also automatically discards beyond-the-max turns (so no cleanup logic required)
