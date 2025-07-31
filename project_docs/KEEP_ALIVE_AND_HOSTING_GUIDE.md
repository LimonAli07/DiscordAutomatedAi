# Keep-Alive and Hosting Guide for ProjectChronos Discord Bot

## How Keep-Alive Works

### What is Keep-Alive?

The keep-alive system is a Flask web server that runs alongside your Discord bot to:

1. **Prevent the bot from sleeping** on free hosting platforms
2. **Provide a health check endpoint** for monitoring services
3. **Allow external services to "ping" your bot** to keep it active

### Current Keep-Alive Implementation

Your bot includes a built-in keep-alive server (`keep_alive.py`) that:

- Runs on port 8080 (both localhost and your local IP)
- Provides a simple web interface at `http://127.0.0.1:8080`
- Responds to HTTP requests to keep the bot active
- Runs in a background thread so it doesn't interfere with the Discord bot

## Laptop Hosting Limitations

### ❌ Your Laptop Limitations:

- **Bot only runs when laptop is ON and connected to internet**
- **Bot stops when you close the laptop or shut down**
- **Bot stops when you lose internet connection**
- **Not suitable for 24/7 bot operation**

### ✅ When Laptop Hosting Works:

- Testing and development
- Personal use when you're actively using your computer
- Short-term bot operations

## 24/7 Hosting Solutions

### 1. Free Hosting Options

#### Render.com (Recommended Free Option)

- **Cost**: Free tier available
- **Uptime**: 24/7 with keep-alive
- **Setup**: Connect GitHub repository, auto-deploy
- **Limitations**: 750 hours/month free, sleeps after 15 minutes of inactivity
- **Keep-Alive**: Use external ping services like UptimeRobot

#### Railway.app

- **Cost**: $5/month credit (free trial)
- **Uptime**: 24/7
- **Setup**: Simple deployment from GitHub
- **Limitations**: Credit-based pricing

#### Heroku

- **Cost**: No longer has free tier
- **Uptime**: 24/7 (paid plans only)
- **Setup**: Git-based deployment

### 2. VPS Hosting (More Control)

#### DigitalOcean Droplet

- **Cost**: $4-6/month
- **Uptime**: 24/7
- **Setup**: Full Linux server control
- **Benefits**: Complete control, can run multiple bots

#### Linode/Vultr

- **Cost**: $3.50-5/month
- **Uptime**: 24/7
- **Setup**: Linux VPS with SSH access

### 3. Cloud Hosting

#### Google Cloud Platform (GCP)

- **Cost**: Free tier + usage-based
- **Uptime**: 24/7
- **Setup**: Cloud Run or Compute Engine

#### Amazon Web Services (AWS)

- **Cost**: Free tier + usage-based
- **Uptime**: 24/7
- **Setup**: EC2 or Lambda

## Setting Up 24/7 Hosting

### Option 1: Render.com (Easiest Free Option)

1. **Create GitHub Repository**:

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/discord-bot.git
   git push -u origin main
   ```

2. **Create Render Account**: Go to render.com and sign up

3. **Create New Web Service**:

   - Connect your GitHub repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `python main.py`
   - Set environment variables (Discord token, API keys)

4. **Set Up Keep-Alive Monitoring**:
   - Use UptimeRobot.com (free)
   - Monitor your Render app URL every 5 minutes
   - This prevents the free tier from sleeping

### Option 2: VPS Setup (DigitalOcean)

1. **Create Droplet**:

   - Choose Ubuntu 22.04
   - $4/month basic plan
   - Add SSH key

2. **Install Dependencies**:

   ```bash
   sudo apt update
   sudo apt install python3 python3-pip git
   ```

3. **Clone and Setup Bot**:

   ```bash
   git clone https://github.com/yourusername/discord-bot.git
   cd discord-bot
   pip3 install -r requirements.txt
   ```

4. **Create .env File**:

   ```bash
   nano .env
   # Add your environment variables
   ```

5. **Run Bot with Screen/Tmux**:
   ```bash
   screen -S discord-bot
   python3 main.py
   # Press Ctrl+A then D to detach
   ```

## Environment Variables for Hosting

### Required Variables:


```env
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_OWNER_ID=your_discord_user_id
```

### Optional Variables:


```env
OPENAI_API_KEY=your_openai_key
GOOGLE_AI_KEY=your_google_ai_key
DEBUG_MODE=false
SESSION_SECRET=random_secret_string
```

## Keep-Alive Monitoring Services

### UptimeRobot (Free)

- Monitor up to 50 URLs for free
- Check every 5 minutes
- Email/SMS alerts when bot goes down
- Perfect for keeping Render.com free tier active

### Pingdom

- Professional monitoring
- More detailed analytics
- Paid service with free trial

### StatusCake

- Free tier available
- Good for basic monitoring

## Recommended Setup for 24/7 Operation

### For Beginners (Free):

1. **Host on Render.com** (free tier)
2. **Monitor with UptimeRobot** (free)
3. **Store code on GitHub** (free)

### For Serious Use ($4-6/month):

1. **VPS hosting** (DigitalOcean/Vultr)
2. **Run with screen/tmux** for persistence
3. **Set up automatic restarts** with systemd
4. **Monitor with UptimeRobot**

## Bot Persistence Commands

### Using Screen (Linux/VPS):

```bash
# Start new screen session
screen -S discord-bot

# Run bot
python3 main.py

# Detach (Ctrl+A then D)
# Reattach later
screen -r discord-bot
```

### Using Systemd (Linux/VPS):

Create `/etc/systemd/system/discord-bot.service`:

```ini
[Unit]
Description=Discord Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable discord-bot
sudo systemctl start discord-bot
```

## Summary

- **Laptop hosting**: Only works when laptop is on and connected
- **Free 24/7 hosting**: Render.com + UptimeRobot monitoring
- **Paid 24/7 hosting**: VPS ($4-6/month) for full control
- **Keep-alive**: Built into your bot, works with all hosting options
- **Monitoring**: Essential for free hosting platforms

Your bot is ready for any of these hosting options with the keep-alive system already built in!
