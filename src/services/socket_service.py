#!/usr/bin/python3
# -*- coding: utf-8 -*-
""" Reusable SocketIO Service for Flask Backend.

This module implements a modular SocketIOService class that encapsulates all
WebSocket communication logic (user authentication, room management, targeted
message pushing) for a Flask application. Designed for reusability and
separation of concerns.

Compatible with Python 3.13+, Flask-SocketIO 5.3.6, and Vue3+TypeScript frontend.
"""

from __future__ import annotations

import threading

from flask import request
from flask_socketio import SocketIO, emit

# --------------------------
# Type Aliases (Improve Readability)
# --------------------------
UserId = str
SessionId = str
RoomId = str
MessagePayload = dict[str, object]

# --------------------------
# SocketIO Service Class
# --------------------------
class SocketIOService:
    """ Core SocketIO service for real-time communication.

    Encapsulates all WebSocket logic including:
    - User-session-room state management (thread-safe)
    - Authentication handling
    - Room join/leave operations
    - Targeted/user/room message pushing
    - Background periodic push tasks
    """

    def __init__(self, socketio: SocketIO) -> None:
        """ Initialize SocketIO service with a Flask-SocketIO instance.

        Args:
            socketio: Pre-configured Flask-SocketIO instance (from Flask app)
        """
        # Dependency injection (SocketIO instance)
        self.socketio: SocketIO = socketio

        # Thread-safe state storage (protected by lock)
        self._user_to_sids: dict[UserId, set[SessionId]] = {}
        self._sid_to_user: dict[SessionId, UserId] = {}
        self._room_to_users: dict[RoomId, set[UserId]] = {}
        self._sid_to_rooms: dict[SessionId, set[RoomId]] = {}

        # Thread safety lock (prevents race conditions)
        self._data_lock: threading.Lock = threading.Lock()

        # Register SocketIO event handlers
        self._register_event_handlers()

    # --------------------------
    # Event Handler Registration (Private)
    # --------------------------
    def _register_event_handlers(self) -> None:
        """ Register all SocketIO event handlers with the Flask-SocketIO instance."""
        # Core connection handlers
        _ = self.socketio.on('connect')(self.handle_connect)
        _ = self.socketio.on('disconnect')(self.handle_disconnect)

        # Authentication handlers
        _ = self.socketio.on('user_auth')(self.handle_user_auth)

        # Room management handlers
        _ = self.socketio.on('join_room')(self.handle_join_room)
        _ = self.socketio.on('leave_room')(self.handle_leave_room)

    # --------------------------
    # Core Connection Handlers (Public API)
    # --------------------------
    def handle_connect(self) -> None:
        """ Handle new client connection.

        Emits connection acknowledgment with session ID (sid) and logs the event.
        """
        sid: SessionId = request.sid
        print(f"📌 New client connection - Session ID: {sid}")
        emit(
            'connect_ack',
            {'msg': 'Successfully connected to Flask WebSocket server', 'sid': sid}
        )

    def handle_disconnect(self) -> None:
        """ Clean up state for disconnected clients.

        Removes the client from all state mappings (user-session, session-room,
        room-user) in a thread-safe manner. Cleans up empty entries to prevent
        memory leaks.
        """
        sid: SessionId = request.sid

        with self._data_lock:
            # Step 1: Clean up user-session mapping
            user_id: UserId | None = self._sid_to_user.get(sid)

            if user_id:
                # Remove session from user's active sessions
                if user_id in self._user_to_sids:
                    self._user_to_sids[user_id].discard(sid)
                    # Delete empty user entry
                    if not self._user_to_sids[user_id]:
                        del self._user_to_sids[user_id]

                # Remove reverse mapping
                del self._sid_to_user[sid]

            # Step 2: Clean up session-room mapping
            if sid in self._sid_to_rooms:
                user_rooms = self._sid_to_rooms[sid].copy()

                # Remove user from all rooms
                for room_id in user_rooms:
                    if room_id in self._room_to_users and user_id in self._room_to_users[room_id]:
                        self._room_to_users[room_id].discard(user_id)
                        # Delete empty room entry
                        if not self._room_to_users[room_id]:
                            del self._room_to_users[room_id]

                    # Remove room from session's room list
                    self._sid_to_rooms[sid].discard(room_id)

                # Delete empty session-room entry
                del self._sid_to_rooms[sid]

        # Log disconnection
        if user_id:
            print(f"❌ User disconnected - User ID: {user_id}, Session ID: {sid}")
        else:
            print(f"❌ Unauthenticated client disconnected - Session ID: {sid}")

    # --------------------------
    # Authentication Handlers (Public API)
    # --------------------------
    def handle_user_auth(self, data: dict[str, object]) -> None:
        """ Authenticate client and bind to a user ID.

        Validates the authentication request and updates state mappings in a
        thread-safe manner. Emits success/error responses to the client.

        Args:
            data: Payload containing 'user_id' (required)
        """
        sid: SessionId = request.sid
        user_id: UserId | None = data.get('user_id')

        # Validate required parameter
        if not user_id:
            emit('auth_error', {'msg': 'Authentication failed: Missing required "user_id" field'})
            return

        # Update state with thread safety
        with self._data_lock:
            # Initialize user-session mapping
            if user_id not in self._user_to_sids:
                self._user_to_sids[user_id] = set()
            self._user_to_sids[user_id].add(sid)
            self._sid_to_user[sid] = user_id

            # Initialize session-room mapping
            if sid not in self._sid_to_rooms:
                self._sid_to_rooms[sid] = set()

        # Emit success and log
        print(f"✅ User authenticated - User ID: {user_id}, Session ID: {sid}")
        emit('auth_success', {'msg': f'User {user_id} authenticated successfully'})

    # --------------------------
    # Room Management Handlers (Public API)
    # --------------------------
    def handle_join_room(self, data: dict[str, object]) -> None:
        """ Add a user to a room (group).

        Validates the request and updates room mappings in a thread-safe manner.
        Emits success/error responses and notifies room members of the join.

        Args:
            data: Payload containing 'room_id' (required)
        """
        sid: SessionId = request.sid

        # Validate authentication
        if sid not in self._sid_to_user:
            emit('room_error', {'msg': 'Cannot join room: User not authenticated'})
            return

        # Validate room ID
        room_id: RoomId | None = data.get('room_id')
        if not room_id:
            emit('room_error', {'msg': 'Cannot join room: Missing required "room_id" field'})
            return

        user_id: UserId = self._sid_to_user[sid]

        # Update room mappings with thread safety
        with self._data_lock:
            # Add user to room
            if room_id not in self._room_to_users:
                self._room_to_users[room_id] = set()
            self._room_to_users[room_id].add(user_id)

            # Add room to session's room list
            self._sid_to_rooms[sid].add(room_id)

        # Emit success and notify room members
        emit('room_success', {'msg': f'Successfully joined room: {room_id}'})
        self.socketio.emit(
            'room_notification',
            {'msg': f'User {user_id} joined room {room_id}', 'room_id': room_id},
            to=sid,
            skip_sid=sid
        )

        print(f"🏠 User joined room - User ID: {user_id}, Room ID: {room_id}, Session ID: {sid}")

    def handle_leave_room(self, data: dict[str, object]) -> None:
        """ Remove a user from a room (group).

        Validates the request and updates room mappings in a thread-safe manner.
        Emits success/error responses and notifies room members of the leave.

        Args:
            data: Payload containing 'room_id' (required)
        """
        sid: SessionId = request.sid

        # Validate authentication
        if sid not in self._sid_to_user:
            emit('room_error', {'msg': 'Cannot leave room: User not authenticated'})
            return

        # Validate room ID
        room_id: RoomId | None = data.get('room_id')
        if not room_id:
            emit('room_error', {'msg': 'Cannot leave room: Missing required "room_id" field'})
            return

        user_id: UserId = self._sid_to_user[sid]

        # Update room mappings with thread safety
        with self._data_lock:
            # Remove user from room
            if room_id in self._room_to_users and user_id in self._room_to_users[room_id]:
                self._room_to_users[room_id].discard(user_id)
                # Clean up empty room
                if not self._room_to_users[room_id]:
                    del self._room_to_users[room_id]

            # Remove room from session's room list
            if sid in self._sid_to_rooms and room_id in self._sid_to_rooms[sid]:
                self._sid_to_rooms[sid].discard(room_id)

        # Emit success and notify room members
        emit('room_success', {'msg': f'Successfully left room: {room_id}'})
        self.socketio.emit(
            'room_notification',
            {'msg': f'User {user_id} left room {room_id}', 'room_id': room_id},
            to=sid,
            skip_sid=sid
        )

        print(f"🏠 User left room - User ID: {user_id}, Room ID: {room_id}, Session ID: {sid}")

    # --------------------------
    # Message Pushing API (Public)
    # --------------------------
    def push_to_user(self, user_id: UserId, message: MessagePayload) -> None:
        """ Push a targeted message to all active sessions of a specific user.

        Args:
            user_id: Target user ID
            message: Message payload (must include 'msg', 'time', 'user_id', 'type')
        """
        with self._data_lock:
            # Get copy of user's active sessions
            user_sessions = list(self._user_to_sids.get(user_id, set()).copy())

        if not user_sessions:
            print(f"⏳ No active clients for user {user_id} - skipping push")
            return

        # Send message to each session
        for sid in user_sessions:
            self.socketio.emit('private_message', message, to=sid)

        print(f"📤 Pushed to {len(user_sessions)} clients for user {user_id}")

    def push_to_room(self, room_id: RoomId, message: MessagePayload) -> None:
        """ Push a group message to all active users in a room.

        Args:
            room_id: Target room ID
            message: Message payload (must include 'msg', 'time', 'room_id', 'type')
        """
        with self._data_lock:
            # Get room members and their sessions
            room_users = self._room_to_users.get(room_id, set()).copy()
            room_sessions: set[SessionId] = set()

            for user_id in room_users:
                room_sessions.update(self._user_to_sids.get(user_id, set()))

        if not room_sessions:
            print(f"⏳ No active members in room {room_id} - skipping push")
            return

        # Send message to all room sessions
        for sid in room_sessions:
            self.socketio.emit('room_message', message, to=sid)

        print(f"📤 Pushed to {len(room_sessions)} clients in room {room_id}")


socketio = SocketIO(
    cors_allowed_origins="*",
    cors_credentials=False,
    async_mode='threading',
    ping_timeout=10,
    ping_interval=5
)

# --------------------------
# Create singleton instance of the FULL SocketIOService
# --------------------------
socket_service = SocketIOService(socketio)

# Export for cross-file access
__all__ = ["socketio", "socket_service"]
