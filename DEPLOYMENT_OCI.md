# Production Deployment Guide: Oracle Cloud Infrastructure (OCI) Always Free Tier

This guide provides step-by-step instructions to deploy **CareerCatalyst v2** on **Oracle Cloud Infrastructure (OCI) Always Free Tier** using Docker Compose and Nginx reverse proxy.

---

## 1. OCI Always Free Compute Specifications

Oracle Cloud offers generous Always Free resources indefinitely:
- **Compute:** Ampere A1 ARM64 architecture with up to **4 OCPUs** and **24 GB RAM** (can be 1 large VM or 2-4 smaller VMs).
- **Storage:** **200 GB** Total Block Volume.
- **Outbound Data Transfer:** **10 TB / month**.
- **Public IP:** 1 Free Ephemeral / Reserved Public IPv4.

---

## 2. Step 1: Provision the VM on OCI Console

1. Log into your **Oracle Cloud Console**.
2. Navigate to **Compute** $\rightarrow$ **Instances** $\rightarrow$ Click **Create Instance**.
3. Configure instance details:
   - **Name:** `careercatalyst-prod`
   - **Image:** `Ubuntu 24.04 LTS` (or `Ubuntu 22.04 LTS`).
   - **Shape:** Click **Change Shape** $\rightarrow$ Select **Ampere (ARM)** $\rightarrow$ Choose `VM.Standard.A1.Flex` $\rightarrow$ Configure **4 OCPUs** and **24 GB RAM** (or 2 OCPUs / 12 GB RAM).
   - **Networking:** Select your Virtual Cloud Network (VCN) and ensure **Assign a public IPv4 address** is checked.
   - **SSH Keys:** Generate or upload your public SSH key (`id_rsa.pub`).
4. Click **Create** and wait for the instance state to show **Running** (green icon). Note down your **Public IP Address**.

---

## 3. Step 2: Configure OCI Firewall & Security Lists

### 3.1 OCI VCN Ingress Rules
1. In OCI Console, go to **Networking** $\rightarrow$ **Virtual Cloud Networks** $\rightarrow$ Select your VCN.
2. Under **Resources**, click **Security Lists** $\rightarrow$ Select **Default Security List**.
3. Click **Add Ingress Rules** and add two rules:
   - **HTTP (Port 80):**
     - Source CIDR: `0.0.0.0/0`
     - IP Protocol: `TCP`
     - Destination Port Range: `80`
   - **HTTPS (Port 443):**
     - Source CIDR: `0.0.0.0/0`
     - IP Protocol: `TCP`
     - Destination Port Range: `443`

### 3.2 OS-Level Firewall (Ubuntu iptables)
Connect to your VM via SSH:
```bash
ssh -i /path/to/private_key ubuntu@<YOUR_PUBLIC_IP>
```

Ubuntu instances on OCI have default `iptables` rules that block incoming traffic on ports 80/443. Open them:
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

---

## 4. Step 3: Install Docker & Docker Compose

Run on the Ubuntu instance:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg lsb-release git

# Install Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable Docker without sudo
sudo usermod -aG docker ubuntu
newgrp docker
```

---

## 5. Step 4: Clone & Configure CareerCatalyst

```bash
git clone https://github.com/<your_username>/CareerCatalyst_v2.git
cd CareerCatalyst_v2

# Create production .env file
nano .env
```

Paste your production secrets into `.env`:
```env
# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# PostgreSQL Database Credentials
POSTGRES_USER=admin
POSTGRES_PASSWORD=generate_a_secure_password_here
POSTGRES_DB=resumes_db

# Gemini Models
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004

# Application
APP_ENV=production
```

---

## 6. Step 5: Launch the Production Stack

Build and start the multi-container stack in detached mode:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Check running containers:
```bash
docker compose -f docker-compose.prod.yml ps
```

You should see 4 active containers:
- `catalyst_db_prod` (`ankane/pgvector:latest`)
- `catalyst_backend_prod` (FastAPI backend on port 8000)
- `catalyst_frontend_prod` (React/Vite static build on port 80)
- `catalyst_nginx_proxy` (Nginx reverse proxy on port 80 & 443)

Verify backend health check:
```bash
curl http://localhost/health
# Expected Output: {"status":"active","message":"CareerCatalyst Backend is running"}
```

---

## 7. Step 6: Enable Free SSL with Let's Encrypt (Certbot)

If you have a domain pointing to your OCI public IP (e.g., `resume.yourdomain.com`):

1. Request certificate using Certbot Docker container:
   ```bash
   docker run -it --rm --name certbot \
     -v "$PWD/certbot_etc:/etc/letsencrypt" \
     -v "$PWD/certbot_var:/var/lib/letsencrypt" \
     -v "$PWD/certbot_challenge:/var/www/certbot" \
     certbot/certbot certonly --webroot -w /var/www/certbot \
     -d resume.yourdomain.com --email your-email@example.com --agree-tos --no-eff-email
   ```

2. Add HTTPS server block in `nginx/nginx.conf`:
   ```nginx
   server {
       listen 443 ssl http2;
       server_name resume.yourdomain.com;

       ssl_certificate /etc/letsencrypt/live/resume.yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/resume.yourdomain.com/privkey.pem;

       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;

       location /api/ {
           proxy_pass http://backend_upstream;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location / {
           proxy_pass http://frontend_upstream;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. Reload Nginx:
   ```bash
   docker compose -f docker-compose.prod.yml restart nginx
   ```

---

## 8. Maintenance & Rolling Updates

To deploy new code updates with zero downtime:
```bash
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```
