import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import threading

logger = logging.getLogger(__name__)

@dataclass
class StreamEvent:
    event_id: str
    event_type: str
    source_service: str
    timestamp: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class KafkaEventManager:
    """
    Real-time event streaming manager using Apache Kafka.
    Handles event publishing, consumption, and routing for the AOS system.
    """
    
    def __init__(self, kafka_config: Dict[str, Any]):
        self.kafka_config = kafka_config
        self.bootstrap_servers = kafka_config.get('bootstrap_servers', 'kafka:29092')
        self.event_handlers: Dict[str, Dict[str, Callable]] = {}
        self.consumers: Dict[str, KafkaConsumer] = {}
        self.producer = None
        self.running = False
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                retry_backoff_ms=1000
            )
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {str(e)}")
        
        for topic_config in self.kafka_config.get('topics', []):
            try:
                consumer = KafkaConsumer(
                    topic_config['name'],
                    bootstrap_servers=self.bootstrap_servers,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    key_deserializer=lambda k: k.decode('utf-8') if k else None,
                    auto_offset_reset='latest',
                    enable_auto_commit=True,
                    group_id=f"aos_{topic_config['name']}_consumer"
                )
                self.consumers[topic_config['name']] = consumer
                logger.info(f"Kafka consumer initialized for topic: {topic_config['name']}")
            except Exception as e:
                logger.error(f"Failed to initialize consumer for topic {topic_config['name']}: {str(e)}")
    
    async def publish_event(self, 
                          topic: str,
                          event: StreamEvent,
                          partition_key: Optional[str] = None) -> bool:
        """Publish an event to Kafka topic"""
        
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
        
        try:
            event_data = asdict(event)
            
            future = self.producer.send(
                topic,
                value=event_data,
                key=partition_key
            )
            
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Event {event.event_id} published to topic {topic} "
                       f"(partition: {record_metadata.partition}, offset: {record_metadata.offset})")
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error publishing event {event.event_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error publishing event {event.event_id}: {str(e)}")
            return False
    
    def register_event_handler(self, 
                             topic: str,
                             event_type: str,
                             handler: Callable[[StreamEvent], Any]):
        """Register an event handler for specific topic and event type"""
        
        if topic not in self.event_handlers:
            self.event_handlers[topic] = {}
        
        self.event_handlers[topic][event_type] = handler
        logger.info(f"Registered handler for topic '{topic}', event type '{event_type}'")
    
    def start_consuming(self):
        """Start consuming events from all configured topics"""
        self.running = True
        
        for topic, consumer in self.consumers.items():
            thread = threading.Thread(
                target=self._consume_topic,
                args=(topic, consumer),
                daemon=True
            )
            thread.start()
            logger.info(f"Started consumer thread for topic: {topic}")
    
    def stop_consuming(self):
        """Stop consuming events"""
        self.running = False
        
        for consumer in self.consumers.values():
            consumer.close()
        
        if self.producer:
            self.producer.close()
        
        logger.info("Stopped all Kafka consumers and producer")
    
    def _consume_topic(self, topic: str, consumer: KafkaConsumer):
        """Consume events from a specific topic"""
        logger.info(f"Starting to consume from topic: {topic}")
        
        try:
            for message in consumer:
                if not self.running:
                    break
                
                try:
                    event_data = message.value
                    event = StreamEvent(
                        event_id=event_data['event_id'],
                        event_type=event_data['event_type'],
                        source_service=event_data['source_service'],
                        timestamp=event_data['timestamp'],
                        data=event_data['data'],
                        metadata=event_data.get('metadata')
                    )
                    
                    if topic in self.event_handlers:
                        if event.event_type in self.event_handlers[topic]:
                            handler = self.event_handlers[topic][event.event_type]
                            asyncio.create_task(self._execute_event_handler(handler, event))
                        else:
                            logger.debug(f"No handler for event type '{event.event_type}' in topic '{topic}'")
                    else:
                        logger.debug(f"No handlers registered for topic '{topic}'")
                        
                except Exception as e:
                    logger.error(f"Error processing message from topic {topic}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error consuming from topic {topic}: {str(e)}")
    
    async def _execute_event_handler(self, handler: Callable, event: StreamEvent):
        """Execute event handler with error handling"""
        
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(f"Error executing handler for event {event.event_id}: {str(e)}")
            
            error_event = StreamEvent(
                event_id=f"error_{event.event_id}",
                event_type='handler_error',
                source_service='kafka_manager',
                timestamp=datetime.utcnow().isoformat(),
                data={
                    'original_event_id': event.event_id,
                    'error_message': str(e),
                    'handler_name': handler.__name__
                }
            )
            
            await self.publish_event('system_errors', error_event)
    
    async def create_event(self,
                         event_type: str,
                         source_service: str,
                         data: Dict[str, Any],
                         metadata: Optional[Dict[str, Any]] = None) -> StreamEvent:
        """Create a new stream event with auto-generated ID and timestamp"""
        
        import uuid
        
        return StreamEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source_service=source_service,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            metadata=metadata
        )
    
    def get_topic_info(self) -> Dict[str, Any]:
        """Get information about configured topics"""
        return {
            'configured_topics': [topic['name'] for topic in self.kafka_config.get('topics', [])],
            'active_consumers': list(self.consumers.keys()),
            'registered_handlers': {
                topic: list(handlers.keys()) 
                for topic, handlers in self.event_handlers.items()
            },
            'producer_status': 'active' if self.producer else 'inactive',
            'consuming_status': 'running' if self.running else 'stopped'
        }
