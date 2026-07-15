set -e

echo "Esperando a que el maestro esté disponible..."
until mysql -h mysql_principal -uroot -proot -e "SELECT 1" &> /dev/null; do
  sleep 2
done

echo "Configurando replicación (esclavo apuntando al maestro)..."
mysql -uroot -proot <<EOF
CHANGE MASTER TO
  MASTER_HOST='mysql_principal',
  MASTER_USER='repl',
  MASTER_PASSWORD='repl_pass123',
  MASTER_AUTO_POSITION=1;
START SLAVE;
EOF

echo "Replicación configurada correctamente."