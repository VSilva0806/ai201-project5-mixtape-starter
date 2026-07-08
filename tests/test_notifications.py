"""
tests/test_notifications.py — Mixtape

Reproduction: notifications should fire for both playlist-adds and ratings.
"""

import pytest
from app import create_app, db
from models import User, Song, Playlist, playlist_entries
from services.notification_service import add_to_playlist, rate_song, get_notifications


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def seed_friends(app):
    """Two friends: alice shares a song, bob adds it to a playlist and rates it."""
    with app.app_context():
        alice = User(username="alice", email="alice@example.com")
        bob = User(username="bob", email="bob@example.com")
        db.session.add_all([alice, bob])
        db.session.flush()

        alice.friends.append(bob)
        bob.friends.append(alice)

        song = Song(title="Nightcall", artist="Kavinsky", shared_by=alice.id)
        db.session.add(song)
        db.session.flush()

        playlist = Playlist(name="Bob's Playlist", created_by=bob.id)
        db.session.add(playlist)
        db.session.flush()

        # Pre-seed the association row (position/added_by) to sidestep an unrelated
        # bug where add_to_playlist's plain relationship .append() omits them.
        db.session.execute(
            playlist_entries.insert().values(
                playlist_id=playlist.id,
                song_id=song.id,
                position=1,
                added_by=bob.id,
            )
        )
        db.session.commit()

        yield {"alice": alice, "bob": bob, "song": song, "playlist": playlist}


def test_notified_on_playlist_add_and_on_rating(app, seed_friends):
    """
    Alice should be notified both when bob adds her song to a playlist
    and when bob rates her song. Currently only the playlist-add notification fires.
    """
    with app.app_context():
        alice_id = seed_friends["alice"].id
        bob_id = seed_friends["bob"].id
        song_id = seed_friends["song"].id
        playlist_id = seed_friends["playlist"].id

        add_to_playlist(playlist_id=playlist_id, song_id=song_id, added_by_user_id=bob_id)
        rate_song(user_id=bob_id, song_id=song_id, score=5)

        notifications = get_notifications(alice_id)
        types = [n["type"] for n in notifications]

        assert "song_added_to_playlist" in types
        assert "song_rated" in types  # Fails: rate_song never creates a notification
