# In-Memory Database: Part 4

The same `MemoryDB` class grows once more: it can now snapshot itself and go
back to a snapshot. This is the state-rewriting level. The tricky part is
time to live: a snapshot must remember how much life each field had left,
not when it would have died. The earlier tests still run.

### What to implement

- `backup(timestamp) -> int`: save a snapshot of the database as of
  `timestamp`, and return the number of records that have at least one field
  alive at `timestamp`.
- `restore(timestamp, timestamp_to_restore) -> None`: replace the entire
  current contents of the database with the latest backup taken at or before
  `timestamp_to_restore`.

`timestamp` values are strictly increasing across all calls, and
`timestamp_to_restore <= timestamp`.

### Rules

- A backup contains only fields alive at the backup time. Expired fields,
  deleted fields and records with no live field are not part of it, and
  are not counted.
- Restoring replaces everything: fields and records created after the
  backup disappear, and fields changed or deleted since come back.
- **TTL is recomputed at restore.** A field with `r` time units left at
  backup time (`expires_at - backup_timestamp`) expires at `timestamp + r`
  after `restore(timestamp, ...)`. A field with a TTL of 10 set at 10, backed
  up at 13 (7 left) and restored at 50 is alive at 56 and gone at 57.
  Fields without a TTL stay permanent.
- If no backup exists at or before `timestamp_to_restore`, `restore` does
  nothing.
- A backup taken exactly at `timestamp_to_restore` counts.
- Restoring does not delete any backup. Backups taken before or after a
  restore stay available to later restores. Backups taken after a restore
  capture the restored state.
- Restoring counts as a timestamped call: the methods without a timestamp
  see the restored state, with "now" being the restore `timestamp`.

### Worked example

```python
db = MemoryDB()
db.set_at_with_ttl("k", "f", "v", 10, 10)   # alive 10..19
db.set_at("k", "g", "w", 11)
db.backup(13)                                # -> 1  (one record); f has 7 left
db.delete_at("k", "g", 14)                   # -> True
db.restore(50, 13)                           # f expires at 57, g is back
db.get_at("k", "f", 56)                      # -> "v"
db.get_at("k", "f", 57)                      # -> None
db.get_at("k", "g", 58)                      # -> "w"
db.restore(60, 5)                            # no backup at or before 5: no-op
```

### Clarifications

- **Do I store the expiry time or the remaining time?** Remaining time in
  the snapshot; the new expiry time is computed at restore.
- **Does `backup` count fields or records?** Records with at least one live
  field.
- **What does a restore to a time before every backup do?** Nothing.
- **Between two backups, which is used?** The one with the greatest backup
  timestamp that is `<= timestamp_to_restore`.
- **Can I restore the same backup twice?** Yes. Backups are never consumed.
- **Do restores affect the return of an earlier `backup`?** No.

Run the provided tests with **Submit**. The tests of Parts 1 to 3 run too.

---
Interviewer notes

The core check is that remaining lifetime (not the original expiry) is what
survives a restore, with the same half-open boundary as level 3. Candidates
stall on aliasing: a snapshot that shares dict or tuple objects with the live
data, or a restore that assigns the stored snapshot itself so later writes
corrupt it. Also watch for counting expired records in `backup` and for
a restore that forgets to move "now" for the plain methods.
