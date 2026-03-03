# API Gateway Security Lab

> A self-hosted API security testing environment built on a home lab, demonstrating how API gateways protect (and fail to protect) against real-world attack vectors — including SQL injection, broken authorization, excessive data exposure, and denial-of-service through load testing.

![Architecture Diagram](./docs/API%20Architecture.jpg)

---

## Why This Project Exists

This project was built as a technical evaluation for an API security company. The assignment: deploy both a **secure** and **insecure** API service, put them behind an API gateway, and demonstrate how APIs are exposed to real security risks — referencing the [OWASP API Security Top 10](https://owasp.org/API-Security/).

Rather than taking the cloud-hosted path the assignment suggested, I  chose to self-host everything using open-source tools on my home lab. I wanted to challenge myself with internally hosted solutions so I could learn more through out the experiece. For open source tools I went with Locust for load testing, Prometheus and Grafana for observability, and cAdvisor for system monitoring, alongside my already-running Pi-hole and Nginx Proxy Manager. The only cloud-hosted components are Kong Konnect's Control Plane and the Dev Portal (Web Application). In the website there is existing documentation covering five OWASP API vulnerabilities. The entire stack runs across two physical nodes managed via Portainer.

---

## Architecture Overview

The system is split across two physical machines on the same local network (`192.168.100.0/24`):

**Raspberry Pi 5 (`192.168.100.52`)** — Acts as the network's DNS server and reverse proxy. Runs Pi-hole (with Hagezi blocklist, 695K+ domains) for local DNS resolution and ad blocking, plus Nginx Proxy Manager for SSL termination and domain routing. All services managed through Portainer, this machine is the main Portainer controller.

**Ryzen 5 PC (`192.168.100.62`)** — The main compute node with larger compute resource. Hosts the Kong Data Plane (API Gateway), the Flask APIs, Prometheus, Grafana, Locust, Redis, and cAdvisor. Also managed through a Portainer Agent that connects back to the Pi 5's Portainer instance.

**Kong Konnect (Cloud)** — The Kong Control Plane runs in Kong's cloud platform (Kong Konnect). It pushes configuration to the self-hosted Data Plane node. The cloud-hosted Dev Portal is accessible via a custom domain (`nonamesec.org`) through a Cloudflare CNAME record.

Traffic flows like this:
1. External requests hit Cloudflare → resolve via proxied A record to my public IP
2. ISP routes traffic to the Raspberry Pi 5 (port forwarding on `443`)
3. Pi-hole handles local DNS; Nginx Proxy Manager routes `kong.nonamesec.org` to the Ryzen PC
4. Kong API Gateway on the Ryzen PC receives the request and routes it based on the path:
   - `/normal` → **Insecure API** (no protections)
   - `/secure` → **Secure API** (full plugin stack enabled)
---

## Tech Stack

| Component | Tool | Why This Choice |
|---|---|---|
| **API Gateway** | Kong Gateway (via Kong Konnect) | Kong's plugin ecosystem was the primary controller for: Rate Limiting, ACL, API key & Basic Auth, Bot Detection, SQL injection protection and much more if you enable more pluigins. They are all available as configurable plugins, this comes across very convenient if implementation is not done in code. |
| **API Framework** | Python 3 + Flask | Simple for setting up the API for both secure and insecure endpoints. Python was the natural choice given it's my primary language. |
| **Documentation Site** | HTML/CSS (hosted on Kong Dev Portal) | Built a custom documentation website covering five OWASP API vulnerabilities with interactive guides, API endpoint documentation, and a landing page. Hosted through Kong Konnect's Dev Portal via `nonamesec.org`. |
| **Observability** | Prometheus + Grafana | Open source fo metrics collection and visualization. The Kong has natively a plugin that integrated with Prometheus configurating it was straightforward. |
| **System Monitoring** | cAdvisor | Added container-level resource monitoring (CPU, memory) alongside Grafana to observe the impact of load testing on the host system. |
| **Load Testing** | Locust | Python-based load testing tool that allowed writing test scenarios in familiar code. Enabled testing 10,000+ requests/second against both API routes to measure the performance impact of security plugins. |
| **DNS / Ad Blocking** | Pi-hole | Already running on my home lab as the primary DNS server. |
| **Reverse Proxy** | Nginx Proxy Manager | Handles SSL termination and domain-based routing for all home lab services. Routes `kong.nonamesec.org` traffic to the Kong Data Plane. |
| **Container Management** | Portainer (+ Agent) | Manages Docker containers across both physical nodes from a single UI. The Pi 5 runs the Portainer server; the Ryzen PC runs a Portainer Agent. |
| **Metrics Storage** | Redis | Persistent storage for metrics data used alongside the observability stack. |
| **Edge / CDN** | Cloudflare | Provides DNS management, proxied A records, and SSL certificates. A CNAME record maps `nonamesec.org` to Kong Konnect's Dev Portal URL. |

---

## OWASP API Vulnerabilities Demonstrated

The project includes a documentation website with dedicated guide pages for five OWASP API Security Top 10 vulnerabilities. Each guide explains the vulnerability, how it applies to the deployed APIs, and how the secure API mitigates it/patches the vulnerability.

| Vulnerability | Guide | Description |
|---|---|---|
| **BOLA** — Broken Object Level Authorization | [Guide](./docs/Guides%20BOLA.html) | Demonstrates how an attacker can access other users' data by manipulating object IDs in API requests when authorization checks are missing. |
| **BFLA** — Broken Function Level Authorization | [Guide](./docs/Guides%20BFLA.html) | Shows how users can access admin-level or privileged API functions when function-level access controls are not enforced. |
| **SQLI** — SQL Injection | [Guide](./docs/Guides%20SQLI.html) | Demonstrates SQL injection through the insecure API endpoint and shows how both Kong's regex-based detection plugin and parameterized queries in the application code defend against it. |
| **EDE** — Excessive Data Exposure | [Guide](./docs/Guides%20EDE.html) | Exposes how APIs that return more data than the client needs which can lead to leak sensitive information, and how response filtering mitigates this. |
| **URC** — Unrestricted Resource Consumption | [Guide](./docs/Guides%20URC.html) | Demonstrates denial-of-service through unthrottled load testing and the role of rate limiting in preventing resource exhaustion. |

---

## Secure vs. Insecure API — What's Different

The Flask API (`simple-api.py`) exposes the same core endpoints on both routes. The difference is entirely in how Kong handles traffic to each:

### Insecure Route (`/normal` — Port 5000)

- **No API key required** — anyone can call any endpoint
- **No ACL (Access Control List)** — no authorization restrictions
- **No rate limiting** — unlimited requests accepted
- **No SQL injection protection** — vulnerable to SQLi through Kong; the application code itself uses string concatenation for SQL queries
- **HTTP only** — traffic is unencrypted (original goal was to intercept with Wireshark, though this wasn't included in the final demo)
- **No authentication** — endpoints are fully open

### Secure Route (`/secure` — Port 5001)

- **API key authentication** — requests must include a valid API key managed through Kong
- **ACL enforcement** — only authorized consumers can access specific endpoints
- **Rate limiting enabled** — Kong plugin throttles requests per consumer/route
- **SQL injection protection** — Kong plugin adds a regex-based detection layer; additionally, the application runs on port 5001 uses which enforces **parameterized queries** instead of string concatenation, eliminating SQLi at the database level
- **HTTPS** — traffic encrypted end-to-end
- **Basic auth on sensitive endpoints** — username/password authentication required before execution

### Key Security Insight

During the demo, I demonstrated that Kong's regex-based SQL injection detection **can be bypassed** with crafted payloads. This is why the secure route uses parameterized queries as a second line of defense. The gateway-level protection is a useful filter but not a complete solution.

---

## Key Findings and Results

### Load Testing Revealed a Hidden Defense Layer

When running Locust at 10,000+ requests/second against the insecure route (no rate limiting), I observed expected latency increases in Grafana. But when I disabled Kong's rate limiting plugin on the secure route and ran the same test, something unexpected happened: the requests were still being throttled.

**Reason: Pi-hole.** My DNS server was blocking a portion of the traffic as part of its filtering rules, creating an unintentional second layer of rate limiting. Once I disabled Pi-hole's blocking alongside Kong's rate limiting and re-ran the load test **Grafana went dark.** The monitoring dashboard itself went down because the Ryzen PC no being able to handle the flood of requests.

### Performance Impact of Security Plugins

With rate limiting enabled on Kong, I observed approximately a **30% increase in latency** compared to the unprotected route. This is the real cost of security at the gateway level and who it does protect against a system outage.

### Metrics Captured

Through the Prometheus + Grafana stack, I monitored:
- Request latency across both routes
- Requests processed per second and success/failure rates
- Container resource consumption (CPU, memory) via cAdvisor
- System behavior under sustained load — identifying the breaking point

---

## Challenges and Lessons Learned

### Kong Gateway Services and Routes (2 days of trial and error)

The hardest part of this project was understanding how Kong's **Services** and **Routes** work together. Documentation was "lacking" for my specific setup, so configuration was done through manual testing. At multiple points, I accidentally broke all endpoint routing. This caused every request to get blocked because a misconfiguration made changes across all routes. The fix required understanding that Services map to upstream targets while Routes map to incoming request patterns, and that the order and specificity of route matching matters significantly.

### Data Plane Metrics Not Producing Output

After enabling the Prometheus plugin on the Control Plane, the Data Plane wasn't producing any metrics not even being able to access the ported URI. This turned out to be a configuration issue. Specific settings needed to be enabled on the Data Plane node to allow metric output. The Kong documentation didn't make this clear for hybrid mode deployments, so it required digging through community forums and testing different configuration parameters.

### Docker Networking Isolation

The initial Kong Gateway deployment created its own isolated Docker network. This meant other services running on the same host (Prometheus, Grafana, the Flask APIs) couldn't communicate with Kong. The fix was switching Kong to **bridge mode** networking so all containers shared the same network space and could reach each other via internal DNS.

### Cloud Control Plane + Self-Hosted Data Plane Communication

Kong Konnect's Dev Portal couldn't communicate with my self-hosted Data Plane through CORS alone. I had to expose port 80 on the Data Plane to allow the cloud-hosted web interface to reach it. This wasn't ideal from a security perspective — in a production environment, I would have preferred a fully self-hosted deployment.

---

## Documentation Site

In addition to the infrastructure, I built a documentation website hosted through Kong Konnect's Dev Portal at `nonamesec.org`. The site includes:

- **Landing page** ([Index.html](./docs/Index.html)) — Project overview and navigation
- **API documentation** ([API.html](./docs/API.html), [API Secure.html](./docs/API%20Secure.html), [API Insecure.html](./docs/API%20Insecure.html)) — Endpoint reference for both the protected and unprotected APIs
- **OWASP vulnerability guides** ([Guides.html](./docs/Guides.html) + individual guide pages) — Interactive walkthroughs for five API security vulnerabilities (BOLA, BFLA, SQLI, EDE, URC), explaining how each attack works and how the secure route defends against it

The site was accessible to interviewers through the `nonamesec.org` domain, which pointed to Kong's Dev Portal via a Cloudflare CNAME record.

---

## Project Structure

```
api-gateway-security/
├── docs/
│   ├── API Architecture.jpg            # Full architecture diagram
│   ├── Index.html                      # Documentation site — landing page
│   ├── API.html                        # API overview documentation
│   ├── API Secure.html                 # Secure API endpoint documentation
│   ├── API Insecure.html               # Insecure API endpoint documentation
│   ├── Guides.html                     # OWASP vulnerability guides — index
│   ├── Guides BOLA.html                # Guide: Broken Object Level Authorization
│   ├── Guides BFLA.html                # Guide: Broken Function Level Authorization
│   ├── Guides SQLI.html                # Guide: SQL Injection
│   ├── Guides EDE.html                 # Guide: Excessive Data Exposure
│   └── Guides URC.html                 # Guide: Unrestricted Resource Consumption
├── grafana/
│   └── docker-compose.yml              # Grafana + cAdvisor dashboards
├── kong-gateway/
│   └── docker-compose.yml              # Kong Data Plane node configuration
├── locust/
│   ├── docker-compose.yml              # Locust load testing service
│   └── locustfile.py                   # Load test scenarios (Python)
├── prometheus/
│   └── docker-compose.yml              # Prometheus metrics collector
├── simple-api/
│   ├── docker-compose.yml              # Flask API service (both secure/insecure)
│   └── simple-api.py                   # API source code with vulnerable + safe endpoints
└── README.md                           # This file
```

---

## How to Run

### Prerequisites

- Docker and Docker Compose installed
- A Kong Konnect account (free tier works) for the Control Plane
- Ports 5000, 5001, 8443, 3000 (Grafana), 9090 (Prometheus), 8089 (Locust) available

### Configuration Notes

- Kong Data Plane requires connection credentials from Kong Konnect (Control Plane URL and cluster certificate)
- Prometheus needs to be enable in Kongs Plugin section, without it, no metrics would come
- Grafana connects to Prometheus as a data source; import the default Kong dashboard or use cAdvisor dashboards for system metrics

---

## Infrastructure

| Node | Hardware | IP | Role |
|---|---|---|---|
| Raspberry Pi 5 | ARM, Portainer Server | `192.168.100.52` | DNS (Pi-hole), Reverse Proxy (NPM), Container orchestration |
| Ryzen 5 PC | 64 GB RAM, Portainer Agent | `192.168.100.62` | Kong Data Plane, APIs, Prometheus, Grafana, Locust, Redis |
| Kong Konnect | Cloud-hosted | — | Control Plane, Dev Portal, Plugin configuration |

---

## What I Would Do Differently

- **Self-host everything and keep the API Gateway internal** — The biggest architectural change would be hosting the documentation website myself (on the Ryzen PC or Pi 5) as the only publicly exposed service, while keeping Kong and all backend APIs entirely on the private network. In this design, only the web server faces the internet; the API Gateway, Flask APIs, and observability and monitor solutions remain internal and unreachable from outside. This eliminates the CORS issues I encountered with Kong Konnect's cloud-hosted Dev Portal and removes the need to expose port 80 on the Data Plane. A fully self-hosted Kong (open-source, without Konnect) or an alternative like Apache APISIX would make this possible.
- **Add Wireshark traffic capture** — I originally planned to capture HTTP traffic on the insecure route to visually demonstrate unencrypted API data in transit. Time constraints prevented this, but it would strengthen the security demonstration.

---

## Author

**Sergio Arce** — DevOps & Security Automation Engineer

- [LinkedIn](https://linkedin.com/in/sergioarceacon)
- [GitHub](https://github.com/Sacon217)