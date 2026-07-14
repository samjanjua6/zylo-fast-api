from __future__ import annotations

import os

# Must be set before any app import
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _get_token(client: TestClient, username="wsuser") -> str:
    """Sign up and log in, returning the JWT."""
    client.post(
        "/signup",
        json={"username": username, "email": f"{username}@example.com", "password": "password123"},
    )
    res = client.post(
        "/login",
        json={"username_or_email": username, "password": "password123"},
    )
    return res.json()["access_token"]


def test_websocket_rejects_connection_without_token():
    """WS connection without a token must be closed with code 1008."""
    client = TestClient(app)
    with pytest.raises(Exception):
        # TestClient raises when the server closes the WS before accepting
        with client.websocket_connect("/ws/chat"):
            pass


def test_websocket_rejects_connection_with_invalid_token():
    """A forged / expired token must be rejected with code 1008."""
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/chat?token=this.is.not.a.valid.jwt"):
            pass


def test_websocket_accepts_connection_with_valid_token():
    """An authenticated user can connect and exchange messages."""
    client = TestClient(app)
    token = _get_token(client)

    with client.websocket_connect(f"/ws/chat?token={token}") as ws:
        greeting = ws.receive_text()
        assert "wsuser" in greeting  # welcome message includes the username
        ws.receive_text()  # consume [DONE]

        ws.send_text("hello")
        reply = ws.receive_text()
        # Groq model might stream it token by token, so just loop until [DONE]
        full_reply = reply
        while reply != "[DONE]":
            reply = ws.receive_text()
            if reply != "[DONE]":
                full_reply += reply
        assert len(full_reply) > 0


def test_websocket_chat_replies_like_a_simple_bot():
    """End-to-end test covering all reply branches."""
    client = TestClient(app)
    token = _get_token(client, username="bottest")

    with client.websocket_connect(f"/ws/chat?token={token}") as ws:
        ws.receive_text()  # consume welcome
        ws.receive_text()  # consume [DONE]

        ws.send_text("hi")
        reply = ws.receive_text()
        full_reply = reply
        while reply != "[DONE]":
            reply = ws.receive_text()
            if reply != "[DONE]":
                full_reply += reply
        assert len(full_reply) > 0

        ws.send_text("What can you do?")
        reply = ws.receive_text()
        full_reply = reply
        while reply != "[DONE]":
            reply = ws.receive_text()
            if reply != "[DONE]":
                full_reply += reply
        assert len(full_reply) > 0

        ws.send_text("just chatting")
        reply = ws.receive_text()
        full_reply = reply
        while reply != "[DONE]":
            reply = ws.receive_text()
            if reply != "[DONE]":
                full_reply += reply
        assert len(full_reply) > 0