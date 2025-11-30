---
description: Initialize Redis for PopKit Power Mode (multi-agent orchestration)
---

# /popkit:power-init - Power Mode Initialization

Set up Redis infrastructure for multi-agent collaboration.

## Usage

```
/popkit:power-init              # Check status and setup if needed
/popkit:power-init start        # Start Redis
/popkit:power-init stop         # Stop Redis
/popkit:power-init restart      # Restart Redis
/popkit:power-init debug        # Start with Redis Commander (http://localhost:8081)
/popkit:power-init test         # Test Redis connectivity
```

## What It Does

Power Mode requires Redis for pub/sub messaging between agents. This command:

1. Checks if Docker is installed and running
2. Checks if Redis container exists
3. Starts/stops Redis as needed
4. Verifies Redis is accessible on localhost:6379
5. Optionally starts Redis Commander for debugging

## Prerequisites

- Docker installed and running
- Docker Compose (V1 or V2)

If Docker is not installed:
- **macOS**: Install Docker Desktop from https://docs.docker.com/desktop/mac/install/
- **Windows**: Install Docker Desktop from https://docs.docker.com/desktop/windows/install/
- **Linux**: Install Docker Engine from https://docs.docker.com/engine/install/

## Process

### Without Arguments (Default: Status + Auto-Start)

```bash
# 1. Check Docker availability
docker ps

# 2. Check if Redis is running
docker ps --filter name=popkit-redis

# 3. Check if Redis is accessible
# Python redis.ping() test on localhost:6379

# 4. If not running, auto-start
cd power-mode/
python setup-redis.py start
```

### Start Command

```bash
# Navigate to power-mode directory
cd power-mode/

# Run setup script
python setup-redis.py start
```

The script will:
1. Pull Redis 7 Alpine image (if not cached)
2. Create popkit-redis container
3. Expose port 6379
4. Create persistent volume for data
5. Wait for health check to pass
6. Verify connectivity

### Stop Command

```bash
cd power-mode/
python setup-redis.py stop
```

Gracefully stops Redis container and removes it (data persists in volume).

### Debug Command

```bash
cd power-mode/
python setup-redis.py debug
```

Starts Redis Commander at http://localhost:8081 for visual debugging of:
- Active pub/sub channels
- Stored keys and values
- Agent states
- Message queues

### Test Command

```bash
cd power-mode/
python setup-redis.py test
```

Verifies:
- Redis connectivity
- Pub/sub functionality
- All Power Mode channels (pop:broadcast, pop:heartbeat, etc.)

## Output

### Success

```
✓ Docker is installed and running
✓ Redis container is running
✓ Redis is accessible on localhost:6379

Ready for Power Mode!
```

### Needs Setup

```
✓ Docker is installed and running
⚠ Redis container is not running
⚠ Redis is not accessible

Power Mode not ready
ℹ Run: /popkit:power-init start
```

### Missing Docker

```
✗ Docker is not available
ℹ Install Docker: https://docs.docker.com/get-docker/

Power Mode not ready
```

## Redis Configuration

From `power-mode/config.json`:

```json
{
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": null,
    "socket_timeout": 5,
    "retry_on_timeout": true
  }
}
```

## Channels Used

Power Mode uses these Redis channels:

| Channel | Purpose |
|---------|---------|
| pop:broadcast | Messages to all agents |
| pop:heartbeat | Agent health checks |
| pop:results | Task completion results |
| pop:insights | Shared discoveries between agents |
| pop:coordinator | Coordinator commands |
| pop:human | Requests for human decisions |

## Docker Compose Configuration

Located at `power-mode/docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: popkit-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  redis-commander:  # Only with --profile debug
    image: rediscommander/redis-commander
    ports:
      - "8081:8081"
```

## Integration with /popkit:morning

After setup, `/popkit:morning` will include Redis status:

```
Code Quality:
  TypeScript: ✓ No errors
  Lint: ✓ Clean
  Tests: ✓ All passing

Services:
  Redis: ✓ Running (localhost:6379)
  Power Mode: ✓ Ready
```

If Redis is not running:

```
Services:
  Redis: ✗ Not running
  Power Mode: ⚠ Unavailable

Recommendations:
1. Start Redis: /popkit:power-init start
```

## Troubleshooting

### Port Already in Use

If port 6379 is already in use:

```bash
# Check what's using the port
# macOS/Linux:
lsof -i :6379

# Windows:
netstat -ano | findstr :6379

# Stop the conflicting service or change PopKit's port in config.json
```

### Container Won't Start

```bash
# Check Docker logs
docker logs popkit-redis

# Remove old container
docker rm -f popkit-redis

# Try starting again
/popkit:power-init start
```

### Redis Not Accessible

```bash
# Check container is running
docker ps | grep popkit-redis

# Check container health
docker inspect popkit-redis | grep Health

# Test connection manually
docker exec -it popkit-redis redis-cli ping
```

### Python redis Module Missing

```bash
# Install redis-py
pip install redis

# Or use the coordinator's requirements
cd power-mode/
pip install -r requirements.txt
```

## Examples

### First-Time Setup

```
/popkit:power-init

ℹ Checking Docker availability...
✓ Docker is installed and running
ℹ Starting Redis container...
✓ Redis container started
ℹ Waiting for Redis to be healthy...
✓ Redis is running and accessible

Ready for Power Mode!

Next steps:
1. Run /popkit:power-mode to activate multi-agent orchestration
2. Run /popkit:power-init debug to open Redis Commander
```

### Daily Check

```
/popkit:power-init

✓ Docker is installed and running
✓ Redis container is running
✓ Redis is accessible on localhost:6379

Ready for Power Mode!
```

### Debugging Session

```
/popkit:power-init debug

ℹ Starting Redis first...
✓ Redis is running and accessible
ℹ Starting Redis Commander...
✓ Redis Commander started at http://localhost:8081

Open http://localhost:8081 in your browser to inspect:
- Active pub/sub subscriptions
- Agent heartbeats
- Message queues
- Insight pool
```

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:power-mode` | Activate multi-agent orchestration |
| `/popkit:morning` | Includes Redis health check |
| `/popkit:power-init debug` | Visual debugging with Redis Commander |

## Architecture Integration

| Component | Integration Point |
|-----------|------------------|
| **Coordinator** | `power-mode/coordinator.py` connects to Redis |
| **Check-In Hook** | `hooks/power-mode-checkin.py` publishes to channels |
| **Morning Check** | Adds Redis status to health report |
| **Power Mode Command** | Auto-starts Redis if not running |
| **Config** | `power-mode/config.json` defines channels and intervals |

## Data Persistence

Redis data is persisted in a Docker volume:

```bash
# View volume
docker volume ls | grep popkit

# Inspect volume
docker volume inspect popkit_redis_data

# Remove volume (clears all data)
docker volume rm popkit_redis_data
```

Data includes:
- Agent registration history
- Learned patterns (last 24 hours)
- Session transcripts
- Objective progress

## Security Notes

This setup is for **local development only**:
- No password authentication
- No TLS/SSL
- Bound to localhost
- Not suitable for production

For production Power Mode:
- Use managed Redis (AWS ElastiCache, Redis Cloud, etc.)
- Enable authentication
- Use TLS
- Configure network security groups
