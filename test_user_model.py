"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# moved outside routes so we always have access to them
USER_DATA = {
    "email" : "test@test.com",
    "username" : "testuser",
    "password" : "HASHED_PASSWORD",
    "image_url": None
}

USER2_DATA = {
    "email" : "test2@test.com",
    "username" : "testuser2",
    "password" : "HASHED_PASSWORD2",
    "image_url": None
}

class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        # user setup
        u = User.signup(**USER_DATA)
        u2 = User.signup(**USER2_DATA)
        db.session.add_all([u,u2])
        db.session.commit()
        self.u = u
        self.u2 = u2

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""
        # logic moved into setUp
        # u = User(
        #     email="test@test.com",
        #     username="testuser",
        #     password="HASHED_PASSWORD"
        # )

        # db.session.add(u)
        # db.session.commit()

        # Users should have no messages & no followers
        self.assertEqual(len(self.u.messages), 0)
        self.assertEqual(len(self.u.followers), 0)
        self.assertEqual(len(self.u2.messages), 0)
        self.assertEqual(len(self.u2.followers), 0)

    def test_user_following(self):
        """Tests following functionality"""
        self.u.following.append(self.u2)
        db.session.commit()

        # u should be following u2
        self.assertTrue(self.u.is_following(self.u2))
        # u2 should not be following u
        self.assertFalse(self.u2.is_following(self.u))

        # u2 should be followed by u
        self.assertTrue(self.u2.is_followed_by(self.u))
        # u should not be followed by u2
        self.assertFalse(self.u.is_followed_by(self.u2))

    def test_valid_user_signup(self):
        """Tests signup functionality"""
        #valid signup
        test_user = User.signup(
            email="signuptest@test.com",
            username="signuptestuser",
            password="HASHED_PASSWORD",
            image_url=None)
        db.session.commit()
        self.assertIsNotNone(test_user.id)
        self.assertEqual(test_user.username, "signuptestuser")

    def test_invalid_user_signup(self):
        #invalid signup
        invalid_username = User.signup(
            username=None,
            email="test3@test.com",
            password="HASHED_PASSWORD",
            image_url=None
        )
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_duplicate_user_signup(self):
        #dupe signup
        dupe_user = User.signup(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD",
            image_url=None
        )
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_user_auth(self):
        """Tests user authentication functionality"""
        authed_user = User.authenticate(self.u.username, "HASHED_PASSWORD")
        #returns False if it fails
        self.assertTrue(authed_user)
        self.assertEqual(self.u.id, authed_user.id)
        #should fail as password should be encrypted
        failed_pass = User.authenticate(self.u.username, self.u.password)
        self.assertFalse(failed_pass)
        #failing username
        failed_user = User.authenticate("?????","password")
        self.assertFalse(failed_user)


