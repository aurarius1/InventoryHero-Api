echo "creating user $PUID:$PGID"
addgroup -g "$PGID" inventoryhero
adduser -u "$PUID" -D inventoryhero -G inventoryhero
chown -R inventoryhero:inventoryhero /app
exec su inventoryhero -c "gunicorn --bind 0.0.0.0:5000 app:app"