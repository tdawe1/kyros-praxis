import aiosqlite, json, os
from typing import List, Dict, Any
from .store import AgentMemoryStore
class SQLiteMemory(AgentMemoryStore):
    def __init__(self, db_path="data/kyros.db"): self.db_path=db_path
    async def _init(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS agent_history(
              id INTEGER PRIMARY KEY, agent_id TEXT, task_id TEXT, context TEXT, result TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            await db.commit()
    async def store_interaction(self, agent_id, task_id, context, result):
        await self._init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO agent_history(agent_id,task_id,context,result) VALUES (?,?,?,?)",
                             (agent_id, task_id, json.dumps(context), json.dumps(result)))
            await db.commit()
    async def history(self, task_id, limit=100) -> List[Dict[str,Any]]:
        await self._init()
        async with aiosqlite.connect(self.db_path) as db:
            rows = await db.execute_fetchall("SELECT context,result,ts FROM agent_history WHERE task_id=? ORDER BY id DESC LIMIT ?", (task_id,limit))
            return [ {"context":json.loads(c), "result":json.loads(r), "ts":ts} for (c,r,ts) in rows ]