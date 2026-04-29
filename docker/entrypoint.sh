#!/bin/bash

mkdir -p /app/data /app/exports /app/backups /app/logs

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
