"""OpenAPI 3.0 specification for the portfolio-MDE_dashboard API.

This module centralizes the Swagger/OpenAPI document used by the local
Swagger UI page and the raw JSON spec endpoint.
"""

from __future__ import annotations

OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "portfolio-MDE_dashboard API",
        "version": "1.0.0",
        "description": "Swagger/OpenAPI documentation for the Flask REST API.",
    },
    "servers": [
        {"url": "http://127.0.0.1:8000", "description": "Local development"},
    ],
    "tags": [
        {"name": "Health"},
        {"name": "Auth"},
        {"name": "Users"},
        {"name": "Companies"},
        {"name": "Trainings"},
        {"name": "Training Sessions"},
        {"name": "Conversations"},
        {"name": "Messages"},
        {"name": "Notifications"},
        {"name": "News"},
        {"name": "Formation Users"},
    ],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        },
        "schemas": {
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "message": {"type": "string"},
                            "details": {"nullable": True, "example": None, "description": "Expected type: object, array, string, boolean, number, or null."},
                        },
                        "required": ["code", "message"],
                    }
                },
            },
            "AuthLoginRequest": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "example": "admin@admin.com"},
                    "password": {"type": "string", "example": "admin"},
                },
            },
            "AuthRegisterRequest": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "example": "user@example.com"},
                    "password": {"type": "string", "example": "password123"},
                    "first_name": {"type": "string", "example": "John"},
                    "last_name": {"type": "string", "example": "Doe"},
                },
            },
            "UserCreateRequest": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string"},
                    "password": {"type": "string"},
                    "first_name": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "last_name": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "phone": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "profile_picture": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "business_card": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "is_super_admin": {"type": "boolean", "nullable": True, "example": None, "description": "Super admin only. Mint another super admin."},
                    "is_staff": {"type": "boolean", "nullable": True, "example": None, "description": "Super admin only. Create a staff account."},
                    "permissions": {"type": "array", "items": {"type": "string"}, "nullable": True, "description": "Staff rights: manage_companies, manage_users, manage_trainings, manage_news."},
                    "company_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                },
            },
            "UserCreateMultipartRequest": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string"},
                    "password": {"type": "string"},
                    "first_name": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "last_name": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "phone": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "profile_picture_file": {"type": "string", "format": "binary", "nullable": True, "description": "Upload a profile image file."},
                    "business_card_file": {"type": "string", "format": "binary", "nullable": True, "description": "Upload a business card image file."},
                    "is_super_admin": {"type": "boolean", "nullable": True, "example": None, "description": "Expected type: boolean or null."},
                    "company_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                },
            },
            "UserUpdateRequest": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "last_name": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "phone": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "profile_picture": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "business_card": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "company_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "is_super_admin": {"type": "boolean", "nullable": True, "example": None, "description": "Expected type: boolean or null."},
                    "is_active": {"type": "boolean", "nullable": True, "example": None, "description": "Expected type: boolean or null."},
                },
            },
            "UserUpdateMultipartRequest": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "last_name": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "phone": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "profile_picture_file": {"type": "string", "format": "binary", "nullable": True, "description": "Upload a profile image file."},
                    "business_card_file": {"type": "string", "format": "binary", "nullable": True, "description": "Upload a business card image file."},
                    "company_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "is_super_admin": {"type": "boolean", "nullable": True, "example": None, "description": "Expected type: boolean or null."},
                    "is_active": {"type": "boolean", "nullable": True, "example": None, "description": "Expected type: boolean or null."},
                },
            },
            "PasswordResetRequest": {
                "type": "object",
                "required": ["password"],
                "properties": {"password": {"type": "string"}},
            },
            "CompanyCreateRequest": {
                "type": "object",
                "required": ["name", "admin_email"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "website_link": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "company_picture": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "admin_email": {"type": "string"},
                    "admin_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null. Optional admin user id."},
                },
            },
            "CompanyCreateMultipartRequest": {
                "type": "object",
                "required": ["name", "admin_email"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "website_link": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "company_picture_file": {"type": "string", "format": "binary", "nullable": True, "description": "Upload a company image file."},
                    "admin_email": {"type": "string"},
                    "admin_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null. Optional admin user id."},
                },
            },
            "CompanyUpdateRequest": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "description": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "website_link": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "company_picture": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "admin_email": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "admin_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null. Optional admin user id."},
                    "is_active": {"type": "boolean", "nullable": True, "example": None, "description": "Expected type: boolean or null."},
                },
            },
            "CompanyUpdateMultipartRequest": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "description": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "website_link": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "company_picture_file": {"type": "string", "format": "binary", "nullable": True, "description": "Upload a company image file."},
                    "admin_email": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "admin_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null. Optional admin user id."},
                    "is_active": {"type": "boolean", "nullable": True, "example": None, "description": "Expected type: boolean or null."},
                },
            },
            "TrainingCreateRequest": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string"},
                    "company_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "description": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "picture": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                },
            },
            "TrainingCreateMultipartRequest": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string"},
                    "company_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "description": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "picture_file": {"type": "string", "format": "binary", "nullable": True, "description": "Upload a training image file."},
                },
            },
            "TrainingUpdateRequest": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "company_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "description": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "picture": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "is_active": {"type": "boolean", "nullable": True, "example": None, "description": "Expected type: boolean or null."},
                },
            },
            "TrainingUpdateMultipartRequest": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "company_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "description": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "picture_file": {"type": "string", "format": "binary", "nullable": True, "description": "Upload a training image file."},
                    "is_active": {"type": "boolean", "nullable": True, "example": None, "description": "Expected type: boolean or null."},
                },
            },
            "ConversationCreateRequest": {
                "type": "object",
                "properties": {
                    "participant_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "nullable": True,
                        "example": None,
                        "description": "Expected type: array of string or null.",
                    }
                },
            },
            "ConversationPatchRequest": {
                "type": "object",
                "properties": {
                    "participant_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "action": {"type": "string", "enum": ["add", "remove"], "nullable": True, "example": None, "description": "Expected type: string or null. Allowed values: add, remove."},
                },
            },
            "MessageCreateRequest": {
                "type": "object",
                "required": ["content"],
                "properties": {
                    "author_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "recipient_id": {"type": "string", "nullable": True, "example": None, "description": "Expected type: string or null."},
                    "content": {"type": "string"},
                },
            },
            "NotificationCreateRequest": {
                "type": "object",
                "required": ["recipient_id", "content"],
                "properties": {
                    "recipient_id": {"type": "string"},
                    "content": {"type": "string"},
                    "is_read": {"type": "boolean", "nullable": True, "example": None, "description": "Expected type: boolean or null."},
                },
            },
            "NewsCreateRequest": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string"},
                    "source": {"type": "string", "nullable": True, "example": None},
                    "summary": {"type": "string", "nullable": True, "example": None},
                    "url": {"type": "string", "nullable": True, "example": None},
                    "published_at": {"type": "string", "format": "date-time", "nullable": True, "example": None},
                    "category": {
                        "type": "string",
                        "nullable": True,
                        "enum": ["actualités", "réglementation", "vie-entreprises", "opportunités", "territoire"],
                        "example": "réglementation",
                    },
                },
            },
            "TrainingSessionCreateRequest": {
                "type": "object",
                "required": ["start_date", "end_date", "max_participants"],
                "properties": {
                    "start_date": {"type": "string", "format": "date-time", "example": "2027-09-01T09:00:00"},
                    "end_date": {"type": "string", "format": "date-time", "example": "2027-09-03T17:00:00"},
                    "max_participants": {"type": "integer", "example": 15},
                    "location": {"type": "string", "nullable": True, "example": "Paris - Salle A"},
                    "link": {"type": "string", "nullable": True, "example": "https://meet.example.com/xyz"},
                },
            },
            "TrainingSessionUpdateRequest": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date-time", "nullable": True},
                    "end_date": {"type": "string", "format": "date-time", "nullable": True},
                    "max_participants": {"type": "integer", "nullable": True},
                    "location": {"type": "string", "nullable": True},
                    "link": {"type": "string", "nullable": True},
                    "status": {
                        "type": "string",
                        "enum": ["upcoming", "full", "completed", "cancelled"],
                        "nullable": True,
                        "description": "Setting to 'completed' auto-validates all enrolled users.",
                    },
                },
            },
        },
    },
    "security": [{"bearerAuth": []}],
    "paths": {
        "/": {
            "get": {
                "tags": ["Health"],
                "summary": "Health check",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/auth/register": {
            "post": {
                "tags": ["Auth"],
                "summary": "Register a user",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AuthRegisterRequest"}}},
                },
                "responses": {"201": {"description": "Created"}, "400": {"description": "Validation error"}},
            }
        },
        "/auth/login": {
            "post": {
                "tags": ["Auth"],
                "summary": "Login and obtain JWT tokens",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AuthLoginRequest"}}},
                },
                "responses": {"200": {"description": "OK"}, "401": {"description": "Invalid credentials"}},
            }
        },
        "/auth/refresh": {
            "post": {
                "tags": ["Auth"],
                "summary": "Refresh access token",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/auth/logout": {
            "post": {
                "tags": ["Auth"],
                "summary": "Revoke current token",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/users": {
            "get": {
                "tags": ["Users"],
                "summary": "List users",
                "parameters": [
                    {"name": "limit", "in": "query",
                        "schema": {"type": "integer"}},
                    {"name": "company_id", "in": "query",
                        "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "OK"}, "401": {"$ref": "#/components/schemas/ErrorResponse"}},
            },
            "post": {
                "tags": ["Users"],
                "summary": "Create user",
                "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {"$ref": "#/components/schemas/UserCreateMultipartRequest"}}}},
                "responses": {"201": {"description": "Created"}},
            },
        },
        "/users/me": {
            "get": {"tags": ["Users"], "summary": "Current user profile", "responses": {"200": {"description": "OK"}}},
            "patch": {
                "tags": ["Users"],
                "summary": "Update current user",
                "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {"$ref": "#/components/schemas/UserUpdateMultipartRequest"}}}},
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/me": {"get": {"tags": ["Users"], "summary": "Alias for current user profile", "responses": {"200": {"description": "OK"}}}},
        "/users/{user_id}": {
            "get": {"tags": ["Users"], "summary": "Get user by id", "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}},
            "put": {"tags": ["Users"], "summary": "Replace user fields", "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}], "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {"$ref": "#/components/schemas/UserUpdateMultipartRequest"}}}}, "responses": {"200": {"description": "OK"}}},
            "patch": {"tags": ["Users"], "summary": "Partial update user", "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}], "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {"$ref": "#/components/schemas/UserUpdateMultipartRequest"}}}}, "responses": {"200": {"description": "OK"}}},
            "delete": {"tags": ["Users"], "summary": "Permanently delete user", "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}},
        },
        "/users/{user_id}/deactivate": {"patch": {"tags": ["Users"], "summary": "Deactivate user without deleting", "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}},
        "/users/{user_id}/reset-password": {"post": {"tags": ["Users"], "summary": "Reset password", "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}], "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PasswordResetRequest"}}}}, "responses": {"200": {"description": "OK"}}}},
        "/companies": {"get": {"tags": ["Companies"], "summary": "List companies", "responses": {"200": {"description": "OK"}}}, "post": {"tags": ["Companies"], "summary": "Create company", "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {"$ref": "#/components/schemas/CompanyCreateMultipartRequest"}}}}, "responses": {"201": {"description": "Created"}, "400": {"description": "admin_email is required"}}}},
        "/companies/{company_id}": {"get": {"tags": ["Companies"], "summary": "Get company", "parameters": [{"name": "company_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}, "patch": {"tags": ["Companies"], "summary": "Update company", "parameters": [{"name": "company_id", "in": "path", "required": True, "schema": {"type": "string"}}], "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {"$ref": "#/components/schemas/CompanyUpdateMultipartRequest"}}}}, "responses": {"200": {"description": "OK"}}}, "delete": {"tags": ["Companies"], "summary": "Deactivate company", "parameters": [{"name": "company_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}},
        "/companies/{company_id}/users": {"get": {"tags": ["Companies"], "summary": "List users for company", "parameters": [{"name": "company_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}},
        "/companies/{company_id}/users/{user_id}": {"post": {"tags": ["Companies"], "summary": "Assign user to company", "parameters": [{"name": "company_id", "in": "path", "required": True, "schema": {"type": "string"}}, {"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}, "delete": {"tags": ["Companies"], "summary": "Remove user from company", "parameters": [{"name": "company_id", "in": "path", "required": True, "schema": {"type": "string"}}, {"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}},
        "/trainings": {"get": {"tags": ["Trainings"], "summary": "List trainings", "responses": {"200": {"description": "OK"}}}, "post": {"tags": ["Trainings"], "summary": "Create training", "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {"$ref": "#/components/schemas/TrainingCreateMultipartRequest"}}}}, "responses": {"201": {"description": "Created"}}}},
        "/trainings/{training_id}": {"get": {"tags": ["Trainings"], "summary": "Get training", "parameters": [{"name": "training_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}, "patch": {"tags": ["Trainings"], "summary": "Update training", "parameters": [{"name": "training_id", "in": "path", "required": True, "schema": {"type": "string"}}], "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {"$ref": "#/components/schemas/TrainingUpdateMultipartRequest"}}}}, "responses": {"200": {"description": "OK"}}}, "delete": {"tags": ["Trainings"], "summary": "Deactivate training", "parameters": [{"name": "training_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}},
        "/trainings/{training_id}/interest": {
            "post": {
                "tags": ["Trainings"],
                "summary": "Express interest in a training (no session required)",
                "parameters": [{"name": "training_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"201": {"description": "Interest recorded"}, "404": {"description": "Training not found"}},
            },
            "delete": {
                "tags": ["Trainings"],
                "summary": "Remove interest in a training",
                "parameters": [{"name": "training_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Interest removed"}, "404": {"description": "Interest or training not found"}},
            },
        },
        "/trainings/{training_id}/interested": {
            "get": {
                "tags": ["Trainings"],
                "summary": "List users who expressed interest (admin only)",
                "parameters": [{"name": "training_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "OK"}, "403": {"description": "Forbidden"}},
            }
        },
        "/trainings/{training_id}/enrollments": {
            "get": {
                "tags": ["Trainings"],
                "summary": "List enrollments for a training",
                "parameters": [
                    {"name": "training_id", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "type", "in": "query", "required": False, "schema": {"type": "string", "enum": ["interested", "enrolled", "completed"]}, "description": "Filter by lifecycle type"},
                ],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/trainings/{training_id}/sessions": {
            "get": {
                "tags": ["Training Sessions"],
                "summary": "List sessions for a training",
                "parameters": [{"name": "training_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "OK"}, "404": {"description": "Training not found"}},
            },
            "post": {
                "tags": ["Training Sessions"],
                "summary": "Create a session for a training (admin only)",
                "parameters": [{"name": "training_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/TrainingSessionCreateRequest"}}}},
                "responses": {"201": {"description": "Session created"}, "400": {"description": "Validation error"}, "403": {"description": "Forbidden"}, "404": {"description": "Training not found"}},
            },
        },
        "/trainings/completions": {
            "get": {
                "tags": ["Training Sessions"],
                "summary": "List completed trainings (admin sees all, user sees own)",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/training-sessions": {
            "get": {
                "tags": ["Training Sessions"],
                "summary": "List all training sessions",
                "parameters": [
                    {"name": "training_id", "in": "query", "required": False, "schema": {"type": "string"}, "description": "Filter by training UUID"},
                    {"name": "status", "in": "query", "required": False, "schema": {"type": "string", "enum": ["upcoming", "full", "completed", "cancelled"]}, "description": "Filter by status"},
                ],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/training-sessions/{session_id}": {
            "get": {
                "tags": ["Training Sessions"],
                "summary": "Get a training session by id",
                "parameters": [{"name": "session_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "OK"}, "404": {"description": "Session not found"}},
            },
            "patch": {
                "tags": ["Training Sessions"],
                "summary": "Update a session (admin only). Setting status=completed auto-validates all enrolled users.",
                "parameters": [{"name": "session_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/TrainingSessionUpdateRequest"}}}},
                "responses": {"200": {"description": "OK"}, "403": {"description": "Forbidden"}, "404": {"description": "Session not found"}},
            },
            "delete": {
                "tags": ["Training Sessions"],
                "summary": "Cancel a session (admin only)",
                "parameters": [{"name": "session_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Session cancelled"}, "403": {"description": "Forbidden"}, "404": {"description": "Session not found"}},
            },
        },
        "/training-sessions/{session_id}/enroll": {
            "post": {
                "tags": ["Training Sessions"],
                "summary": "Enroll current user in a session. Auto-upgrades interest to enrolled. Rejected if session is full.",
                "parameters": [{"name": "session_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"201": {"description": "Enrolled"}, "404": {"description": "Session not found"}, "409": {"description": "Session full or already enrolled"}},
            },
            "delete": {
                "tags": ["Training Sessions"],
                "summary": "Unenroll current user from a session. Reverts session from full to upcoming if applicable.",
                "parameters": [{"name": "session_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Unenrolled"}, "404": {"description": "Session or enrollment not found"}},
            },
        },
        "/users/{user_id}/trainings": {
            "get": {
                "tags": ["Trainings"],
                "summary": "List enrollments for a specific user",
                "parameters": [
                    {"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "type", "in": "query", "required": False, "schema": {"type": "string", "enum": ["interested", "enrolled", "completed"]}, "description": "Filter by lifecycle type"},
                ],
                "responses": {"200": {"description": "OK"}, "404": {"description": "User not found"}},
            }
        },
        "/me/trainings": {
            "get": {
                "tags": ["Trainings"],
                "summary": "List current user's enrollments",
                "parameters": [
                    {"name": "type", "in": "query", "required": False, "schema": {"type": "string", "enum": ["interested", "enrolled", "completed"]}, "description": "Filter by lifecycle type"},
                ],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/conversations": {"get": {"tags": ["Conversations"], "summary": "List conversations", "responses": {"200": {"description": "OK"}}}, "post": {"tags": ["Conversations"], "summary": "Create conversation", "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ConversationCreateRequest"}}}}, "responses": {"201": {"description": "Created"}}}},
        "/rooms": {"get": {"tags": ["Conversations"], "summary": "Alias for list conversations", "responses": {"200": {"description": "OK"}}}, "post": {"tags": ["Conversations"], "summary": "Alias for create conversation", "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ConversationCreateRequest"}}}}, "responses": {"201": {"description": "Created"}}}},
        "/conversations/{conversation_id}": {"get": {"tags": ["Conversations"], "summary": "Get conversation", "parameters": [{"name": "conversation_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}, "patch": {"tags": ["Conversations"], "summary": "Modify conversation participants", "parameters": [{"name": "conversation_id", "in": "path", "required": True, "schema": {"type": "string"}}], "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ConversationPatchRequest"}}}}, "responses": {"200": {"description": "OK"}}}, "delete": {"tags": ["Conversations"], "summary": "Deactivate conversation", "parameters": [{"name": "conversation_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}},
        "/rooms/{conversation_id}": {"get": {"tags": ["Conversations"], "summary": "Alias for get conversation", "parameters": [{"name": "conversation_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}, "patch": {"tags": ["Conversations"], "summary": "Alias for modify conversation participants", "parameters": [{"name": "conversation_id", "in": "path", "required": True, "schema": {"type": "string"}}], "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ConversationPatchRequest"}}}}, "responses": {"200": {"description": "OK"}}}, "delete": {"tags": ["Conversations"], "summary": "Alias for deactivate conversation", "parameters": [{"name": "conversation_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}},
        "/conversations/{conversation_id}/messages": {"get": {"tags": ["Messages"], "summary": "List messages in conversation", "parameters": [{"name": "conversation_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}, "post": {"tags": ["Messages"], "summary": "Post message in conversation", "parameters": [{"name": "conversation_id", "in": "path", "required": True, "schema": {"type": "string"}}], "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageCreateRequest"}}}}, "responses": {"201": {"description": "Created"}}}},
        "/rooms/{conversation_id}/messages": {"get": {"tags": ["Messages"], "summary": "Alias for list messages in conversation", "parameters": [{"name": "conversation_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}, "post": {"tags": ["Messages"], "summary": "Alias for post message in conversation", "parameters": [{"name": "conversation_id", "in": "path", "required": True, "schema": {"type": "string"}}], "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageCreateRequest"}}}}, "responses": {"201": {"description": "Created"}}}},
        "/messages": {"get": {"tags": ["Messages"], "summary": "List messages", "responses": {"200": {"description": "OK"}}}},
        "/messages/{message_id}": {"delete": {"tags": ["Messages"], "summary": "Delete message", "parameters": [{"name": "message_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}},
        "/notifications": {"get": {"tags": ["Notifications"], "summary": "List notifications", "responses": {"200": {"description": "OK"}}}, "post": {"tags": ["Notifications"], "summary": "Create notification", "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/NotificationCreateRequest"}}}}, "responses": {"201": {"description": "Created"}}}},
        "/notifications/{notification_id}": {"patch": {"tags": ["Notifications"], "summary": "Mark notification as read", "parameters": [{"name": "notification_id", "in": "path", "required": True, "schema": {"type": "string"}}], "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {"is_read": {"type": "boolean"}}}}}}, "responses": {"200": {"description": "OK"}}}, "delete": {"tags": ["Notifications"], "summary": "Delete notification", "parameters": [{"name": "notification_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}}},
        "/news": {
            "get": {
                "tags": ["News"],
                "summary": "List news items",
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 100}},
                    {
                        "name": "category",
                        "in": "query",
                        "description": "Filter by category",
                        "schema": {"type": "string", "enum": ["actualités", "réglementation", "vie-entreprises", "opportunités", "territoire"]},
                    },
                    {"name": "source", "in": "query", "description": "Filter by source name (e.g. BODACC, BOAMP)", "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "OK"}},
            },
            "post": {
                "tags": ["News"],
                "summary": "Create news item",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/NewsCreateRequest"}}}},
                "responses": {"201": {"description": "Created"}},
                "security": [{"BearerAuth": []}],
            },
        },
        "/news/{news_id}": {
            "get": {"tags": ["News"], "summary": "Get news item", "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}},
            "delete": {"tags": ["News"], "summary": "Delete news item", "parameters": [{"name": "news_id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}, "security": [{"BearerAuth": []}]},
        },
        "/news/sync": {
            "post": {
                "tags": ["News"],
                "summary": "Trigger external news sync",
                "description": "Fetches latest items from BODACC, BOAMP, Journal Officiel, BOFiP and URSSAF and stores new entries.",
                "responses": {
                    "200": {"description": "Sync completed", "content": {"application/json": {"schema": {"type": "object", "properties": {"synced": {"type": "integer", "description": "Number of new items inserted"}}}}}},
                    "500": {"description": "Sync failed"},
                },
                "security": [{"BearerAuth": []}],
            }
        },
        "/formation-users": {
            "get": {
                "tags": ["Formation Users"],
                "summary": "List all formation-user relations (admin only)",
                "responses": {"200": {"description": "OK"}, "403": {"description": "Forbidden"}},
            }
        },
        "/formation-users/{relation_id}": {
            "get": {
                "tags": ["Formation Users"],
                "summary": "Get a formation-user relation by id",
                "parameters": [{"name": "relation_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "OK"}, "404": {"description": "Not found"}},
            },
            "patch": {
                "tags": ["Formation Users"],
                "summary": "Revoke a completion — sets type back to enrolled (admin only)",
                "parameters": [{"name": "relation_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "OK"}, "403": {"description": "Forbidden"}, "404": {"description": "Completed enrollment not found"}},
            },
            "delete": {
                "tags": ["Formation Users"],
                "summary": "Delete a formation-user relation (admin only)",
                "parameters": [{"name": "relation_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "OK"}, "403": {"description": "Forbidden"}, "404": {"description": "Not found"}},
            },
        },
    },
}

SWAGGER_UI_HTML = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>portfolio-MDE_dashboard API Docs</title>
    <link rel=\"stylesheet\" href=\"https://unpkg.com/swagger-ui-dist@5/swagger-ui.css\" />
    <style>
            :root {
                color-scheme: light;
            }

            html, body {
                margin: 0;
                padding: 0;
                background: #f8fafc;
                color: #0f172a;
                font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }

      #swagger-ui { max-width: 100vw; }

            .topbar {
                display: none;
            }

            .swagger-ui .wrapper {
                background: #f8fafc;
            }

            .swagger-ui .info .title,
            .swagger-ui .info p,
            .swagger-ui .info li,
            .swagger-ui .scheme-container,
            .swagger-ui .opblock-tag,
            .swagger-ui .renderedMarkdown,
            .swagger-ui .parameter__name,
            .swagger-ui .parameter__type,
            .swagger-ui .response-col_status,
            .swagger-ui .response-col_description,
            .swagger-ui .tab li,
            .swagger-ui .opblock .opblock-summary-description {
                color: #0f172a;
            }

            .swagger-ui .opblock {
                border-color: #cbd5e1;
                background: #ffffff;
            }

            .swagger-ui .opblock.opblock-get {
                border-color: #93c5fd;
                background: #eff6ff;
            }

            .swagger-ui .opblock.opblock-post {
                border-color: #86efac;
                background: #f0fdf4;
            }

            .swagger-ui .opblock.opblock-patch,
            .swagger-ui .opblock.opblock-put {
                border-color: #fcd34d;
                background: #fffbeb;
            }

            .swagger-ui .opblock.opblock-delete {
                border-color: #fca5a5;
                background: #fef2f2;
            }

            .swagger-ui .btn,
            .swagger-ui button,
            .swagger-ui input,
            .swagger-ui select,
            .swagger-ui textarea {
                font-family: inherit;
            }

            .swagger-ui select,
            .swagger-ui input,
            .swagger-ui textarea {
                background: #ffffff;
                color: #0f172a;
                border-color: #cbd5e1;
            }

            .swagger-ui .btn.authorize,
            .swagger-ui .btn.execute {
                background-color: #2563eb;
                color: #ffffff;
                border-color: #2563eb;
            }

            .swagger-ui .btn.authorize:hover,
            .swagger-ui .btn.execute:hover {
                background-color: #1d4ed8;
                border-color: #1d4ed8;
            }
    </style>
  </head>
  <body>
    <div id=\"swagger-ui\"></div>
    <script src=\"https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js\"></script>
    <script>
      window.onload = () => {
        window.ui = SwaggerUIBundle({
          url: '/openapi.json',
          dom_id: '#swagger-ui',
          deepLinking: true,
          displayRequestDuration: true,
          docExpansion: 'list',
          persistAuthorization: true,
        });
      };
    </script>
  </body>
</html>
"""
