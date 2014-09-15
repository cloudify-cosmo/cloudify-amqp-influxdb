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

import pika

from amqp_to_influx import (InfluxDBPublisher,
                            AMQPTopicConsumer)


influx_database = 'influx'
amqp_exchange = 'exchange'
routing_key = 'routing_key'


class Test(unittest.TestCase):

    def test(self):

        def start():
            publisher = InfluxDBPublisher(
                database=influx_database,
                host='11.0.0.7')
            consumer = AMQPTopicConsumer(
                exchange=amqp_exchange,
                routing_key=routing_key,
                message_processor=publisher.process)
            consumer.consume()

        thread = threading.Thread(target=start)
        thread.daemon = True

        thread.start()
        publish_event()
        thread.join()


def publish_event():

    event = {
        'node_id': 'node_id',
        'node_name': 'node_name',
        'deployment_id': 'deployment_id',
        'name': 'name',
        'path': 'path',
        'metric': 100,
        'unit': '',
        'type': 'type',
    }

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange=amqp_exchange,
                             type='topic',
                             durable=False,
                             auto_delete=True,
                             internal=False)
    channel.queue_declare(
        queue=routing_key,
        auto_delete=True,
        durable=False,
        exclusive=False)
    channel.queue_bind(exchange=amqp_exchange,
                       queue=routing_key,
                       routing_key=routing_key)
    channel.basic_publish(exchange=amqp_exchange,
                          routing_key=routing_key,
                          body=json.dumps(event))
    channel.close()
    connection.close()
