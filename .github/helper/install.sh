#!/bin/bash

set -e

echo "=== CI Setup frappe + erpnext + etsy ==="

cd ~ || exit

echo "Updating system & installing dependencies..."
sudo apt update
sudo apt remove mysql-server mysql-client
sudo apt install libcups2-dev redis-server mariadb-client libmariadb-dev

pip install frappe-bench

frappeuser=${FRAPPE_USER:-"frappe"}
frappebranch=${FRAPPE_BRANCH:-"version-15"}

echo "Cloning Frappe..."
git clone "https://github.com/${frappeuser}/frappe" --branch "${frappebranch}" --depth 1

echo "Initializing bench..."
bench init --skip-assets --frappe-path ~/frappe --python "$(which python)" frappe-bench

# Copy site config
mkdir ~/frappe-bench/sites/test_site
cp -r "${GITHUB_WORKSPACE}/.github/helper/site_config.json" ~/frappe-bench/sites/test_site/site_config.json

# MariaDB tuning
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL character_set_server = 'utf8mb4'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

# Create DB user
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE USER 'test_frappe'@'localhost' IDENTIFIED BY 'test_frappe'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE DATABASE test_frappe"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "GRANT ALL PRIVILEGES ON \`test_frappe\`.* TO 'test_frappe'@'localhost'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "FLUSH PRIVILEGES"

# Install wkhtmltopdf (needed for PDF tests)
install_whktml() {
    wget -O /tmp/wkhtmltox.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb
    sudo apt install /tmp/wkhtmltox.deb
}
install_whktml &
wkpid=$!

cd ~/frappe-bench || exit

# sed -i 's/watch:/# watch:/g' Procfile
# sed -i 's/schedule:/# schedule:/g' Procfile
# sed -i 's/socketio:/# socketio:/g' Procfile
# sed -i 's/redis_socketio:/# redis_socketio:/g' Procfile

echo "Getting apps..."
bench get-app erpnext --branch "${frappebranch}"
bench get-app etsy "${GITHUB_WORKSPACE}"

echo "Installing Python requirements..."
bench setup requirements --dev

wait $wkpid

# bench start &>> ~/frappe-bench/bench_start.log &
# CI=Yes bench build --app frappe &

echo "Setting up test_site..."
bench --site test_site reinstall --yes

# Explicit install is much more reliable than required_apps in CI
bench --site test_site install-app erpnext
bench --verbose --site test_site install-app etsy

# Safety net
bench --site test_site migrate

echo "=== Test site setup completed successfully! ==="
