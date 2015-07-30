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

import unittest
import threading
import json
import uuid
import time

import pika
from influxdb.influxdb08 import InfluxDBClient

from amqp_influxdb import (InfluxDBPublisher,
                           AMQPTopicConsumer)


influx_database = 'influx'
amqp_exchange = 'exchange'
routing_key = 'routing_key'


class Test(unittest.TestCase):

    def test(self):

        def start():
            publisher = InfluxDBPublisher(
                database=influx_database,
                host='localhost')
            consumer = AMQPTopicConsumer(
                exchange=amqp_exchange,
                routing_key=routing_key,
                message_processor=publisher.process)
            consumer.consume()

        thread = threading.Thread(target=start)
        thread.daemon = True

        thread.start()
        time.sleep(5)
        event_id = str(uuid.uuid4())
        publish_event(event_id)
        thread.join(3)
        self.assertTrue(find_event(event_id), 'event not found in influxdb')


def publish_event(unique_id):

    event = {
        'node_id': 'node_id',
        'node_name': 'node_name',
        'deployment_id': unique_id,
        'name': 'name',
        'path': 'path',
        'metric': 100,
        'unit': '',
        'type': 'type',
    }

    credentials = pika.PlainCredentials('cloudify', 'c10udify')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost', credentials=credentials))
    channel = connection.channel()
    channel.exchange_declare(exchange=amqp_exchange,
                             type='topic',
                             durable=False,
                             auto_delete=True,
                             internal=False)
    channel.basic_publish(exchange=amqp_exchange,
                          routing_key=routing_key,
                          body=json.dumps(event))
    channel.close()
    connection.close()


def find_event(unique_id):
    client = InfluxDBClient('localhost', 8086, 'root', 'root', influx_database)
    results = client.query('select * from /{0}/ limit 1'.format(unique_id))
    return bool(len(results))
