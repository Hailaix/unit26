"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users"""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser.bio = "Test user bio"
        self.usertwo = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)
        self.usertwo.bio = "User Two bio"
        self.testuser.following.append(self.usertwo)
        self.usertwo.following.append(self.testuser)
        db.session.commit()
        # for some reason, the id needs to be taken here for the user to remain bound to a session
        # and not throw an exception when they're referenced later
        self.u2id = self.usertwo.id

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    def test_user_page(self):
        """Test user detail Pages"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # Test a user's own details page
            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.testuser.bio, html)
            
            # Test viewing other user's details page
            resp = c.get(f"/users/{self.usertwo.id}")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.usertwo.bio, html)
    
    def test_following(self):
        """Test user following page"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # Test a user's own following page
            resp = c.get(f"/users/{self.testuser.id}/following")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.usertwo.bio, html)

            # Test viewing another's following page
            resp = c.get(f"/users/{self.usertwo.id}/following")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.testuser.bio, html)

    def test_no_auth_following(self):
        """Test user following page, no auth"""
        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_followers(self):
        """Test user followers page"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # Test a user's own following page
            resp = c.get(f"/users/{self.testuser.id}/followers")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.usertwo.bio, html)

            # Test viewing another's following page
            resp = c.get(f"/users/{self.usertwo.id}/followers")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.testuser.bio, html)
    
    def test_no_auth_followers(self):
        """Test user followers page, no auth"""
        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_stop_following(self):
        """Test user ability to stop following"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post(f"/users/stop-following/{self.usertwo.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(self.usertwo.bio, html)
    
    def test_no_auth_stop_following(self):
        """Test user ability to stop following, no auth"""
        with self.client as c:
            resp = c.post(f"/users/stop-following/{self.usertwo.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_follow(self):
        """Test user ability to follow another user"""
        new_user = User.signup(username="testuser3",
                                    email="test3@test.com",
                                    password="testuser3",
                                    image_url=None)
        new_user.bio = "The new user bio"
        db.session.commit()
        # same thing with DetachedInstanceError if we don't capture the id here for some reason
        nid = new_user.id
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post(f"/users/follow/{new_user.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(new_user.bio, html)
    
    def test_no_auth_follow(self):
        """Test non user ability to follow a user, no auth"""
        with self.client as c:
            resp = c.post(f"/users/follow/{self.usertwo.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)
