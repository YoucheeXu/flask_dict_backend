"""Utility file to send messages to users via SocketIOService."""
import time
from src.services.socket_service import UserId, RoomId, MessagePayload
from src.services.socket_service import socket_service   # Import the singleton SocketIOService


def notify_user(
    user_id: UserId,
    message: str,
    message_type: str = "notification"
) -> bool:
    """ notification."""
    payload: MessagePayload = {
        'msg': message,
        'time': time.strftime('%H:%M:%S'),
        'user_id': user_id,
        'type': message_type
    }

    socket_service.push_to_user(user_id=user_id, message=payload)
    print(f"✅ notification sent to {user_id}: {message}")
    return True

def send_notification_to_user(
    user_id: UserId,
    message_text: str,
    message_type: str = "notification"
):
    """ Send real-time message to a user.

    Args:
        user_id: Target user ID (matches auth ID in SocketIOService._user_to_sids)
        message_text: Human-readable message content
        message_type: Custom type for frontend handling (e.g., "progress", "reminder")

    Returns:
        bool: True if message was queued (user has active sessions), False otherwise
    """
    # --------------------------
    # Build payload matching SocketIOService's expected format
    # --------------------------
    payload: MessagePayload = {
        'msg': message_text,
        'time': time.strftime('%H:%M:%S'),
        'user_id': user_id,
        'type': message_type  # Matches frontend handling
    }

    # --------------------------
    # Call the EXACT method from the full SocketIOService
    # --------------------------
    socket_service.push_to_user(user_id=user_id, message=payload)
    print(f"✅ Notification sent to user {user_id} (type: {message_type}): {message_text}")


# --------------------------
# Background Task Helpers (Public)
# --------------------------
def start_periodic_user_push(target_user: UserId = 'user_123', interval: int = 8) -> None:
    """ Start a background task to push periodic messages to a specific user.

    Args:
        target_user: User ID to target (default: 'user_123')
        interval: Push interval in seconds (default: 8)
    """
    def _periodic_push() -> None:
        while True:
            time.sleep(interval)
            message: MessagePayload = {
                'msg': f"[Exclusive Push] Scheduled update for {target_user}",
                'time': time.strftime('%H:%M:%S'),
                'user_id': target_user,
                'type': 'user'
            }
            socket_service.push_to_user(target_user, message)

    # Start task in SocketIO-managed background thread
    _ = socket_service.socketio.start_background_task(_periodic_push)
    print(f"🔄 Started periodic user push for {target_user} (interval: {interval}s)")

def start_periodic_room_push(target_room: RoomId = 'room_100', interval: int = 10) -> None:
    """ Start a background task to push periodic messages to a specific room.

    Args:
        target_room: Room ID to target (default: 'room_100')
        interval: Push interval in seconds (default: 10)
    """
    def _periodic_push() -> None:
        while True:
            time.sleep(interval)
            message: MessagePayload  = {
                'msg': f"[Room Push] Scheduled update for room {target_room}",
                'time': time.strftime('%H:%M:%S'),
                'room_id': target_room,
                'type': 'room'
            }
            socket_service.push_to_room(target_room, message)

    # Start task in SocketIO-managed background thread
    _ = socket_service.socketio.start_background_task(_periodic_push)
    print(f"🔄 Started periodic room push for {target_room} (interval: {interval}s)")
