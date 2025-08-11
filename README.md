# RTComments — Realtime Comments API & WebSocket Stream

A lightweight Django + DRF + Channels project that provides a REST API for post comments and a WebSocket stream to broadcast comment events in real time.

> Stack: **Django 5.2**, **Django REST Framework**, **Django Channels**, **Daphne**, optional **Redis** (for production channel layer).

---

## Quick Start

```bash
# 1) Create & activate a virtualenv (Windows PowerShell example)
py -m venv venv
venv\Scripts\activate

# 2) Install deps
pip install django djangorestframework channels daphne bleach

# 3) Run migrations & create a user
python manage.py migrate
python manage.py createsuperuser

# 4) Start the ASGI server (Daphne)
daphne -b 127.0.0.1 -p 8000 RTComments.asgi:application
# or for quick tests (limited WS support), you can still do:
# python manage.py runserver
```

**Dev channel layer:** in-memory (default). For production, use Redis:

```python
# settings.py (example)
CHANNEL_LAYERS = {
  "default": {
    "BACKEND": "channels_redis.core.RedisChannelLayer",
    "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
  }
}
```

---

## Data Model

`Comment`

| Field       | Type      | Notes                               |
|-------------|-----------|-------------------------------------|
| id          | int       | Auto PK                              |
| post_id     | int       | The post/entity id the comment belongs to |
| user        | FK(User)  | Author (set automatically on create) |
| text        | char(750) | Sanitized with `bleach`              |
| created_at  | datetime  | Auto                                |
| updated_at* | datetime  | Auto                                |
| is_deleted  | bool      | Soft delete flag                     |

> `*` Depending on your local code, this may appear as `updated_At` (note the capital `A`). Keep your API docs consistent with your codebase.

---

## Authentication

- **Create / Update / Delete** require authentication (session or token).
- **List** may be public (as configured).

---

## REST API

Base path: `http://127.0.0.1:8000/api/`

### 1) List Comments (optionally by post)

**GET** `/api/comments/?post=<post_id>`

**Query Params**

- `post` (optional, int): filters comments for a given `post_id`.

**Response 200** — JSON array of comments

```json
[
  {
    "id": 12,
    "post_id": 42,
    "user": 7,
    "text": "Nice post!",
    "created_at": "2025-08-11T09:40:00Z",
    "updated_at": "2025-08-11T09:41:10Z",
    "is_deleted": false
  }
]
```

**cURL**

```bash
curl "http://127.0.0.1:8000/api/comments/?post=42"
```

---

### 2) Create Comment

**POST** `/api/comments/`  _(Auth required)_

**Body** (JSON)

```json
{
  "post_id": 42,
  "text": "Harika oldu!"
}
```

> `user` is taken from the authenticated request; `text` is sanitized server-side.

**Response 201** — created comment object.

**cURL**

```bash
curl -X POST "http://127.0.0.1:8000/api/comments/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"post_id":42,"text":"Harika oldu!"}'
```

---

### 3) Retrieve Comment

**GET** `/api/comments/<id>/`

**Response 200** — comment object.

**cURL**

```bash
curl "http://127.0.0.1:8000/api/comments/12/"
```

---

### 4) Update Comment (Partial)

**PATCH** `/api/comments/<id>/`  _(Auth required)_

**Body** (JSON)

```json
{ "text": "Edited text" }
```

**Response 200** — updated comment object.

**cURL**

```bash
curl -X PATCH "http://127.0.0.1:8000/api/comments/12/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"text":"Edited text"}'
```

---

### 5) Soft Delete Comment

**DELETE** `/api/comments/<id>/`  _(Auth required)_

- Marks the comment `is_deleted = true` and broadcasts a deletion event.

**Response 204** — no content.

**cURL**

```bash
curl -X DELETE "http://127.0.0.1:8000/api/comments/12/" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## WebSocket — Real‑Time Comment Stream

**Purpose:** receive real-time events for a specific post’s comments.

**URL pattern (example):**

```
ws://127.0.0.1:8000/ws/comments/<post_id>/
```

> The exact path comes from your app’s `routing.py`. Ensure it routes to the `CommentStream` consumer with a `post_id` URL kwarg.

### Events

Server sends JSON messages with the shape:

```json
{
  "type": "comment.created | comment.updated | comment.deleted",
  "data": { ... }
}
```

**Payloads**

- **`comment.created`** — contains the full created comment
- **`comment.updated`** — contains the updated comment
- **`comment.deleted`** — contains `{ "id": <int>, "post_id": <int> }`

### Minimal Client Example

```js
const postId = 42;
const ws = new WebSocket(`ws://127.0.0.1:8000/ws/comments/${postId}/`);

ws.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  switch (msg.type) {
    case "comment.created":
      // append msg.data to UI
      break;
    case "comment.updated":
      // update comment in UI
      break;
    case "comment.deleted":
      // remove comment from UI (by id)
      break;
  }
};
```

---

## Notes & Behavior

- **Bleach sanitization:** incoming `text` is cleaned server-side.
- **Soft deletes:** deleted comments won’t appear in lists; a deletion event is still broadcast to clients.
- **Transaction safety:** WebSocket broadcasts are scheduled on DB `on_commit`, so clients only receive events for committed changes.
- **Throttling (DRF):** default rates are `20/min` for anonymous and `60/min` for authenticated users (adjust in `REST_FRAMEWORK` settings).

---

## Testing with cURL & wscat

```bash
# REST
curl "http://127.0.0.1:8000/api/comments/?post=42"

# WS (requires wscat: npm i -g wscat)
wscat -c "ws://127.0.0.1:8000/ws/comments/42/"
```

---

## Project Structure (high‑level)

```
RTComments/
  commentingapp/
    models.py        # Comment model
    serializers.py   # CommentSerializer (bleach sanitization)
    views.py         # ListCreate + RetrieveUpdateDestroy + broadcast
    consumers.py     # CommentStream (WS group per post)
    routing.py       # websocket_urlpatterns (path -> CommentStream)
  RTComments/
    settings.py      # DRF throttle, Channels, Channel layers
    asgi.py          # ProtocolTypeRouter (http + websocket)
    urls.py          # API routes include commentingapp.urls
```
