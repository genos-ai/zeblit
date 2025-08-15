# Zeblit AI Development Platform - Production Deployment Checklist

## Pre-Deployment Checklist

### 1. Infrastructure Setup ✓
- [ ] Kubernetes cluster provisioned (minimum 3 nodes)
- [ ] Load balancer configured
- [ ] DNS records configured for zeblit.com and api.zeblit.com
- [ ] SSL certificates obtained (Let's Encrypt)
- [ ] CDN configured for static assets
- [ ] Backup storage configured (S3 or equivalent)

### 2. Security Review ✓
- [ ] All secrets rotated and stored in Kubernetes secrets
- [ ] JWT_SECRET is strong and unique
- [ ] Database passwords are strong
- [ ] Redis password configured
- [ ] Network policies configured in Kubernetes
- [ ] RBAC configured for Kubernetes access
- [ ] Security headers verified
- [ ] Rate limiting configured
- [ ] DDoS protection enabled

### 3. Database Preparation ✓
- [ ] Production database created
- [ ] Database backups configured
- [ ] Point-in-time recovery enabled
- [ ] Connection pooling configured
- [ ] Read replicas configured (if needed)
- [ ] Database monitoring enabled
- [ ] Slow query logging enabled
- [ ] All migrations tested

### 4. Environment Variables ✓
```bash
# Production .env checklist
DATABASE_URL=postgresql://user:pass@host:5432/zeblit_prod
REDIS_URL=redis://:password@redis:6379
JWT_SECRET=<strong-random-secret>
ENVIRONMENT=production
ANTHROPIC_API_KEY=<production-key>
OPENAI_API_KEY=<production-key>
RESEND_API_KEY=<production-key>
SENTRY_DSN=<sentry-project-dsn>
LOG_LEVEL=INFO
CORS_ORIGINS=https://zeblit.com,https://www.zeblit.com
```

### 5. Container Registry ✓
- [ ] Docker images built and tested
- [ ] Images scanned for vulnerabilities
- [ ] Images pushed to registry
- [ ] Image tags follow semantic versioning
- [ ] Latest stable images tagged as 'latest'

### 6. Kubernetes Resources ✓
- [ ] Namespaces created (production, staging)
- [ ] Resource quotas configured
- [ ] Network policies applied
- [ ] Secrets created from .env values
- [ ] ConfigMaps deployed
- [ ] PersistentVolumes provisioned
- [ ] Ingress controller installed
- [ ] Cert-manager configured

### 7. Monitoring & Observability ✓
- [ ] Prometheus deployed and configured
- [ ] Grafana dashboards created
- [ ] AlertManager rules configured
- [ ] Log aggregation (Loki) configured
- [ ] Application metrics exposed
- [ ] Uptime monitoring configured
- [ ] Error tracking (Sentry) configured
- [ ] APM solution deployed

### 8. Backup & Disaster Recovery ✓
- [ ] Database backup schedule configured
- [ ] Backup retention policy defined
- [ ] Backup restoration tested
- [ ] Kubernetes etcd backup configured
- [ ] Application data backup configured
- [ ] Disaster recovery plan documented
- [ ] Recovery time objective (RTO) defined
- [ ] Recovery point objective (RPO) defined

### 9. Performance Optimization ✓
- [ ] Database indexes verified
- [ ] Query performance tested
- [ ] Redis caching verified
- [ ] CDN caching headers configured
- [ ] Image optimization completed
- [ ] Bundle sizes optimized
- [ ] API response times < 200ms (p95)
- [ ] Load testing completed

### 10. CI/CD Pipeline ✓
- [ ] GitHub Actions secrets configured
- [ ] Kubernetes credentials added
- [ ] Automated testing passing
- [ ] Security scanning enabled
- [ ] Deployment automation tested
- [ ] Rollback procedure tested
- [ ] Blue-green deployment configured
- [ ] Health checks verified

## Deployment Steps

### Step 1: Database Setup
```bash
# 1. Create production database
kubectl apply -f k8s/production/postgres-secrets.yaml
kubectl apply -f k8s/base/postgres-deployment.yaml

# 2. Run migrations
kubectl exec -it postgres-0 -- psql -U zeblit -d zeblit_prod
kubectl exec -it backend-deployment -- python -m alembic upgrade head

# 3. Seed initial data
kubectl exec -it backend-deployment -- python -m src.backend.seed_data --production
```

### Step 2: Deploy Core Services
```bash
# 1. Deploy Redis
kubectl apply -f k8s/base/redis-deployment.yaml

# 2. Deploy Backend
kubectl apply -f k8s/production/backend-secrets.yaml
kubectl apply -f k8s/base/backend-deployment.yaml

# 3. Deploy Frontend
kubectl apply -f k8s/base/frontend-deployment.yaml

# 4. Configure Ingress
kubectl apply -f k8s/base/ingress.yaml
```

### Step 3: Configure Monitoring
```bash
# 1. Deploy Prometheus
kubectl apply -f k8s/monitoring/prometheus.yaml

# 2. Deploy Grafana
kubectl apply -f k8s/monitoring/grafana.yaml

# 3. Deploy Loki
kubectl apply -f k8s/monitoring/loki.yaml

# 4. Configure alerts
kubectl apply -f k8s/monitoring/alerts.yaml
```

### Step 4: Verify Deployment
```bash
# 1. Check pod status
kubectl get pods -n production

# 2. Check service endpoints
kubectl get svc -n production

# 3. Test health endpoints
curl https://api.zeblit.com/api/v1/health/health
curl https://zeblit.com/health

# 4. Run smoke tests
python scripts/smoke_tests.py --environment production
```

### Step 5: Configure Backups
```bash
# 1. Configure database backups
kubectl apply -f k8s/jobs/backup-postgres.yaml

# 2. Configure file backups
kubectl apply -f k8s/jobs/backup-uploads.yaml

# 3. Test backup restoration
kubectl apply -f k8s/jobs/test-restore.yaml
```

## Post-Deployment Checklist

### 1. Verification ✓
- [ ] All pods running and healthy
- [ ] Database connections working
- [ ] Redis connections working
- [ ] WebSocket connections working
- [ ] File uploads working
- [ ] Authentication working
- [ ] Project creation working
- [ ] Agent communication working

### 2. Performance Verification ✓
- [ ] Page load time < 3 seconds
- [ ] API response time < 200ms (p95)
- [ ] WebSocket latency < 100ms
- [ ] Database query time < 50ms (p95)
- [ ] Error rate < 0.1%
- [ ] Uptime > 99.9%

### 3. Security Verification ✓
- [ ] SSL certificates valid
- [ ] Security headers present
- [ ] CORS properly configured
- [ ] Authentication required on all endpoints
- [ ] Rate limiting working
- [ ] No sensitive data in logs
- [ ] Secrets not exposed

### 4. Monitoring Verification ✓
- [ ] Metrics being collected
- [ ] Dashboards showing data
- [ ] Alerts configured and tested
- [ ] Logs being aggregated
- [ ] Error tracking working
- [ ] Uptime monitoring active

### 5. Documentation ✓
- [ ] API documentation updated
- [ ] Deployment guide completed
- [ ] Troubleshooting guide created
- [ ] Runbook created
- [ ] Architecture diagrams updated
- [ ] Security policies documented

## Rollback Procedure

### Automatic Rollback
The CI/CD pipeline will automatically rollback if:
- Health checks fail
- Error rate exceeds 5%
- Response time exceeds SLA

### Manual Rollback
```bash
# 1. Rollback deployment
kubectl rollout undo deployment/backend -n production
kubectl rollout undo deployment/frontend -n production

# 2. Verify rollback
kubectl rollout status deployment/backend -n production
kubectl rollout status deployment/frontend -n production

# 3. Check application health
./scripts/health_check.sh production
```

## Emergency Contacts

- **On-Call Engineer**: [Phone/Email]
- **Database Admin**: [Phone/Email]
- **Security Team**: [Phone/Email]
- **Infrastructure Team**: [Phone/Email]

## Incident Response

1. **Identify** - Check monitoring dashboards
2. **Assess** - Determine severity and impact
3. **Communicate** - Notify stakeholders
4. **Mitigate** - Apply immediate fixes
5. **Resolve** - Implement permanent solution
6. **Review** - Post-mortem and improvements

## Sign-off

- [ ] Development Team Lead: _________________ Date: _______
- [ ] Operations Team Lead: _________________ Date: _______
- [ ] Security Team Lead: __________________ Date: _______
- [ ] Product Owner: ______________________ Date: _______ 