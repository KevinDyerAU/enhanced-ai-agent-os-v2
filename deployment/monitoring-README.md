# AOS Monitoring Stack

This directory contains the configuration for the AOS monitoring stack, which includes:
- Prometheus for metrics collection and alerting
- Grafana for visualization
- Alertmanager for alert routing and notification
- PostgreSQL Exporter for database metrics

## Services and Ports

| Service | Port | Description |
|---------|------|-------------|
| Prometheus | 9090 | Metrics collection and alerting |
| Grafana | 3001 | Dashboards and visualization |
| Alertmanager | 9093 | Alert routing and notification |
| PostgreSQL Exporter | 9187 | PostgreSQL metrics exporter |

## Getting Started

1. Start the monitoring stack:
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

2. Access the services:
   - Grafana: http://localhost:3001
     - Default credentials: admin/admin
   - Prometheus: http://localhost:9090
   - Alertmanager: http://localhost:9093

## Dashboards

### AOS Service Dashboard
- URL: http://localhost:3001/d/1/aos-service-dashboard
- Displays:
  - Service status and health
  - Request latency and error rates
  - Resource utilization (CPU, memory)
  - PostgreSQL metrics

## Alerts

Alerts are configured in `deployment/alert.rules` and managed by Alertmanager. Key alerts include:
- Service down
- High request latency
- High error rates

## Adding a New Service

1. Add the service to Prometheus configuration in `deployment/prometheus.yml`
2. Ensure the service exposes a `/metrics` endpoint
3. Update the Grafana dashboards as needed

## Customizing Alerts

1. Edit `deployment/alert.rules` for alert rules
2. Configure alert routing in `deployment/alertmanager.yml`
3. Reload Prometheus configuration:
   ```bash
   curl -X POST http://localhost:9090/-/reload
   ```
