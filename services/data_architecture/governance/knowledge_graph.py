import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncpg
import json

logger = logging.getLogger(__name__)

@dataclass
class Entity:
    id: str
    type: str
    properties: Dict[str, Any]

@dataclass
class Relationship:
    id: str
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any]

class KnowledgeGraphManager:
    """
    Knowledge graph manager for storing and querying relationships between entities.
    Provides graph-based reasoning capabilities for AI agents.
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            await self._create_tables()
            logger.info("Knowledge graph manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize knowledge graph: {str(e)}")
    
    async def _create_tables(self):
        """Create knowledge graph tables if they don't exist"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS kg_entities (
                    id VARCHAR(255) PRIMARY KEY,
                    type VARCHAR(100) NOT NULL,
                    properties JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS kg_relationships (
                    id VARCHAR(255) PRIMARY KEY,
                    source_id VARCHAR(255) REFERENCES kg_entities(id),
                    target_id VARCHAR(255) REFERENCES kg_entities(id),
                    type VARCHAR(100) NOT NULL,
                    properties JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entities_type ON kg_entities(type);
                CREATE INDEX IF NOT EXISTS idx_relationships_type ON kg_relationships(type);
                CREATE INDEX IF NOT EXISTS idx_relationships_source ON kg_relationships(source_id);
                CREATE INDEX IF NOT EXISTS idx_relationships_target ON kg_relationships(target_id);
            """)
    
    async def create_entity(self, entity: Entity) -> bool:
        """Create or update an entity in the knowledge graph"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO kg_entities (id, type, properties, updated_at)
                    VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO UPDATE SET
                        type = EXCLUDED.type,
                        properties = EXCLUDED.properties,
                        updated_at = CURRENT_TIMESTAMP
                """, entity.id, entity.type, json.dumps(entity.properties))
                
                logger.info(f"Created/updated entity {entity.id}")
                return True
        except Exception as e:
            logger.error(f"Error creating entity {entity.id}: {str(e)}")
            return False
    
    async def create_relationship(self, relationship: Relationship) -> bool:
        """Create a relationship between entities"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO kg_relationships (id, source_id, target_id, type, properties)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO UPDATE SET
                        type = EXCLUDED.type,
                        properties = EXCLUDED.properties
                """, relationship.id, relationship.source_id, relationship.target_id,
                    relationship.type, json.dumps(relationship.properties))
                
                logger.info(f"Created relationship {relationship.id}")
                return True
        except Exception as e:
            logger.error(f"Error creating relationship {relationship.id}: {str(e)}")
            return False
    
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT id, type, properties FROM kg_entities WHERE id = $1",
                    entity_id
                )
                
                if row:
                    return Entity(
                        id=row['id'],
                        type=row['type'],
                        properties=row['properties']
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting entity {entity_id}: {str(e)}")
            return None
    
    async def find_related_entities(self, 
                                  entity_id: str, 
                                  relationship_type: Optional[str] = None,
                                  direction: str = 'both') -> List[Tuple[Entity, Relationship]]:
        """Find entities related to a given entity"""
        try:
            async with self.pool.acquire() as conn:
                if direction == 'outgoing':
                    query = """
                        SELECT e.id, e.type, e.properties, r.id as rel_id, r.type as rel_type, r.properties as rel_props
                        FROM kg_entities e
                        JOIN kg_relationships r ON e.id = r.target_id
                        WHERE r.source_id = $1
                    """
                elif direction == 'incoming':
                    query = """
                        SELECT e.id, e.type, e.properties, r.id as rel_id, r.type as rel_type, r.properties as rel_props
                        FROM kg_entities e
                        JOIN kg_relationships r ON e.id = r.source_id
                        WHERE r.target_id = $1
                    """
                else:  # both
                    query = """
                        SELECT e.id, e.type, e.properties, r.id as rel_id, r.type as rel_type, r.properties as rel_props
                        FROM kg_entities e
                        JOIN kg_relationships r ON (e.id = r.target_id OR e.id = r.source_id)
                        WHERE (r.source_id = $1 OR r.target_id = $1) AND e.id != $1
                    """
                
                params = [entity_id]
                if relationship_type:
                    query += " AND r.type = $2"
                    params.append(relationship_type)
                
                rows = await conn.fetch(query, *params)
                
                results = []
                for row in rows:
                    entity = Entity(
                        id=row['id'],
                        type=row['type'],
                        properties=row['properties']
                    )
                    
                    relationship = Relationship(
                        id=row['rel_id'],
                        source_id=entity_id if direction != 'incoming' else row['id'],
                        target_id=row['id'] if direction != 'incoming' else entity_id,
                        type=row['rel_type'],
                        properties=row['rel_props']
                    )
                    
                    results.append((entity, relationship))
                
                return results
        except Exception as e:
            logger.error(f"Error finding related entities for {entity_id}: {str(e)}")
            return []
    
    async def query_entities(self, 
                           entity_type: Optional[str] = None,
                           property_filters: Optional[Dict[str, Any]] = None) -> List[Entity]:
        """Query entities by type and properties"""
        try:
            async with self.pool.acquire() as conn:
                query = "SELECT id, type, properties FROM kg_entities WHERE 1=1"
                params = []
                param_count = 0
                
                if entity_type:
                    param_count += 1
                    query += f" AND type = ${param_count}"
                    params.append(entity_type)
                
                if property_filters:
                    for key, value in property_filters.items():
                        param_count += 1
                        query += f" AND properties->>${param_count} = ${param_count + 1}"
                        params.extend([key, str(value)])
                        param_count += 1
                
                rows = await conn.fetch(query, *params)
                
                return [
                    Entity(
                        id=row['id'],
                        type=row['type'],
                        properties=row['properties']
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error querying entities: {str(e)}")
            return []
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
