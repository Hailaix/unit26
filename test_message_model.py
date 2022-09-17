"""Message model tests."""

import os
from unittest import TestCase

from models import db, User, Message

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    
    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    def test_message_model(self):
        """Tests message creation"""
        msg = Message(
            text="Test Message",
            user_id=self.testuser.id
        )
        db.session.add(msg)
        db.session.commit()

        # message should be in testuser's messages relationship
        self.assertEqual(self.testuser.messages[0],msg)