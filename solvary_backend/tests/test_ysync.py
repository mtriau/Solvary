"""Unit tests for the lib0/y-protocol codec."""

from app.services.collaboration import sync


def test_var_uint_roundtrip():
    for n in [0, 1, 127, 128, 300, 16_383, 16_384, 2**31, 2**53]:
        buf = sync.write_var_uint(n)
        decoded, pos = sync.read_var_uint(buf, 0)
        assert decoded == n
        assert pos == len(buf)


def test_var_uint8array_roundtrip():
    payload = bytes(range(200))
    buf = sync.write_var_uint8array(payload)
    decoded, pos = sync.read_var_uint8array(buf, 0)
    assert decoded == payload
    assert pos == len(buf)


def test_sync_message_roundtrip():
    update = b"\x01\x02\x03yjs-update-bytes"
    for encoder, subtype in [
        (sync.encode_sync_step1, sync.SYNC_STEP1),
        (sync.encode_sync_step2, sync.SYNC_STEP2),
        (sync.encode_sync_update, sync.SYNC_UPDATE),
    ]:
        msg_type, sub, payload = sync.parse_message(encoder(update))
        assert msg_type == sync.MESSAGE_SYNC
        assert sub == subtype
        assert payload == update


def test_awareness_roundtrip():
    payload = b"awareness-payload"
    msg_type, sub, decoded = sync.parse_message(sync.encode_awareness(payload))
    assert msg_type == sync.MESSAGE_AWARENESS
    assert sub is None
    assert decoded == payload


def test_files_changed_tag():
    msg_type, _, _ = sync.parse_message(sync.encode_files_changed())
    assert msg_type == sync.MESSAGE_FILES_CHANGED
    # Must stay outside y-websocket's tag space (0=sync 1=awareness 2=auth 3=queryAwareness)
    assert sync.MESSAGE_FILES_CHANGED > 3


def test_awareness_removal_parses_back():
    frame = sync.encode_awareness_removal(client_id=12345678, clock=42)
    msg_type, _, payload = sync.parse_message(frame)
    assert msg_type == sync.MESSAGE_AWARENESS
    client_id, clock = sync.parse_awareness_client(payload)
    assert client_id == 12345678
    assert clock == 42
