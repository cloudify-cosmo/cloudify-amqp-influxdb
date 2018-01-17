
Name:           cloudify-amqp-influx
Version:        %{CLOUDIFY_VERSION}
Release:        %{CLOUDIFY_PACKAGE_RELEASE}%{?dist}
Summary:        Cloudify AMQP InfluxDB Transport
Group:          Applications/Multimedia
License:        Apache 2.0
URL:            https://github.com/cloudify-cosmo/cloudify-amqp-influxdb
Vendor:         Cloudify Platform Ltd.
Packager:       Cloudify Platform Ltd.

BuildRequires:  python >= 2.7, python-virtualenv
Requires:       python >= 2.7, influxdb
Requires(pre):  shadow-utils

%define _venv /opt/amqpinflux/env
%define _user amqpinflux


%description
Pulls Cloudify formatted Metrics from RabbitMQ and posts them in InfluxDB.


%build

virtualenv %_venv

%_venv/bin/pip install --upgrade pip setuptools
%_venv/bin/pip install --upgrade "${RPM_SOURCE_DIR}/"


%install

mkdir -p %{buildroot}/opt/amqpinflux
mv %_venv %{buildroot}/opt/amqpinflux

# Create the log dir
mkdir -p %{buildroot}/var/log/cloudify/influxdb

# Copy static files into place. In order to have files in /packaging/files
# actually included in the RPM, they must have an entry in the %files
# section of this spec file.
cp -R ${RPM_SOURCE_DIR}/packaging/files/* %{buildroot}


%pre

groupadd -fr %_user
getent passwd %_user >/dev/null || useradd -r -g %_user -d /opt/amqpinflux -s /sbin/nologin %_user


%files

%dir %attr(750,%_user,%_user) /opt/amqpinflux
/opt/amqpinflux/*
/opt/amqpinflux_NOTICE.txt
/usr/lib/systemd/system/cloudify-amqpinflux.service

/etc/logrotate.d/cloudify-influxdb
%attr(750,influxdb,adm) /var/log/cloudify/influxdb
