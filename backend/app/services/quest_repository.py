from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import uuid

try:
    from pymongo import ReturnDocument
except ImportError:
    ReturnDocument = None

from backend.app.database.mongodb import get_database

# In-memory storage fallback if MongoDB Atlas is not reachable or configured
_memory_db: Dict[str, Dict[str, Any]] = {}


class QuestRepository:
    def __init__(self):
        self.db = get_database()

    async def save_quest(
        self,
        user_preferences: dict,
        selected_location: dict,
        quest_data: dict,
    ) -> str:
        """Saves a new quest document into MongoDB (or in-memory fallback) and returns quest_id."""
        quest_id = str(uuid.uuid4())
        record = {
            "_id": quest_id,
            "quest_id": quest_id,
            "user_preferences": user_preferences,
            "selected_location": selected_location,
            "quest": {
                "title": quest_data.get("title"),
                "location": quest_data.get("location", selected_location.get("name") if isinstance(selected_location, dict) else selected_location),
                "address": quest_data.get("address", selected_location.get("address") if isinstance(selected_location, dict) else None),
                "estimated_duration": quest_data.get("estimated_duration"),
                "difficulty": quest_data.get("difficulty"),
                "description": quest_data.get("description"),
                "objectives": quest_data.get("objectives", []),
                "safety_note": quest_data.get("safety_note"),
            },
            "completion_status": "not_completed",
            "reflection": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }

        if self.db is not None:
            try:
                await self.db.quests.insert_one(record)
                return quest_id
            except Exception:
                pass  # Fallback to in-memory store on DB write errors

        _memory_db[quest_id] = record
        return quest_id

    async def get_quest_by_id(self, quest_id: str) -> Optional[dict]:
        """Retrieves a quest document by ID."""
        if self.db is not None:
            try:
                result = await self.db.quests.find_one({"_id": quest_id})
                if result:
                    result["id"] = result["_id"]
                    result["quest_id"] = result["_id"]
                    return result
            except Exception:
                pass

        if quest_id in _memory_db:
            res = _memory_db[quest_id].copy()
            res["id"] = res["_id"]
            res["quest_id"] = res["_id"]
            return res

        return None

    async def update_completion(
        self, quest_id: str, status: str, reflection: Optional[str] = None
    ) -> Optional[dict]:
        """Updates the completion status and reflection of a quest."""
        completed_at = datetime.now(timezone.utc).isoformat()
        update_data = {
            "completion_status": status,
            "reflection": reflection,
            "completed_at": completed_at,
        }

        if self.db is not None:
            try:
                opts = {"return_document": ReturnDocument.AFTER} if ReturnDocument else {}
                result = await self.db.quests.find_one_and_update(
                    {"_id": quest_id},
                    {"$set": update_data},
                    **opts,
                )
                if result:
                    result["id"] = result["_id"]
                    result["quest_id"] = result["_id"]
                    return result
            except Exception:
                pass

        if quest_id in _memory_db:
            _memory_db[quest_id].update(update_data)
            res = _memory_db[quest_id].copy()
            res["id"] = res["_id"]
            res["quest_id"] = res["_id"]
            return res

        return None

    async def get_recent_quests(self, limit: int = 10) -> List[dict]:
        """Retrieves a list of recent quests."""
        if self.db is not None:
            try:
                cursor = self.db.quests.find().sort("created_at", -1).limit(limit)
                quests = await cursor.to_list(length=limit)
                for q in quests:
                    q["id"] = q["_id"]
                    q["quest_id"] = q["_id"]
                return quests
            except Exception:
                pass

        quests = list(_memory_db.values())
        quests.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        for q in quests[:limit]:
            q["id"] = q["_id"]
            q["quest_id"] = q["_id"]
        return quests[:limit]


quest_repo = QuestRepository()
