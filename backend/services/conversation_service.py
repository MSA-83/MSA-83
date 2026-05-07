"""Conversation management service."""

import uuid
from datetime import datetime


class ConversationService:
    """Manage chat conversations and message history."""

    def __init__(self):
        self._conversations: dict[str, dict] = {}
        self._messages: dict[str, list[dict]] = {}

    def create_conversation(self, user_id: str, title: str | None = None) -> dict:
        """Create a new conversation."""
        conv_id = f"conv-{uuid.uuid4().hex[:8]}"

        conversation = {
            "id": conv_id,
            "user_id": user_id,
            "title": title or "New Conversation",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "message_count": 0,
        }

        self._conversations[conv_id] = conversation
        self._messages[conv_id] = []

        return conversation

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        """Add a message to a conversation."""
        if conversation_id not in self._messages:
            raise ValueError(f"Conversation not found: {conversation_id}")

        message = {
            "id": f"msg-{uuid.uuid4().hex[:8]}",
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }

        self._messages[conversation_id].append(message)

        if conversation_id in self._conversations:
            self._conversations[conversation_id]["updated_at"] = datetime.utcnow().isoformat()
            self._conversations[conversation_id]["message_count"] = len(self._messages[conversation_id])

            if (
                len(self._messages[conversation_id]) == 2
                and self._conversations[conversation_id]["title"] == "New Conversation"
            ):
                self._conversations[conversation_id]["title"] = content[:50] + ("..." if len(content) > 50 else "")

        return message

    def get_conversation(self, conversation_id: str) -> dict | None:
        """Get a conversation by ID."""
        return self._conversations.get(conversation_id)

    def get_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Get messages for a conversation."""
        messages = self._messages.get(conversation_id, [])
        return messages[offset : offset + limit]

    def get_conversations(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """Get all conversations for a user."""
        user_convs = [c for c in self._conversations.values() if c["user_id"] == user_id]

        user_convs.sort(key=lambda c: c["updated_at"], reverse=True)

        return user_convs[offset : offset + limit]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and its messages."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            self._messages.pop(conversation_id, None)
            return True
        return False

    def update_title(self, conversation_id: str, title: str) -> dict | None:
        """Update conversation title."""
        if conversation_id in self._conversations:
            self._conversations[conversation_id]["title"] = title
            return self._conversations[conversation_id]
        return None

    def search_conversations(
        self,
        user_id: str,
        query: str,
    ) -> list[dict]:
        """Search conversations by title or message content."""
        query_lower = query.lower()
        results = []

        for conv_id, conv in self._conversations.items():
            if conv["user_id"] != user_id:
                continue

            if query_lower in conv["title"].lower():
                results.append(conv)
                continue

            messages = self._messages.get(conv_id, [])
            for msg in messages:
                if query_lower in msg["content"].lower():
                    results.append(conv)
                    break

        return results

    def get_stats(self, user_id: str) -> dict:
        """Get conversation statistics for a user."""
        user_convs = [c for c in self._conversations.values() if c["user_id"] == user_id]

        total_messages = sum(len(self._messages.get(c["id"], [])) for c in user_convs)

        return {
            "total_conversations": len(user_convs),
            "total_messages": total_messages,
            "active_conversations": sum(1 for c in user_convs if c["message_count"] > 0),
        }


conversation_service = ConversationService()
