# Classes App for fofofish

Online classroom app integrated with `account.User`.

## Role Mapping

- Teacher: `account.User.role == "teacher"`
- Student: `account.User.role == "user"`

## Main Endpoints

- `GET/POST /api/v1/classes/`
- `GET/PATCH /api/v1/classes/{id}/`
- `POST /api/v1/classes/{id}/start/`
- `POST /api/v1/classes/{id}/end/`
- `POST /api/v1/classes/{id}/cancel/`
- `POST /api/v1/classes/{id}/enroll/`
- `GET /api/v1/classes/{id}/enrollments/`
- `POST /api/v1/classes/{id}/join/`
- `POST /api/v1/classes/{id}/leave/`
- `GET /api/v1/classes/{id}/participants/`
- `POST/GET /api/v1/classes/{id}/messages/`
- `DELETE /api/v1/classes/{id}/messages/{message_id}/`
- `POST /api/v1/classes/{id}/hand/raise/`
- `POST /api/v1/classes/{id}/hand/lower/`
- `GET /api/v1/classes/{id}/hands/`
- `POST /api/v1/classes/{id}/hands/{user_id}/acknowledge/`
- `POST /api/v1/classes/{id}/reactions/`
- `POST /api/v1/classes/{id}/grant-mic/{user_id}/`
- `POST /api/v1/classes/{id}/revoke-mic/{user_id}/`
- `POST /api/v1/classes/{id}/kick/{user_id}/`
- `POST /api/v1/classes/{id}/spotlight/{user_id}/`
- `POST /api/v1/classes/{id}/whiteboard/grant/{user_id}/`
- `POST /api/v1/classes/{id}/whiteboard/revoke/{user_id}/`
- `POST /api/v1/classes/{id}/whiteboard/clear/`

## Deployment

Configure Centrifugo and RTC secrets in environment variables before production use, then run:

```bash
python manage.py migrate classes
```
