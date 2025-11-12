#!/bin/bash

# Backup script for Equipment Management System
# Run daily via cron: 0 2 * * * /path/to/backup.sh

BACKUP_DIR="/home/django/backups"
PROJECT_DIR="/home/django/equipment_management"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Database backup
echo "Backing up database..."
PGPASSWORD=$(grep DB_PASSWORD $PROJECT_DIR/.env | cut -d '=' -f2) \
pg_dump -h localhost -U equipment_user equipment_db > $BACKUP_DIR/db_$DATE.sql

# Compress database backup
gzip $BACKUP_DIR/db_$DATE.sql

# Backup media files
echo "Backing up media files..."
if [ -d "$PROJECT_DIR/media" ]; then
    tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C $PROJECT_DIR media/
fi

# Backup .env file
echo "Backing up .env file..."
cp $PROJECT_DIR/.env $BACKUP_DIR/env_$DATE

# Remove backups older than 7 days
echo "Cleaning up old backups..."
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"



