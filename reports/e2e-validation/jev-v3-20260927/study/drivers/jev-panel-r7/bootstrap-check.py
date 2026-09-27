import socket
from unittest.mock import patch
import track_common as tc
with patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
    tc.pin_runtime_settings()
    tc.pin_runtime_settings()
    adapter = tc.astra_adapter()
    assert (adapter.provider, adapter.source) == ("openai", "subscription")
print("bootstrap idempotent; exact subscription adapter resolved; no network")
