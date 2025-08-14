# Zeblit Database Dump

This directory contains SQL dump files for importing the Zeblit AI Development Platform database into a clean PostgreSQL instance.

## Files

- `zeblit_database_dump.sql` - Complete database schema and seed data
- `README.md` - This documentation file

## Database Requirements

- PostgreSQL 16+ (recommended)
- Extensions: `uuid-ossp`, `pgcrypto`
- Minimum 1GB RAM for development
- Minimum 10GB storage for production

## Import Instructions

### 1. Create New Database

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create new database
CREATE DATABASE zeblit_production;

# Create user (optional)
CREATE USER zeblit WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE zeblit_production TO zeblit;

# Exit psql
\q
```

### 2. Import SQL Dump

```bash
# Import the complete dump
psql -U postgres -d zeblit_production -f zeblit_database_dump.sql

# Or with custom user
psql -U zeblit -d zeblit_production -f zeblit_database_dump.sql
```

### 3. Verify Import

```bash
# Connect to database
psql -U postgres -d zeblit_production

# Check tables
\dt

# Check users
SELECT email, username, role FROM users;

# Check agents
SELECT name, agent_type, is_active FROM agents;

# Check templates
SELECT name, framework, language FROM project_templates;

# Exit
\q
```

## What's Included

### Database Schema
- **users** - User accounts and authentication
- **agents** - AI agents with configurations
- **projects** - User projects and applications
- **project_templates** - Pre-configured project templates
- **containers** - Container lifecycle management
- **tasks** - AI agent tasks and execution
- **conversations** - AI chat conversations
- **project_files** - File management and versioning
- **git_branches** - Git branch tracking
- **cost_tracking** - LLM usage and cost tracking
- **audit_logs** - Comprehensive audit trail

### Seed Data
- **Default Users**:
  - `user@zeblit.com` / `password123` (regular user)
  - `admin@zeblit.com` / `admin123` (admin user)

- **AI Agents** (6 agents):
  - Development Manager (orchestration)
  - Product Manager (requirements)
  - Data Analyst (database design)
  - Senior Engineer (coding)
  - System Architect (architecture)
  - Platform Engineer (DevOps)

- **Project Templates** (6 templates):
  - Blank Project
  - React + TypeScript + Vite
  - FastAPI + Python
  - Next.js Fullstack
  - Vue 3 + TypeScript
  - Django + Python

### Performance Features
- Optimized indexes for all tables
- GIN indexes for JSONB and array columns
- Automatic timestamp triggers
- Proper foreign key constraints

## Environment Configuration

After importing, update your `.env` file:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://zeblit:your_password@localhost:5432/zeblit_production

# Or for development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/zeblit_production
```

## Post-Import Steps

1. **Update Environment Variables**
   ```bash
   # Copy example env file
   cp config/env.example .env
   
   # Update DATABASE_URL in .env
   nano .env
   ```

2. **Verify Database Connection**
   ```bash
   # Test connection
   python -c "from src.backend.core.database import engine; print('Database connected successfully')"
   ```

3. **Start the Application**
   ```bash
   # Backend
   python -m uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000
   
   # Frontend
   cd frontend && bun run dev
   ```

4. **Test Login**
   - Navigate to `http://localhost:3000`
   - Login with `user@zeblit.com` / `password123`

## Troubleshooting

### Permission Errors
```bash
# Grant permissions to user
psql -U postgres -d zeblit_production -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zeblit;"
psql -U postgres -d zeblit_production -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zeblit;"
```

### Extension Errors
```bash
# Install extensions as superuser
psql -U postgres -d zeblit_production -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
psql -U postgres -d zeblit_production -c "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";"
```

### Connection Issues
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check port: `sudo netstat -tlnp | grep :5432`
- Verify pg_hba.conf allows connections
- Check firewall settings

### Import Errors
- Ensure database is empty before import
- Check PostgreSQL version compatibility
- Verify file permissions on SQL dump
- Check disk space availability

## Maintenance

### Regular Backups
```bash
# Create backup
pg_dump -U postgres -d zeblit_production > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump -U postgres -d zeblit_production | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Update Statistics
```bash
# Update table statistics
psql -U postgres -d zeblit_production -c "ANALYZE;"
```

### Monitor Performance
```bash
# Check slow queries
psql -U postgres -d zeblit_production -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## Security Notes

- Change default passwords immediately after import
- Review and update JWT secrets
- Configure proper firewall rules
- Enable SSL/TLS for production
- Regular security updates
- Monitor audit logs

## Support

For issues with the database dump or import process:
1. Check the troubleshooting section above
2. Verify PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-*.log`
3. Review application logs in `logs/` directory
4. Check the main project documentation

## Version Information

- Database Schema Version: 621c2ea7c143
- Compatible with: Zeblit AI Development Platform v1.0+
- PostgreSQL Version: 16+
- Last Updated: 2024-01-XX 