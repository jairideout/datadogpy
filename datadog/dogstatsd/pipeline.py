# Unless explicitly stated otherwise all files in this repository are licensed under the BSD-3-Clause License.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2015-Present Datadog, Inc


# stdlib
from random import random
import logging
import os
import socket
import errno
import time
from threading import Lock

# datadog
from datadog.dogstatsd.context import TimedContextManagerDecorator
from datadog.dogstatsd.route import get_default_route
from datadog.util.compat import text
from datadog.util.config import get_pkg_version
from datadog.util.format import normalize_tags

class Pipeline(object, telemetry = None):

    MAX_SIZE = 1452
    MAX_ENTRY = 50

    def __init__(self, send):
        self.buffer = []
        self._max_size = MAX_SIZE
        self._max_entry = MAX_ENTRY
        self._size = 0
        self._send = send

    def _report(self, metric, metric_type, value, tags, sample_rate):
        """
        Create a metric packet and send it.

        More information about the packets' format: http://docs.datadoghq.com/guides/dogstatsd/
        """
        if value is None:
            return

        if self._telemetry:
            self.metrics_count += 1

        if sample_rate is None:
            sample_rate = self.default_sample_rate

        if sample_rate != 1 and random() > sample_rate:
            return

        # Resolve the full tag list
        tags = self._add_constant_tags(tags)
        payload = self._serialize_metric(metric, metric_type, value, tags, sample_rate)

        # Append to the buffer
        self.buffer.append(payload)
        
        #self._send(payload)
        #if len(self.buffer) >= self.max_buffer_size:
        #    self._flush_buffer()
    
    def _flush_buffer(self):
        self._send("\n".join(self.buffer))
        self.buffer = []

    def _serialize_metric(self, metric, metric_type, value, tags, sample_rate=1):
        # Create/format the metric packet
        return "%s%s:%s|%s%s%s" % (
            (self.namespace + ".") if self.namespace else "",
            metric,
            value,
            metric_type,
            ("|@" + text(sample_rate)) if sample_rate != 1 else "",
            ("|#" + ",".join(normalize_tags(tags))) if tags else "",
        )

    # def get_payload_with_telemetry(self):
