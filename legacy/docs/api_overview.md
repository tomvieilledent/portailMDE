# API Overview

## Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`

## Users

- `GET /users`
- `POST /users`
- `GET /users/me` / `GET /me`
- `PATCH /users/me` / `PATCH /me`
- `GET /users/{id}`
- `PUT /users/{id}`
- `PATCH /users/{id}`
- `DELETE /users/{id}`
- `PATCH /users/{id}/deactivate`
- `POST /users/{id}/reset-password`
- `GET /users/{id}/trainings`
- `GET /me/trainings`

## Companies

- `GET /companies`
- `POST /companies`
- `GET /companies/{id}`
- `PATCH /companies/{id}`
- `DELETE /companies/{id}`
- `GET /companies/{id}/users`
- `POST /companies/{id}/users/{user_id}`
- `DELETE /companies/{id}/users/{user_id}`

## Trainings

- `GET /trainings`
- `POST /trainings`
- `GET /trainings/completions`
- `GET /trainings/{id}`
- `PATCH /trainings/{id}`
- `DELETE /trainings/{id}`
- `POST /trainings/{id}/interest`
- `DELETE /trainings/{id}/interest`
- `GET /trainings/{id}/interested`
- `GET /trainings/{id}/enrollments`
- `GET /trainings/{id}/sessions`
- `POST /trainings/{id}/sessions`

## Training Sessions

- `GET /training-sessions`
- `GET /training-sessions/{id}`
- `PATCH /training-sessions/{id}`
- `DELETE /training-sessions/{id}`
- `POST /training-sessions/{id}/enroll`
- `DELETE /training-sessions/{id}/enroll`

## Conversations / Rooms

- `GET /conversations` / `GET /rooms`
- `POST /conversations` / `POST /rooms`
- `GET /conversations/{id}` / `GET /rooms/{id}`
- `PATCH /conversations/{id}` / `PATCH /rooms/{id}`
- `DELETE /conversations/{id}` / `DELETE /rooms/{id}`
- `GET /conversations/{id}/messages` / `GET /rooms/{id}/messages`
- `POST /conversations/{id}/messages` / `POST /rooms/{id}/messages`

## Messages

- `GET /messages`
- `DELETE /messages/{id}`

## Notifications

- `GET /notifications`
- `POST /notifications`
- `PATCH /notifications/{id}`
- `DELETE /notifications/{id}`

## News

- `GET /news`
- `POST /news`
- `POST /news/sync`
- `GET /news/{id}`
- `DELETE /news/{id}`

## Formation Users

- `GET /formation-users`
- `GET /formation-users/{id}`
- `PATCH /formation-users/{id}`
- `DELETE /formation-users/{id}`

## Misc

- `GET /status`
- `GET /openapi.json`
- `GET /` / `GET /docs` / `GET /swagger` — Swagger UI
- `GET /uploads/{filename}`

## Error Codes

All errors use this JSON shape:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "user not found",
    "details": null
  }
}
```

Defined codes:

- `BAD_REQUEST`
- `UNAUTHORIZED`
- `FORBIDDEN`
- `NOT_FOUND`
- `CONFLICT`
- `VALIDATION_ERROR`
- `INVALID_CREDENTIALS`
- `INVALID_TOKEN`
- `TOKEN_EXPIRED`
- `TOKEN_REVOKED`
- `NOT_IMPLEMENTED`
- `INTERNAL_ERROR`
