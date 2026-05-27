# Estate Asset Manager - Setup Guide

## Prerequisites

- Python 3.8+
- MySQL 8.0+ (on dbms.blscomputer.work or localhost)
- Git
- Virtual environment (recommended)

## Installation Steps

### 1. Clone the Repository
```bash
git clone git@github.com:barrysmith63/Estate-Asset-Manager.git
cd Estate-Asset-Manager
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database Connection

**Copy the example configuration:**
```bash
cp project_config.example.json project_config.json
```

**Edit `project_config.json` with your database details:**
```json
{
  "database": {
    "host": "dbms.blscomputer.work",
    "port": 3306,
    "user": "your_mysql_user",
    "password": "your_mysql_password",
    "name": "estate_assets"
  },
  "flask": {
    "debug": false,
    "secret_key": "your-secret-key-here"
  },
  "upload": {
    "folder": "uploads/images",
    "max_size_mb": 16
  },
  "connection_pool": {
    "size": 5
  },
  "pagination": {
    "items_per_page": 20
  },
  "cache": {
    "enabled": true,
    "ttl_seconds": 300
  }
}
```

### 5. Create MySQL Database and Tables

**Connect to MySQL server:**
```bash
mysql -h dbms.blscomputer.work -u your_mysql_user -p
```

**Run schema setup:**
```bash
# In MySQL CLI:
source db/schema.sql;
source db/procedures.sql;
```

Or from command line:
```bash
mysql -h dbms.blscomputer.work -u your_mysql_user -p estate_assets < db/schema.sql
mysql -h dbms.blscomputer.work -u your_mysql_user -p estate_assets < db/procedures.sql
```

### 6. Create Required Directories
```bash
mkdir -p uploads/images
chmod 755 uploads/images
```

### 7. Test Database Connection
```bash
python3 -c "from db import init_db_pool; print('✓ Connected!' if init_db_pool() else '✗ Connection failed')"
```

### 8. Run the Application
```bash
python3 app.py
```

Application will start at: `http://localhost:5000`

## Verification Checklist

- [ ] MySQL server is running and accessible
- [ ] Database `estate_assets` is created
- [ ] Tables created: `locations`, `assets`, `video_details`
- [ ] Stored procedures created
- [ ] `project_config.json` configured with correct credentials
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] `uploads/images` directory exists
- [ ] Flask app starts without errors
- [ ] Can access `http://localhost:5000/videos`

## Database Connection Test

Run this to verify connectivity:
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Configuration Options

### Flask Settings
```json
"flask": {
  "debug": false,                    // Set to true for development
  "secret_key": "change-this"        // Change in production
}
```

### Database Settings
```json
"database": {
  "host": "dbms.blscomputer.work",   // Your MySQL server address
  "port": 3306,                       // MySQL port
  "user": "estate_user",              // MySQL username
  "password": "your_password",        // MySQL password
  "name": "estate_assets"             // Database name
}
```

### Connection Pool Settings
```json
"connection_pool": {
  "size": 5                           // Adjust for concurrent users
}
```

**Recommendations:**
- Development: 5 connections
- Production (10-50 users): 10 connections
- Production (50+ users): 20 connections

### Pagination Settings
```json
"pagination": {
  "items_per_page": 20               // Adjust for preference
}
```

**Recommendations:**
- Small screens: 10-15 items
- Standard: 20 items
- Large datasets: 50 items

## Troubleshooting

### "Connection refused" error
- Check if MySQL is running: `mysql -h dbms.blscomputer.work -u root`
- Verify host/port in `project_config.json`
- Check firewall rules

### "Access denied for user" error
- Verify username and password in `project_config.json`
- Ensure user has permissions: `GRANT ALL ON estate_assets.* TO 'user'@'%';`

### "Database does not exist" error
- Create database: `CREATE DATABASE estate_assets;`
- Run schema.sql: `source db/schema.sql;`

### "Procedure does not exist" error
- Run procedures.sql: `source db/procedures.sql;`

### Slow performance
- Check indexes: `SHOW INDEX FROM assets;`
- Increase connection pool size in `project_config.json`
- Check MySQL slow query log

### File upload issues
- Ensure `uploads/images` directory exists
- Check directory permissions: `chmod 755 uploads/images`
- Verify `MAX_CONTENT_LENGTH` setting (default: 16MB)

## Development Tips

### Enable Debug Mode
Edit `project_config.json`:
```json
"flask": {
  "debug": true
}
```

### View Logs
Application logs appear in console with timestamps and levels.

### Test Database Procedures
```bash
mysql -h dbms.blscomputer.work -u your_user -p estate_assets
CALL add_video_asset('Description', NULL, NULL, NULL, NULL, NULL, 'Test Title', NULL, NULL, NULL);
```

### Add Test Data
```sql
INSERT INTO locations (location_name) VALUES ('Living Room');
INSERT INTO locations (location_name) VALUES ('Master Bedroom');
```

## Deployment

### Production Checklist
- [ ] Set `debug: false` in `project_config.json`
- [ ] Use strong `secret_key`
- [ ] Configure production MySQL user with minimal permissions
- [ ] Set up SSL/TLS for database connection
- [ ] Enable MySQL slow query logging
- [ ] Set up log rotation
- [ ] Configure backup strategy
- [ ] Use production WSGI server (Gunicorn/uWSGI)
- [ ] Set up reverse proxy (Nginx/Apache)

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using uWSGI
```bash
pip install uwsgi
uwsgi --http :5000 --wsgi-file app.py --callable app --processes 4 --threads 2
```

## Next Steps

1. Add more locations via MySQL
2. Test adding/editing videos through web interface
3. Configure regular backups
4. Set up monitoring
5. Customize CSS in `static/css/styles.css`
6. Add authentication layer (optional)

## Support

For issues, check:
1. Application logs in console
2. MySQL error log: `/var/log/mysql/error.log`
3. `PERFORMANCE_IMPROVEMENTS.md` for optimization tips
