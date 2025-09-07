import aiosqlite
import json
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from .store import AgentMemoryStore, InteractionRecord

class SQLiteMemoryStore(AgentMemoryStore):
    """SQLite implementation of agent memory store."""
    
    def __init__(self, db_path: str = "data/kyros.db"):
        self.db_path = db_path
        self._initialized = False
    
    async def _init(self):
        """Initialize the database and create tables if they don't exist."""
        if self._initialized:
            return
            
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_interactions(
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    context TEXT NOT NULL,
                    result TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON agent_interactions(agent_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_task_id ON agent_interactions(task_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON agent_interactions(timestamp)")
            
            await db.commit()
        self._initialized = True
    
    async def store_interaction(self, agent_id: str, task_id: str, context: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Store an agent interaction and return interaction ID."""
        await self._init()
        interaction_id = str(uuid.uuid4())
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO agent_interactions(id, agent_id, task_id, context, result) VALUES (?, ?, ?, ?, ?)",
                (interaction_id, agent_id, task_id, json.dumps(context), json.dumps(result))
            )
            await db.commit()
        
        return interaction_id
    
    async def get_interaction(self, interaction_id: str) -> Optional[InteractionRecord]:
        """Get a specific interaction by ID."""
        await self._init()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT agent_id, task_id, context, result, timestamp FROM agent_interactions WHERE id = ?",
                (interaction_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                
                agent_id, task_id, context_json, result_json, timestamp = row
                return InteractionRecord(
                    interaction_id=interaction_id,
                    agent_id=agent_id,
                    task_id=task_id,
                    context=json.loads(context_json),
                    result=json.loads(result_json),
                    timestamp=datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow()
                )
    
    async def history(self, task_id: str, limit: int = 100) -> List[InteractionRecord]:
        """Get interaction history for a task."""
        await self._init()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, agent_id, context, result, timestamp FROM agent_interactions WHERE task_id = ? ORDER BY timestamp DESC LIMIT ?",
                (task_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                
                interactions = []
                for row in rows:
                    interaction_id, agent_id, context_json, result_json, timestamp = row
                    interactions.append(InteractionRecord(
                        interaction_id=interaction_id,
                        agent_id=agent_id,
                        task_id=task_id,
                        context=json.loads(context_json),
                        result=json.loads(result_json),
                        timestamp=datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow()
                    ))
                
                return interactions
    
    async def search_interactions(self, agent_id: Optional[str] = None, task_id: Optional[str] = None, 
                                since: Optional[datetime] = None, limit: int = 100) -> List[InteractionRecord]:
        """Search interactions with optional filters."""
        await self._init()
        
        conditions = []
        params = []
        
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        
        if task_id:
            conditions.append("task_id = ?")
            params.append(task_id)
        
        if since:
            conditions.append("timestamp >= ?")
            params.append(since.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)
        
        query = f"""
            SELECT id, agent_id, task_id, context, result, timestamp 
            FROM agent_interactions 
            WHERE {where_clause} 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
                interactions = []
                for row in rows:
                    interaction_id, agent_id, task_id, context_json, result_json, timestamp = row
                    interactions.append(InteractionRecord(
                        interaction_id=interaction_id,
                        agent_id=agent_id,
                        task_id=task_id,
                        context=json.loads(context_json),
                        result=json.loads(result_json),
                        timestamp=datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow()
                    ))
                
                return interactions
    
    async def delete_interaction(self, interaction_id: str) -> bool:
        """Delete an interaction by ID."""
        await self._init()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM agent_interactions WHERE id = ?", (interaction_id,))
            await db.commit()
            return cursor.rowcount > 0