"""
y-protocol wire codec (lib0 encoding) — the exact framing the stock
`y-websocket` client provider speaks, so it works unmodified (design §7.2).

Message layout: varUint messageType, then payload.
  0 = sync      → varUint subtype: 0 step1 (state vector), 1 step2 (update),
                  2 update
  1 = awareness → varUint8Array awareness-update payload
  127 = file-listing-changed (Solvary extension, empty payload).
        The design's original 0x03 tag collides with y-websocket's
        queryAwareness (=3); 127 is outside the protocol's tag space.
"""

MESSAGE_SYNC = 0
MESSAGE_AWARENESS = 1
MESSAGE_FILES_CHANGED = 127

SYNC_STEP1 = 0
SYNC_STEP2 = 1
SYNC_UPDATE = 2


# ── lib0 primitives ────────────────────────────────────────────────


def write_var_uint(n: int) -> bytes:
    out = bytearray()
    while n > 127:
        out.append(128 | (n & 127))
        n >>= 7
    out.append(n)
    return bytes(out)


def read_var_uint(buf: bytes, pos: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while True:
        byte = buf[pos]
        pos += 1
        n |= (byte & 127) << shift
        if byte < 128:
            return n, pos
        shift += 7


def write_var_uint8array(data: bytes) -> bytes:
    return write_var_uint(len(data)) + data


def read_var_uint8array(buf: bytes, pos: int) -> tuple[bytes, int]:
    length, pos = read_var_uint(buf, pos)
    return buf[pos : pos + length], pos + length


def write_var_string(s: str) -> bytes:
    return write_var_uint8array(s.encode())


# ── message encoders ───────────────────────────────────────────────


def encode_sync_step1(state_vector: bytes) -> bytes:
    return (
        write_var_uint(MESSAGE_SYNC)
        + write_var_uint(SYNC_STEP1)
        + write_var_uint8array(state_vector)
    )


def encode_sync_step2(update: bytes) -> bytes:
    return (
        write_var_uint(MESSAGE_SYNC)
        + write_var_uint(SYNC_STEP2)
        + write_var_uint8array(update)
    )


def encode_sync_update(update: bytes) -> bytes:
    return (
        write_var_uint(MESSAGE_SYNC)
        + write_var_uint(SYNC_UPDATE)
        + write_var_uint8array(update)
    )


def encode_awareness(payload: bytes) -> bytes:
    return write_var_uint(MESSAGE_AWARENESS) + write_var_uint8array(payload)


def encode_files_changed() -> bytes:
    return write_var_uint(MESSAGE_FILES_CHANGED)


def encode_awareness_removal(client_id: int, clock: int) -> bytes:
    """Awareness update marking a client as offline (state = null) —
    sent by the server when a connection drops, so peers' cursors
    disappear immediately instead of after the 30s awareness timeout."""
    payload = (
        write_var_uint(1)  # one client entry
        + write_var_uint(client_id)
        + write_var_uint(clock)
        + write_var_string("null")
    )
    return encode_awareness(payload)


# ── message parsing ────────────────────────────────────────────────


def parse_message(data: bytes) -> tuple[int, int | None, bytes]:
    """Returns (message_type, sync_subtype | None, payload)."""
    msg_type, pos = read_var_uint(data, 0)
    if msg_type == MESSAGE_SYNC:
        subtype, pos = read_var_uint(data, pos)
        payload, _ = read_var_uint8array(data, pos)
        return msg_type, subtype, payload
    if msg_type == MESSAGE_AWARENESS:
        payload, _ = read_var_uint8array(data, pos)
        return msg_type, None, payload
    return msg_type, None, data[pos:]


def parse_awareness_client(payload: bytes) -> tuple[int, int]:
    """(client_id, clock) of the first entry in an awareness update."""
    _count, pos = read_var_uint(payload, 0)
    client_id, pos = read_var_uint(payload, pos)
    clock, _pos = read_var_uint(payload, pos)
    return client_id, clock
