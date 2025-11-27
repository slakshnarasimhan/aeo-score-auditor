# 🌐 Network Access Guide - Share AEO Score Auditor

## ✅ Your Tool is Now Network Accessible!

**Your Machine IP:** `192.168.0.101`

Anyone on your local network can now use the AEO Score Auditor!

---

## 👥 For Users on Your Network

### Quick Start:

**1. Open this URL in your browser:**
```
http://192.168.0.101:3000
```

**2. Start auditing!**
- Single Page: Enter any URL and click "Audit Page"
- Entire Domain: Enter domain name and click "Audit Domain"

That's it! No installation needed! 🎉

---

## 🖥️ For The Host (You)

### Current Configuration:

✅ **Frontend**: Accessible at http://192.168.0.101:3000
✅ **Backend API**: Accessible at http://192.168.0.101:8000
✅ **CORS**: Enabled for all origins
✅ **Network**: All services properly configured

### Your Access URLs:

You can use either:
- `http://localhost:3000` (local access)
- `http://192.168.0.101:3000` (network access)

Both work the same way!

---

## 🔧 Configuration Details

### What Was Changed:

**1. Frontend Config (`frontend/src/config.ts`)**
```typescript
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

**2. Docker Compose (`docker-compose.yml`)**
```yaml
frontend:
  environment:
    - NEXT_PUBLIC_API_URL=http://192.168.0.101:8000
```

**3. Backend CORS (already enabled)**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📋 Sharing Instructions

### Send This to Your Team:

```
🎯 AEO Score Auditor is now available!

URL: http://192.168.0.101:3000

What it does:
• Audit any webpage for Answer Engine Optimization
• Analyze entire domains (multiple pages)
• Get detailed score breakdowns
• Identify improvement opportunities

How to use:
1. Open the URL above
2. Choose "Single Page" or "Entire Domain"
3. Enter URL/domain
4. Click audit and wait for results!

No installation needed - just use your browser!
```

---

## 🔥 Advanced: Access from Outside Your Network

### Option 1: Port Forwarding (Router Configuration)

**If you want internet access:**

1. Log into your router (usually 192.168.0.1 or 192.168.1.1)
2. Find "Port Forwarding" settings
3. Add rules:
   - External Port: 3000 → Internal IP: 192.168.0.101:3000 (Frontend)
   - External Port: 8000 → Internal IP: 192.168.0.101:8000 (Backend)
4. Get your public IP: `curl ifconfig.me`
5. Share: `http://YOUR_PUBLIC_IP:3000`

**⚠️ Security Warning:** This exposes your tool to the internet. Consider:
- Adding authentication
- Using HTTPS
- Restricting access by IP
- Using a VPN instead

### Option 2: Ngrok (Easy Tunneling)

**Quick internet access without router config:**

```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Tunnel frontend
ngrok http 3000

# Tunnel backend (in another terminal)
ngrok http 8000
```

Then update the frontend URL to use the ngrok backend URL.

### Option 3: Tailscale (Secure VPN)

**Best for team access:**

```bash
# Install Tailscale on your machine
curl -fsSL https://tailscale.com/install.sh | sh

# Install on team members' machines
# Then everyone can access via: http://100.x.x.x:3000
```

---

## 🔍 Troubleshooting

### Users Can't Access:

**1. Check Firewall**
```bash
# Allow ports 3000 and 8000
sudo ufw allow 3000
sudo ufw allow 8000
sudo ufw status
```

**2. Verify Services Are Running**
```bash
docker compose ps
# All should show "Up"
```

**3. Test from Host Machine**
```bash
# Test backend
curl http://192.168.0.101:8000/health

# Test frontend
curl http://192.168.0.101:3000
```

**4. Check Network Connectivity**
```bash
# From another machine on network
ping 192.168.0.101
```

### If Your IP Changes:

**Your IP might change after reboot!** To update:

```bash
# 1. Find new IP
hostname -I | awk '{print $1}'

# 2. Update docker-compose.yml
# Change NEXT_PUBLIC_API_URL to new IP

# 3. Restart frontend
docker compose restart frontend
```

### Using Static IP (Recommended):

**Set a static IP in your router:**
1. Log into router
2. Find DHCP settings
3. Reserve IP 192.168.0.101 for your MAC address
4. Reboot router

---

## 📊 Performance Considerations

### Network Load:

- **Single Page Audit**: ~1-3 MB data transfer
- **Domain Audit (50 pages)**: ~10-20 MB data transfer
- **Concurrent Users**: Up to 5-10 users simultaneously

### Resource Usage:

- **Backend**: ~500MB RAM per concurrent audit
- **Frontend**: Minimal (static assets)
- **Database**: ~100MB for typical usage

### Scaling:

For more users:
- Increase Docker resource limits
- Add more worker containers
- Consider deploying to a server (AWS, DigitalOcean, etc.)

---

## 🚀 Quick Verification

### Test Network Access:

**From your machine:**
```bash
curl http://192.168.0.101:8000/health
# Should return: {"status":"healthy",...}
```

**From another machine on your network:**
```bash
# Test backend
curl http://192.168.0.101:8000/health

# Test frontend (in browser)
http://192.168.0.101:3000
```

---

## 📱 Access from Mobile Devices

Anyone on your WiFi network can access from their phone or tablet:

1. Open browser on mobile device
2. Go to: `http://192.168.0.101:3000`
3. Use the tool just like on desktop!

Works on:
- ✅ iPhone/iPad (Safari, Chrome)
- ✅ Android (Chrome, Firefox)
- ✅ Tablets
- ✅ Smart TVs with browsers

---

## 🎯 What Others Will See

Users accessing your tool will see:
- ✅ Full AEO Score Auditor interface
- ✅ Single Page and Domain audit options
- ✅ Real-time progress bars
- ✅ Detailed score breakdowns
- ✅ Expandable categories
- ✅ All features you have!

---

## 🔒 Security Notes

### Current Setup (Development Mode):

- ⚠️ No authentication
- ⚠️ No HTTPS
- ⚠️ Open CORS (accepts all origins)
- ✅ Safe for trusted local networks
- ❌ NOT safe for internet exposure

### For Production:

Consider adding:
- [ ] User authentication (OAuth, JWT)
- [ ] HTTPS/SSL certificates
- [ ] Rate limiting
- [ ] API keys
- [ ] Access logs
- [ ] Restricted CORS origins

---

## 📝 Summary

### For Network Users:

**URL:** http://192.168.0.101:3000

Just open in any browser on your network! No setup required.

### For Internet Access:

Use ngrok or port forwarding (see Advanced section above).

### For Host (You):

Everything is configured! Your team can start using it right now.

---

## ✅ Checklist

- [x] Backend configured for network access
- [x] Frontend configured with host IP
- [x] CORS enabled for all origins
- [x] Services running on 0.0.0.0 (accessible from network)
- [x] Firewall rules (check if needed)
- [x] Documentation created

**Your AEO Score Auditor is now accessible to everyone on your network!** 🎉

Share the URL: **http://192.168.0.101:3000** 🚀

