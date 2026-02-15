# Database Scripts

Utility scripts for database initialization and management.

## Scripts Overview

### 1. `init_database.py`
**Purpose**: Complete database initialization workflow

**Usage**:
```bash
python scripts/init_database.py
```

**What it does**:
1. ✅ Checks database connection
2. 🔧 Creates PostgreSQL extensions (vector, pgcrypto, etc.)
3. 📦 Runs Alembic migrations
4. 👥 Seeds default roles
5. 👤 Optionally creates admin user

**Prerequisites**:
- PostgreSQL 15+ running
- Database created: `createdb psychiatric_ehr`
- `.env` file configured

---

### 2. `seed_roles.py`
**Purpose**: Seed default RBAC roles and permissions

**Usage**:
```bash
python scripts/seed_roles.py
```

**Roles created**:
- `SUPER_ADMIN` - Full system access
- `PSYCHOLOGIST` - Clinical practitioner access
- `PSYCHIATRIST` - Medical practitioner with prescribing
- `THERAPIST` - Limited clinical access
- `ADMIN_STAFF` - Administrative functions
- `PATIENT` - Patient portal (own data only)
- `RESEARCHER` - Anonymized data access

**Safe to run multiple times**: Skips existing roles

---

### 3. `create_admin.py`
**Purpose**: Create initial super admin user

**Usage**:

**Interactive mode** (recommended):
```bash
python scripts/create_admin.py
```

**Non-interactive mode** (for automation):
```bash
python scripts/create_admin.py admin@example.com admin_username SecureP@ssw0rd123
```

**Password requirements**:
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)

**Prerequisites**:
- Database migrated
- Roles seeded (run `seed_roles.py` first)

**Security notes**:
- Passwords are hashed with bcrypt
- Admin account is auto-verified
- MFA should be enabled after first login

---

## Quick Start

### First-time setup:

```bash
# 1. Create database
createdb psychiatric_ehr

# 2. Enable extensions (optional, init_database.py will do this)
psql psychiatric_ehr -c "CREATE EXTENSION vector;"
psql psychiatric_ehr -c "CREATE EXTENSION pgcrypto;"

# 3. Run initialization (does everything)
python scripts/init_database.py
```

### Manual step-by-step:

```bash
# 1. Run migrations
alembic upgrade head

# 2. Seed roles
python scripts/seed_roles.py

# 3. Create admin
python scripts/create_admin.py
```

---

## Troubleshooting

### "Cannot connect to database"
```bash
# Check PostgreSQL is running
pg_isready

# Check connection string in .env
cat .env | grep DATABASE_URL
```

### "SUPER_ADMIN role not found"
```bash
# Run role seeding first
python scripts/seed_roles.py
```

### "User already exists"
The email or username is already taken. Use different credentials or check existing users:
```sql
SELECT id, email, username FROM users;
```

### Permission errors
Ensure your database user has sufficient privileges:
```sql
GRANT ALL PRIVILEGES ON DATABASE psychiatric_ehr TO your_user;
```

---

## Advanced Usage

### Reset database (CAUTION: DELETES ALL DATA)

```bash
# Drop all tables
alembic downgrade base

# Re-run migrations
alembic upgrade head

# Re-seed roles
python scripts/seed_roles.py

# Create admin
python scripts/create_admin.py
```

### Check migration status

```bash
# Current version
alembic current

# Migration history
alembic history

# Pending migrations
alembic heads
```

### Create new admin (after initial setup)

```bash
python scripts/create_admin.py
```

---

## Security Best Practices

1. **Strong passwords**: Use password manager for admin credentials
2. **Enable MFA**: Configure TOTP 2FA after first login
3. **Limit admin accounts**: Only create necessary admin users
4. **Audit regularly**: Check audit_logs for admin activities
5. **Rotate credentials**: Change admin passwords periodically

---

## Database Schema Version

These scripts work with Alembic migration: `001_initial`

Schema includes:
- 15+ tables (users, roles, patients, encounters, etc.)
- FHIR-compliant resources
- pgvector for AI/RAG
- Audit logging
- ROW-level security ready

For detailed schema documentation, see [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md)
