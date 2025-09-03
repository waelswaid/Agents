# 14. Deployment (Dev, systemd, Reverse Proxy)

## Dev
```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## systemd (example)
```
[Unit]
Description=Pi Agent Server
After=network-online.target
Wants=network-online.target

[Service]
User=user
Group=user
WorkingDirectory=/home/user/Agents
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/user/Agents/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=2
TimeoutStartSec=60

[Install]
WantedBy=multi-user.target
```

## Reverse Proxy (Caddy/Nginx)
- Terminate TLS, forward to `127.0.0.1:8000`.
- For streaming, ensure **no buffering** on the proxy path.
