#/bin/bash -e

# VERSION/PRERELEASE/BUILD are exported to follow with our standard of exposing them as env vars. They are not used.
CORE_TAG_NAME="3.5m1"
curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-packager/${PACKAGER_BRANCH-$CORE_TAG_NAME}/common/provision.sh -o ./common-provision.sh &&
source common-provision.sh

AWS_ACCESS_KEY_ID=$1
AWS_ACCESS_KEY=$2
AMQP_INFLUX_BRANCH=$3
PACKAGER_BRANCH=$4

install_common_prereqs &&

rm -rf cloudify-amqp-influxdb
git clone https://github.com/cloudify-cosmo/cloudify-amqp-influxdb.git
cd cloudify-amqp-influxdb
git checkout ${AMQP_INFLUX_BRANCH-$CORE_TAG_NAME}
cd packaging/amqpinflux/omnibus
git tag -d $CORE_TAG_NAME
NEW_TAG_NAME="${VERSION}.${PRERELEASE}"
git tag $NEW_TAG_NAME
omnibus build cloudify-amqp-influxdb && result="success"
while [ $? -ne 0 ]; do !!; done
cd pkg
cat *.json || exit 1
rm -f version-manifest.json

[ "$result" == "success" ] && create_md5 "rpm" &&
[ -z ${AWS_ACCESS_KEY} ] || upload_to_s3 "rpm" && upload_to_s3 "md5" && upload_to_s3 "json"
