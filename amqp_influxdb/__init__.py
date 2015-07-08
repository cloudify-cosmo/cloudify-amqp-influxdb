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

import json
import logging
import time

import requests
import pika
from pika.exceptions import AMQPConnectionError


D_CONN_ATTEMPTS = 12
D_RETRY_DELAY = 5
BATCH_SIZE = 100
MAX_BATCH_DELAY = 5


logging.basicConfig()
logger = logging.getLogger('amqp_influx')


class AMQPTopicConsumer(object):

    def __init__(self,
                 exchange,
                 routing_key,
                 message_processor,
                 connection_parameters=None):
        self.message_processor = message_processor

        connection_parameters = connection_parameters or {}

        if 'credentials' not in connection_parameters:
            connection_parameters['credentials'] = \
                pika.PlainCredentials('cloudify', 'cl10dify')

        # add retry with try/catch because Pika currently ignoring these
        # connection parameters when using BlockingConnection:
        # https://github.com/pika/pika/issues/354
        attempts = connection_parameters.get('connection_attempts',
                                             D_CONN_ATTEMPTS)
        timeout = connection_parameters.get('retry_delay', D_RETRY_DELAY)
        for _ in range(attempts):
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(**connection_parameters))
            except AMQPConnectionError:
                time.sleep(timeout)
            else:
                break
        else:
            raise AMQPConnectionError

        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=exchange,
                                      type='topic',
                                      durable=False,
                                      auto_delete=True,
                                      internal=False)
        result = self.channel.queue_declare(
            auto_delete=True,
            durable=False,
            exclusive=False)
        queue = result.method.queue
        self.channel.queue_bind(exchange=exchange,
                                queue=queue,
                                routing_key=routing_key)
        self.channel.basic_consume(self._process,
                                   queue,
                                   no_ack=True)

    def consume(self):
        self.channel.start_consuming()

    def _process(self, channel, method, properties, body):
        try:
            parsed_body = json.loads(body)
            self.message_processor(parsed_body)
        except Exception as e:
            logger.warn('Failed message processing: {0}'.format(e))


class InfluxDBPublisher(object):

    columns = ["value", "unit", "type"]

    def __init__(self,
                 database,
                 host='localhost',
                 port=8086,
                 user='root',
                 password='root',
                 batch_size=BATCH_SIZE,
                 max_batch_delay=MAX_BATCH_DELAY):
        self.database = database
        self.batch_size = batch_size
        self.max_batch_delay = max_batch_delay
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.url = 'http://{0}:{1}/db/{2}/series'.format(self.host,
                                                         self.port,
                                                         self.database)
        self.params = {'u': self.user, 'p': self.password}
        self.current_batch_size = 0
        self.current_batch = {}
        self.last_batch_time = time.time()

    def process(self, event):
        name = self._event_name(event)
        if name not in self.current_batch:
            self.current_batch[name] = []
        points = self.current_batch[name]
        points.append(self._event_point(event))
        self.current_batch_size += 1

        if (self.current_batch_size < self.batch_size and
                time.time() < self.last_batch_time + self.max_batch_delay):
            return

        data = json.dumps(self._build_body())
        self.current_batch_size = 0
        self.current_batch = {}
        response = requests.post(
            self.url,
            data=data,
            params=self.params,
            headers={
                'Content-Type': 'application/json'
            })
        self.last_batch_time = time.time()
        if response.status_code != 200:
            raise RuntimeError('influxdb response code: {0}'
                               .format(response.status_code))

    def _build_body(self):
        body = []
        for name, points in self.current_batch.iteritems():
            body.append({
                'name': name,
                'points': points,
                'columns': self.columns
            })
        return body

    @staticmethod
    def _event_name(event):
        return '{0}.{1}.{2}.{3}_{4}'.format(
            event['deployment_id'],
            event['node_name'],
            event['node_id'],
            event['name'],
            event['path'])

    @staticmethod
    def _event_point(event):
        return event['metric'], event['unit'], event['type']
