#/bin/bash
set -e

# Usage
if [ -z "$1" ]; then
    printf "\nInfluxDB version not provided.\n"
    printf "usage: %s <INFLUXDB VERSION>\n" "$0"
    exit 1
fi

# Download
FILEURL="http://s3.amazonaws.com/influxdb/influxdb_$1_amd64.deb"
TEMPFILE=$(mktemp --suffix=.deb)
printf "Trying to download $FILEURL, saving as $TEMPFILE\n"
curl --fail --progress-bar -L "http://s3.amazonaws.com/influxdb/influxdb_$1_amd64.deb" -o "$TEMPFILE"

# Install & start
printf "Installing InfluxDB\n"
dpkg -i $TEMPFILE
service influxdb start

# Create initial db
for i in 1 2 3 4 5 6; do
    if [ "$i" -eq 6 ]; then
        printf "Initializing new db failed, exiting.\n"
        exit 1
    fi
    curl --fail 'http://localhost:8086/db?u=root&p=root' -d "{\"name\": \"influx\"}" && break || sleep 2;
done
printf "Finished successfully!\n"