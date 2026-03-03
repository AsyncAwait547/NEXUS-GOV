"""Kafka/Redpanda Bridge — Abstraction layer for distributed event streaming."""
import asyncio
import json
import logging
import time
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("nexus.kafka")


class KafkaBridge:
    """
    Abstraction over Redis Streams that can optionally route to Kafka/Redpanda.
    When USE_KAFKA=true, messages are produced to Kafka topics instead of Redis Streams.
    Acts as a drop-in enhancement for the EventBus.
    """

    TOPIC_MAP = {
        "nexus:broadcast": "nexus.events.broadcast",
        "nexus:conflicts": "nexus.events.conflicts",
        "nexus:timeline": "nexus.events.timeline",
    }

    def __init__(self, broker_url: str, enabled: bool = False):
        self.broker_url = broker_url
        self.enabled = enabled
        self._producer = None
        self._consumer = None
        self._running = False

    async def initialize(self):
        """Initialize Kafka producer and consumer."""
        if not self.enabled:
            logger.info("[Kafka] Kafka bridge disabled — using Redis Streams only")
            return

        try:
            from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.broker_url,
                value_serializer=lambda v: json.dumps(v, default=str).encode(),
                key_serializer=lambda k: k.encode() if k else None,
            )
            await self._producer.start()
            self._running = True
            logger.info(f"[Kafka] Producer connected to {self.broker_url}")

        except ImportError:
            logger.warning("[Kafka] aiokafka not installed — Kafka bridge disabled")
            self.enabled = False
        except Exception as e:
            logger.warning(f"[Kafka] Failed to connect: {e} — falling back to Redis Streams")
            self.enabled = False

    async def close(self):
        """Shutdown Kafka connections."""
        self._running = False
        if self._producer:
            await self._producer.stop()
            logger.info("[Kafka] Producer disconnected")

    async def produce(self, stream: str, message: dict, key: str = None):
        """
        Produce a message to Kafka if enabled.
        Returns True if the message was sent to Kafka, False if it should go to Redis.
        """
        if not self.enabled or not self._producer:
            return False

        topic = self.TOPIC_MAP.get(stream, stream.replace(":", "."))
        try:
            await self._producer.send_and_wait(topic, value=message, key=key)
            logger.debug(f"[Kafka] Produced to {topic}: {key}")
            return True
        except Exception as e:
            logger.error(f"[Kafka] Produce error on {topic}: {e}")
            return False

    async def create_consumer(self, topics: List[str], group_id: str = "nexus-group") -> Optional[object]:
        """Create a Kafka consumer for the given topics."""
        if not self.enabled:
            return None

        try:
            from aiokafka import AIOKafkaConsumer

            kafka_topics = [self.TOPIC_MAP.get(t, t.replace(":", ".")) for t in topics]
            consumer = AIOKafkaConsumer(
                *kafka_topics,
                bootstrap_servers=self.broker_url,
                group_id=group_id,
                value_deserializer=lambda v: json.loads(v.decode()),
                auto_offset_reset="latest",
            )
            await consumer.start()
            return consumer
        except Exception as e:
            logger.error(f"[Kafka] Consumer creation failed: {e}")
            return None

    async def consume_loop(self, topics: List[str], handler: Callable, group_id: str = "nexus-group"):
        """Background loop that consumes from Kafka and calls the handler."""
        consumer = await self.create_consumer(topics, group_id)
        if not consumer:
            return

        try:
            async for msg in consumer:
                try:
                    await handler(msg.topic, msg.value)
                except Exception as e:
                    logger.error(f"[Kafka] Handler error: {e}")
        finally:
            await consumer.stop()

    def get_status(self) -> dict:
        """Return Kafka bridge status."""
        return {
            "enabled": self.enabled,
            "connected": self._running,
            "broker": self.broker_url if self.enabled else None,
        }
