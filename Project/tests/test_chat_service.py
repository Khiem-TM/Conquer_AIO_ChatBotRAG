from __future__ import annotations

import unittest

from app.rag_core.chat_service import ChatService


class ChatServiceTestCase(unittest.TestCase):
    def test_detect_system_metadata(self) -> None:
        service = ChatService()
        mode, confidence = service._detect_mode('Cho tôi biết metadata hệ thống và model hiện tại')
        self.assertEqual(mode, 'system_metadata')
        self.assertGreaterEqual(confidence, 0.5)

    def test_detect_reasoning(self) -> None:
        service = ChatService()
        mode, _ = service._detect_mode('Hãy phân tích nguyên nhân và kết luận từ tài liệu')
        self.assertEqual(mode, 'reasoning_over_docs')


if __name__ == '__main__':
    unittest.main()
