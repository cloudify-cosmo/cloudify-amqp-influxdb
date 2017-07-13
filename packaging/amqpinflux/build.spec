%define _rpmdir /tmp


Name:           cloudify-amqp-influx
Version:        %{VERSION}
Release:        %{PRERELEASE}
Summary:        Cloudify's AMQP InfluxDB Broker
Group:          Applications/Multimedia
License:        Apache 2.0
URL:            https://github.com/cloudify-cosmo/cloudify-amqp-influxdb
Vendor:         Gigaspaces Inc.
Prefix:         %{_prefix}
Packager:       Gigaspaces Inc.
BuildRoot:      %{_tmppath}/%{name}-root



%description
Cloudify's Broker pulls Cloudify formatted Metrics from RabbitMQ and posts them in InfluxDB.



%prep

set +e
pip=$(which pip)
set -e

[ ! -z $pip ] || sudo curl --show-error --silent --retry 5 https://bootstrap.pypa.io/get-pip.py | sudo python
sudo yum install -y git python-devel gcc
sudo pip install virtualenv
sudo virtualenv /tmp/env
sudo /tmp/env/bin/pip install setuptools==18.1 && \
sudo /tmp/env/bin/pip install wheel==0.24.0 && \

%build
%install

sudo /tmp/env/bin/pip wheel virtualenv --wheel-dir %{buildroot}/var/wheels/%{name} && \
sudo /tmp/env/bin/pip wheel --wheel-dir=%{buildroot}/var/wheels/%{name} --find-links=%{buildroot}/var/wheels/%{name} https://github.com/cloudify-cosmo/cloudify-amqp-influxdb/archive/%{CORE_BRANCH}.tar.gz && \



%pre
%post

pip install --use-wheel --no-index --find-links=/var/wheels/%{name} virtualenv && \
if [ ! -d "/opt/amqpinflux/env" ]; then virtualenv /opt/amqpinflux/env; fi && \
/opt/amqpinflux/env/bin/pip install --upgrade --force-reinstall --use-wheel --no-index --find-links=/var/wheels/%{name} cloudify-amqp-influxdb --pre


%preun
%postun

rm -rf /var/wheels/${name}



%files

%defattr(-,root,root)
/var/wheels/%{name}/*.whl