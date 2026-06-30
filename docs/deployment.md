# Production Deployment Guide

This guide details instructions for deploying **AI Gateway Pro** to production environments.

---

## 1. Production Requirements

- **Production Database:** PostgreSQL 14+ or MySQL 8.0+ (avoid using SQLite in highly concurrent production environments).
- **Process Manager:** Systemd (Linux) or Windows Service wrapper.
- **Reverse Proxy:** Nginx or Caddy with SSL enabled.

---

## 2. Docker Deployment

We provide a multi-container Docker configuration for instant deployment.

### Step 1: Set Up Env Configuration
Create a production `.env` file containing database connections and master encryption parameters:
```env
APP_NAME="AI Gateway Pro"
ENV=production
DEBUG=false
DATABASE_URL="mysql+pymysql://aigateway:[email protected]:3306/aigateway"
SECRET_KEY="your-super-secret-production-key"
MASTER_PASSWORD="your-strong-master-password"
```

### Step 2: Deploy Container
Run the Docker container image containing the precompiled FastAPI service and mounted sqlite/mysql volume:
```bash
docker run -d \
  --name ai-gateway-pro \
  -p 8080:8080 \
  --env-file .env \
  -v aigateway-data:/app/data \
  umeshpunia/ai-model-rotation:latest
```

---

## 3. Production Security Hardening

1. **Enable TLS/SSL:** Always run the gateway behind an HTTPS proxy to encrypt API credentials in transit.
2. **Restrict Access:** Bind the server host address to `127.0.0.1` unless external network nodes explicitly require query access.
3. **Log Rotation:** Keep application log files constrained to a max file size of 10MB to avoid server disk exhaustion.
