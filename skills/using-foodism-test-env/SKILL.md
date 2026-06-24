---
name: using-foodism-test-env
description: Use when the user asks to connect to, inspect, operate, or read Docker/service logs from the Foodism test environment at 34.63.71.94.
---

# Using Foodism Test Env

## Overview

Use SSH key auth to reach the Foodism test host and inspect Docker services/logs. Treat the environment as shared test infrastructure: prefer read-only checks first, and ask before restarting, redeploying, editing configuration, or touching secrets.

## Connection

Use this SSH target:

```bash
ssh -i ~/.ssh/foodism_ops_ed25519 jik1992@34.63.71.94
```

Non-interactive checks should use:

```bash
ssh -i ~/.ssh/foodism_ops_ed25519 -o BatchMode=yes -o ConnectTimeout=8 jik1992@34.63.71.94 'whoami && hostname && pwd'
```

Verified host details:

- Public IP: `34.63.71.94`
- SSH user: `jik1992`
- Hostname: `instance-foodism-flow-002`
- Internal IP: `10.128.0.3`
- Key path: `~/.ssh/foodism_ops_ed25519`
- Home: `/home/jik1992`

## Read-Only Checks

Start with these before changing anything:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
df -h
free -h
uptime
```

Useful project paths:

- `/home/jik1992/foodism-monitor-stack/docker-compose.dokploy.yml`
- `/home/jik1992/foodism-monitor-files`
- `/home/jik1992/foodism-monitor-secrets`
- `/home/jik1992/foodism-monitor-zernio-update`

## Logs

List relevant containers:

```bash
docker ps --format '{{.Names}}' | grep -E 'foodism-backend-test|foodism-proxy-test|dokploy-traefik|foodism-monitoring-stack' | sort
```

Known test containers include:

- `foodism-backend-test-wuxasm_api.1.nwp08p4uspvajp43k40x536pg`
- `foodism-backend-test-wuxasm_celery-worker.1.vcnddeyd1bpc9pvje6l3ovzbz`
- `foodism-backend-test-wuxasm_admin.1.d7ay0q44xexaopi86xeckm26h`
- `foodism-proxy-test-ot7xeq_payment.1.nsb8yuh9sr7fvcutpfifr90z2`
- `foodism-proxy-test-ot7xeq_deduction.1.iyqhfhos515fhfscz5qibkle9`
- `foodism-proxy-test-ot7xeq_foodism_mcp_proxy.1.p5hrw3puqebjocpgap34khzps`
- `dokploy-traefik`

Read recent logs:

```bash
docker logs --tail 100 <container>
docker logs --since 15m <container>
docker logs -f --tail 50 <container>
```

When reporting logs to the user, redact JWTs, API keys, cookies, authorization headers, database URLs, and any query parameters named `token`, `key`, `secret`, or `password`.

## Change Control

Do not restart containers, redeploy stacks, edit compose files, change DNS/Traefik labels, or read secret files unless the user explicitly asks for that operation. Use `docker logs`, `docker ps`, and file metadata first.
