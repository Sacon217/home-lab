# home-lab
This repository will be used to contain my home-lab journey. From services that will be ran locally to project I will have for testing and much more.

## Current Setup

### Hardware
- Raspberry Pi 5

### Services
This repository includes Docker Compose configurations for the following services:

1. **Nginx Proxy Manager (NPM)** - Web-based reverse proxy management
2. **Pi-hole** - Network-wide ad blocking and DNS server

## Quick Start

### Prerequisites
- Docker and Docker Compose installed on your Raspberry Pi 5
- Basic understanding of Docker containers

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Sacon217/home-lab.git
   cd home-lab
   ```

2. Create your environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file and set your desired Pi-hole password:
   ```bash
   nano .env
   ```

4. Start the services:
   ```bash
   docker-compose up -d
   ```

### Accessing Services

#### Nginx Proxy Manager
- **Web Interface**: http://your-raspberry-pi-ip:81
- **Default Credentials**:
  - Email: `admin@example.com`
  - Password: `changeme`
- **Important**: Change the default credentials after first login!

#### Pi-hole
- **Web Interface**: http://your-raspberry-pi-ip:8080/admin
- **Password**: The password you set in your `.env` file

### Port Configuration

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| NPM | 80 | HTTP | Web traffic |
| NPM | 443 | HTTPS | Secure web traffic |
| NPM | 81 | HTTP | Admin interface |
| Pi-hole | 53 | TCP/UDP | DNS server |
| Pi-hole | 8080 | HTTP | Web interface |

### Managing Services

Stop all services:
```bash
docker-compose down
```

View logs:
```bash
docker-compose logs -f
```

Restart services:
```bash
docker-compose restart
```

Update services:
```bash
docker-compose pull
docker-compose up -d
```

## Data Persistence

All service data is stored in local directories:
- `npm-data/` - Nginx Proxy Manager configuration
- `npm-ssl/` - SSL certificates
- `pihole/` - Pi-hole configuration and settings

These directories are automatically created when you start the services and are excluded from git via `.gitignore`.

## Network Configuration

Both services run on a custom Docker bridge network called `homelab`, allowing them to communicate with each other while maintaining isolation from the host network.

## Troubleshooting

### Port Conflicts
If you encounter port conflicts, you can modify the port mappings in `docker-compose.yml`. The format is `host-port:container-port`.

### Permission Issues
If you encounter permission issues with volumes, ensure your user has proper permissions:
```bash
sudo chown -R $USER:$USER npm-data npm-ssl pihole
```

### DNS Not Working
If Pi-hole DNS is not working, ensure:
1. Port 53 is not in use by another service
2. Your router/device is configured to use the Pi-hole IP as DNS server

## Future Plans
- Additional services as needed
- Testing and development projects
- Documentation improvements
