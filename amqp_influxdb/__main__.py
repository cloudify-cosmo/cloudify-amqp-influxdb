########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
############

import argparse

from amqp_influxdb import (
    InfluxDBPublisher,
    AMQPTopicConsumer,
    BATCH_SIZE,
    MAX_BATCH_DELAY,
    BROKER_PORT_SSL,
    BROKER_PORT_NO_SSL,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--amqp-hostname', required=False,
                        default='localhost')
    parser.add_argument('--amqp-username', required=False,
                        default='guest')
    parser.add_argument('--amqp-password', required=False,
                        default='guest')
    parser.add_argument('--amqp-ssl-enabled', required=False)
    parser.add_argument('--amqp-ca-cert-path', required=False,
                        default='')
    parser.add_argument('--amqp-exchange', required=True)
    parser.add_argument('--amqp-routing-key', required=True)
    parser.add_argument('--influx-hostname', required=False,
                        default='localhost')
    parser.add_argument('--influx-database', required=True)
    parser.add_argument('--influx-batch-size', type=int, default=BATCH_SIZE)
    parser.add_argument('--influx-max-batch-delay', type=int,
                        default=MAX_BATCH_DELAY)
    return parser.parse_args()


def main():
    args = parse_args()

    publisher = InfluxDBPublisher(
        database=args.influx_database,
        host=args.influx_hostname,
        batch_size=args.influx_batch_size,
        max_batch_delay=args.influx_max_batch_delay)

    # This arg is a string for ease of use with the manager blueprint
    if args.amqp_ssl_enabled.lower() == 'true':
        ssl_enabled = True
        amqp_port = BROKER_PORT_SSL
    else:
        ssl_enabled = False
        amqp_port = BROKER_PORT_NO_SSL

    conn_params = {
        'host': args.amqp_hostname,
        'port': amqp_port,
        'connection_attempts': 12,
        'retry_delay': 5,
        'credentials': {
            'username': args.amqp_username,
            'password': args.amqp_password,
        },
        'ca_path': args.amqp_ca_cert_path,
        'ssl': ssl_enabled,
    }
    consumer = AMQPTopicConsumer(
        exchange=args.amqp_exchange,
        routing_key=args.amqp_routing_key,
        message_processor=publisher.process,
        connection_parameters=conn_params)
    consumer.consume()


if __name__ == '__main__':
    main()
