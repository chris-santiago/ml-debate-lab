# Entry Types & Schema

Every journal entry has a type that determines its required fields, confirmation behavior, and weight.

## Entry type reference

### issue

A bug or inconsistency identified during investigation.

| Field | Required | Type |
|-------|----------|------|
| `description` | Yes | string |
| `severity` | Yes | `low` \| `moderate` \| `high` \| `critical` |
| `context` | No | string |
| `tags` | No | string[] |

**Confirm:** No (logged immediately). **Weight:** Light.

---

### resolution

A verified fix for a previously logged issue.

| Field | Required | Type |
|-------|----------|------|
| `description` | Yes | string |
| `linked_issue_id` | No | string (ID of the issue being resolved) |
| `approach` | No | string |
| `evidence` | No | string |

**Confirm:** No. **Weight:** Light.

---

### decision

A direction confirmed by the user.

| Field | Required | Type |
|-------|----------|------|
| `description` | Yes | string |
| `rationale` | Yes | string |
| `alternatives` | No | string |
| `implications` | No | string |
| `linked_issue_id` | No | string |
| `linked_id` | No | string |

**Confirm:** Yes (draft shown first). **Weight:** Medium.

---

### discovery

An unexpected finding that changes understanding or approach.

| Field | Required | Type |
|-------|----------|------|
| `description` | Yes | string |
| `implications` | No | string |
| `source` | No | string |
| `linked_issue_id` | No | string |

**Confirm:** Yes. **Weight:** Medium.

---

### hypothesis

A testable claim to be investigated.

| Field | Required | Type |
|-------|----------|------|
| `description` | Yes | string |
| `expected_result` | No | string |
| `metric` | No | string |
| `linked_issue_id` | No | string |

**Confirm:** Yes. **Weight:** Medium.

---

### lesson

A root-cause explanation — *why* something broke.

| Field | Required | Type |
|-------|----------|------|
| `description` | Yes | string |
| `context` | No | string |
| `applies_to` | No | string |
| `linked_id` | No | string |

**Confirm:** No. **Weight:** Light.

---

### memo

A general-purpose note that doesn't fit other types.

| Field | Required | Type |
|-------|----------|------|
| `description` | Yes | string |
| `detail` | No | string |
| `context` | No | string |
| `tags` | No | string[] |
| `linked_issue_id` | No | string |
| `linked_id` | No | string |

**Confirm:** No. **Weight:** Light.

---

### experiment

A verdict on a tested hypothesis.

| Field | Required | Type |
|-------|----------|------|
| `description` | Yes | string |
| `verdict` | Yes | `confirmed` \| `refuted` \| `inconclusive` |
| `linked_hypothesis_id` | No | string |
| `linked_issue_id` | No | string |
| `metric` | No | string |
| `result` | No | string |

**Confirm:** Yes. **Weight:** Medium.

---

### summary

A phase or block completion summary.

| Field | Required | Type |
|-------|----------|------|
| `description` | Yes | string |
| `key_decisions` | No | string |
| `open_threads` | No | string |

**Confirm:** Yes. **Weight:** Medium.

---

### post_mortem

A structured failure analysis.

| Field | Required | Type |
|-------|----------|------|
| `description` | Yes | string |
| `what_failed` | Yes | string |
| `root_cause` | Yes | string |
| `linked_issue_id` | Yes | string |
| `contributing_factors` | No | string |
| `lessons` | No | string |
| `severity` | No | string |
| `scope` | No | string |
| `remediation` | No | string |
| `detail` | No | string |

**Confirm:** Yes. **Weight:** Heavy.

---

### checkpoint

A session state snapshot.

| Field | Required | Type |
|-------|----------|------|
| `in_progress` | Yes | string |
| `pending_decisions` | No | string |
| `recently_completed` | No | string |
| `key_context` | No | string |
| `git_state` | No | string |
| `open_threads` | No | string |

**Confirm:** Yes. **Weight:** Heavy.

---

### git

A commit with audit context. Written by `/log-commit`.

| Field | Required | Type |
|-------|----------|------|
| `commit_hash` | Yes | string |
| `message` | Yes | string |
| `branch` | Yes | string |
| `files_changed` | No | string |
| `diff_summary` | No | string |

**Confirm:** Yes (via `/log-commit` flow). **Weight:** N/A.

---

## Common envelope fields

Every entry, regardless of type, includes:

| Field | Description |
|-------|-------------|
| `id` | Unique 8-character hex ID |
| `timestamp` | ISO 8601 timestamp |
| `type` | Entry type (from table above) |
| `project` | Repository name |
| `session_id` | Claude Code session identifier |
