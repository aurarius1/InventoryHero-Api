echo "creating user $PUID:$PGID"
groupmod -g "$PGID" -o iventoryhero
usermod -u "$PUID" -o iventoryhero
chown -R iventoryhero:iventoryhero ./files/
chown vikunja:vikunja .
exec su vikunja -c /app/vikunja/vikunja "$@"