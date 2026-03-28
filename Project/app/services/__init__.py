"""Service layer for chat operations."""

import json
import uuid
from datetime import datetime
from pathlib import Path

from app.models.chat import ChatMessage


class ChatHistoryService:
    """Service to manage chat history."""

    def __init__(self, history_file: str = "data/chat_history.json"):
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_history()

    def _load_history(self) -> None:
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    self.messages: list[dict] = data.get("messages", [])
            except (json.JSONDecodeError, IOError):
                self.messages = []
        else:
            self.messages = []

    def _save_history(self) -> None:
        """Save history to file."""
        with open(self.history_file, "w") as f:
            json.dump({"messages": self.messages}, f, indent=2, default=str)

    def add_message(
        self, question: str, answer: str, sources: list[dict] | None = None
    ) -> ChatMessage:
        """Add a new message to history."""
        msg_id = str(uuid.uuid4())
        timestamp = datetime.now()

        message = {
            "id": msg_id,
            "question": question,
            "answer": answer,
            "timestamp": timestamp.isoformat(),
            "sources": sources or [],
        }

        self.messages.insert(0, message)  # Insert at beginning (latest first)
        self._save_history()

        return ChatMessage(**message, timestamp=timestamp)

    def get_all_messages(self) -> list[ChatMessage]:
        """Get all messages (latest first)."""
        messages = []
        for msg in self.messages:
            # Convert ISO string back to datetime
            timestamp = datetime.fromisoformat(msg["timestamp"])
            messages.append(
                ChatMessage(
                    id=msg["id"],
                    question=msg["question"],
                    answer=msg["answer"],
                    timestamp=timestamp,
                    sources=msg.get("sources", []),
                )
            )
        return messages

    def clear_all(self) -> None:
        """Clear all chat history."""
        self.messages = []
        self._save_history()

    def get_message_count(self) -> int:
        """Get total number of messages."""
        return len(self.messages)
