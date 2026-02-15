# Users API Specification

## Overview

This document specifies the REST API endpoints required for the Users module of the Evotrack application. The API should follow RESTful conventions and return JSON responses.

**Base URL:** `/api/v1`

**Authentication:** All endpoints require Bearer token authentication via `Authorization` header.

---

## Data Models

### User Object

```json
{
  "id": "string (UUID)",
  "email": "string (unique, required)",
  "first_name": "string (required)",
  "last_name": "string (required)",
  "avatar": "string (URL, optional)",
  "phone": "string (optional)",
  "date_of_birth": "string (ISO 8601 date, optional)",
  "identification": "string (ID/passport number, optional)",
  "nationality": "string (optional)",
  "role": "string (enum: 'owner', 'admin', 'member')",
  "department_id": "string (UUID, optional)",
  "department": "string (department name, optional - returned in responses)",
  "language": "string (default: 'en', enum: 'en', 'es', 'fr', 'pt')",
  "timezone": "string (IANA timezone, default: 'UTC')",
  "status": "string (enum: 'ACTIVE', 'PENDING', 'INACTIVE')",
  "is_active": "boolean",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime, optional)"
}
```

### Paginated Response

```json
{
  "data": [User],
  "meta": {
    "current_page": "integer",
    "per_page": "integer",
    "total": "integer",
    "total_pages": "integer"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {} // optional validation errors
  }
}
```

---

## Endpoints

### 1. List Users (Paginated)

Retrieve a paginated list of users for an organization.

**Endpoint:** `GET /organizations/{organizationId}/users`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| organizationId | string (UUID) | Yes | Organization ID |

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number |
| page_size | integer | No | 20 | Items per page (max: 100) |
| search | string | No | - | Search by name or email |
| role | string | No | - | Filter by role (owner, admin, member) |
| department | string | No | - | Filter by department ID |
| is_active | boolean | No | - | Filter by active status |
| status | string | No | - | Filter by status (ACTIVE, PENDING, INACTIVE) |
| sort_by | string | No | created_at | Field to sort by (created_at, first_name, last_name) |
| sort_order | string | No | desc | Sort order (asc, desc) |

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@company.com",
      "first_name": "John",
      "last_name": "Doe",
      "avatar": "https://example.com/avatars/john.jpg",
      "phone": "+1 809 123 4567",
      "date_of_birth": "1990-05-15",
      "identification": "001-1234567-8",
      "nationality": "Dominican",
      "role": "admin",
      "department_id": "dept-123",
      "department": "Engineering",
      "language": "en",
      "timezone": "America/Santo_Domingo",
      "status": "ACTIVE",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-02-01T14:22:00Z"
    }
  ],
  "meta": {
    "current_page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

---

### 2. Get User by ID

Retrieve a single user by their ID.

**Endpoint:** `GET /users/{userId}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | string (UUID) | Yes | User ID |

**Response:** `200 OK`
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "avatar": "https://example.com/avatars/john.jpg",
    "phone": "+1 809 123 4567",
    "date_of_birth": "1990-05-15",
    "identification": "001-1234567-8",
    "nationality": "Dominican",
    "role": "admin",
    "department_id": "dept-123",
    "department": "Engineering",
    "language": "en",
    "timezone": "America/Santo_Domingo",
    "status": "ACTIVE",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-02-01T14:22:00Z"
  }
}
```

**Error Responses:**
- `404 Not Found` - User not found

---

### 3. Create User

Create a new user in the organization.

**Endpoint:** `POST /organizations/{organizationId}/users`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| organizationId | string (UUID) | Yes | Organization ID |

**Request Body:**
```json
{
  "email": "string (required, unique)",
  "first_name": "string (required)",
  "last_name": "string (required)",
  "password": "string (required, min 8 chars)",
  "phone": "string (optional)",
  "date_of_birth": "string (ISO 8601 date, optional)",
  "identification": "string (optional)",
  "nationality": "string (optional)",
  "role": "string (optional, default: 'member')",
  "department_id": "string (UUID, optional)",
  "language": "string (optional, default: 'en')",
  "timezone": "string (optional, default: 'UTC')",
  "avatar": "string (URL, optional)",
  "status": "string (optional, default: 'ACTIVE')",
  "is_active": "boolean (optional, default: true)"
}
```

**Example Request:**
```json
{
  "email": "jane.smith@company.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "password": "SecurePass123!",
  "phone": "+1 809 987 6543",
  "date_of_birth": "1992-08-20",
  "identification": "001-9876543-2",
  "nationality": "American",
  "role": "member",
  "department_id": "dept-456",
  "language": "es",
  "timezone": "America/New_York",
  "is_active": true
}
```

**Response:** `201 Created`
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "email": "jane.smith@company.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "avatar": null,
    "phone": "+1 809 987 6543",
    "date_of_birth": "1992-08-20",
    "identification": "001-9876543-2",
    "nationality": "American",
    "role": "member",
    "department_id": "dept-456",
    "department": "Sales",
    "language": "es",
    "timezone": "America/New_York",
    "status": "ACTIVE",
    "is_active": true,
    "created_at": "2024-02-04T12:00:00Z",
    "updated_at": null
  }
}
```

**Error Responses:**
- `400 Bad Request` - Validation error
- `409 Conflict` - Email already exists

---

### 4. Update User

Update an existing user's information.

**Endpoint:** `PUT /users/{userId}` or `PATCH /users/{userId}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | string (UUID) | Yes | User ID |

**Request Body (all fields optional):**
```json
{
  "first_name": "string",
  "last_name": "string",
  "phone": "string",
  "date_of_birth": "string (ISO 8601 date)",
  "identification": "string",
  "nationality": "string",
  "role": "string",
  "department_id": "string (UUID)",
  "language": "string",
  "timezone": "string",
  "avatar": "string (URL)",
  "status": "string",
  "is_active": "boolean"
}
```

**Note:** The `email` field should NOT be updatable through this endpoint for security reasons.

**Response:** `200 OK`
```json
{
  "data": {
    // Updated user object
  }
}
```

**Error Responses:**
- `400 Bad Request` - Validation error
- `404 Not Found` - User not found

---

### 5. Delete User

Permanently delete a user from the organization.

**Endpoint:** `DELETE /users/{userId}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | string (UUID) | Yes | User ID |

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found` - User not found
- `403 Forbidden` - Cannot delete owner or self

---

### 6. Activate User

Activate a deactivated user.

**Endpoint:** `POST /users/{userId}/activate`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | string (UUID) | Yes | User ID |

**Response:** `200 OK`
```json
{
  "data": {
    // Updated user object with is_active: true, status: "ACTIVE"
  }
}
```

---

### 7. Deactivate User

Deactivate an active user (soft delete).

**Endpoint:** `POST /users/{userId}/deactivate`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | string (UUID) | Yes | User ID |

**Response:** `200 OK`
```json
{
  "data": {
    // Updated user object with is_active: false, status: "INACTIVE"
  }
}
```

---

### 8. Update User Avatar

Upload or update a user's avatar image.

**Endpoint:** `PUT /users/{userId}/avatar`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | string (UUID) | Yes | User ID |

**Request Body (Option A - URL):**
```json
{
  "avatar_url": "string (URL)"
}
```

**Request Body (Option B - File Upload):**
- Content-Type: `multipart/form-data`
- Field name: `avatar`
- Accepted formats: JPEG, PNG, WebP
- Max size: 5MB

**Response:** `200 OK`
```json
{
  "data": {
    // Updated user object with new avatar URL
  }
}
```

---

### 9. Get Current User (Me)

Retrieve the currently authenticated user's profile.

**Endpoint:** `GET /users/me`

**Response:** `200 OK`
```json
{
  "data": {
    // Current user object
  }
}
```

---

### 10. Update Current User (Me)

Update the currently authenticated user's own profile.

**Endpoint:** `PUT /users/me` or `PATCH /users/me`

**Request Body (limited fields):**
```json
{
  "first_name": "string",
  "last_name": "string",
  "phone": "string",
  "date_of_birth": "string (ISO 8601 date)",
  "language": "string",
  "timezone": "string",
  "avatar": "string (URL)"
}
```

**Note:** Users cannot change their own role, department, or status through this endpoint.

**Response:** `200 OK`
```json
{
  "data": {
    // Updated current user object
  }
}
```

---

### 11. Change Password

Change the current user's password.

**Endpoint:** `POST /users/me/change-password`

**Request Body:**
```json
{
  "current_password": "string (required)",
  "new_password": "string (required, min 8 chars)",
  "confirm_password": "string (required, must match new_password)"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Validation error or passwords don't match
- `401 Unauthorized` - Current password is incorrect

---

### 12. Reset Password (Admin)

Send a password reset link to a user (admin action).

**Endpoint:** `POST /users/{userId}/reset-password`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | string (UUID) | Yes | User ID |

**Response:** `200 OK`
```json
{
  "message": "Password reset email sent successfully"
}
```

---

### 13. Invite User

Send an invitation email to a new user.

**Endpoint:** `POST /organizations/{organizationId}/users/invite`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| organizationId | string (UUID) | Yes | Organization ID |

**Request Body:**
```json
{
  "email": "string (required)",
  "first_name": "string (required)",
  "last_name": "string (required)",
  "role": "string (optional, default: 'member')",
  "department_id": "string (UUID, optional)"
}
```

**Response:** `201 Created`
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "email": "invited.user@company.com",
    "first_name": "Invited",
    "last_name": "User",
    "status": "PENDING",
    "is_active": false,
    "created_at": "2024-02-04T12:00:00Z"
    // ... other fields will be null/default until user completes registration
  }
}
```

---

### 14. Resend Invitation

Resend invitation email to a pending user.

**Endpoint:** `POST /users/{userId}/resend-invitation`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | string (UUID) | Yes | User ID (must have status: "PENDING") |

**Response:** `200 OK`
```json
{
  "message": "Invitation resent successfully"
}
```

---

### 15. Cancel Invitation

Cancel a pending user invitation.

**Endpoint:** `DELETE /users/{userId}/invitation`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | string (UUID) | Yes | User ID (must have status: "PENDING") |

**Response:** `204 No Content`

---

## Validation Rules

### Email
- Must be a valid email format
- Must be unique within the system
- Max length: 255 characters

### Password
- Minimum 8 characters
- Should contain at least: 1 uppercase, 1 lowercase, 1 number (recommended)

### Names (first_name, last_name)
- Required
- Min length: 1 character
- Max length: 100 characters

### Phone
- Optional
- Should accept international format with country code

### Date of Birth
- Optional
- Must be a valid date in the past
- Format: ISO 8601 (YYYY-MM-DD)

### Language
- Must be one of: 'en', 'es', 'fr', 'pt'

### Timezone
- Must be a valid IANA timezone identifier
- Examples: 'UTC', 'America/Santo_Domingo', 'America/New_York', 'Europe/Madrid'

### Status
- Must be one of: 'ACTIVE', 'PENDING', 'INACTIVE'

### Role
- Must be one of: 'owner', 'admin', 'member'

---

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Request successful, no content to return |
| 400 | Bad Request - Validation error |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Semantic error |
| 500 | Internal Server Error |

---

## Authorization Rules

| Action | Owner | Admin | Member |
|--------|-------|-------|--------|
| List users | ✅ | ✅ | ✅ (limited) |
| View user | ✅ | ✅ | ✅ (own) |
| Create user | ✅ | ✅ | ❌ |
| Update user | ✅ | ✅ | ❌ |
| Delete user | ✅ | ✅ | ❌ |
| Activate user | ✅ | ✅ | ❌ |
| Deactivate user | ✅ | ✅ | ❌ |
| Update own profile | ✅ | ✅ | ✅ |
| Change own password | ✅ | ✅ | ✅ |
| Reset other's password | ✅ | ✅ | ❌ |
| Invite user | ✅ | ✅ | ❌ |
| Change roles | ✅ | ❌ | ❌ |

---

## Notes for Implementation

1. **Soft Delete**: The `deactivate` endpoint should be used instead of hard delete for most cases. The `delete` endpoint should only be used for removing pending invitations or GDPR compliance.

2. **Email Notifications**: The following actions should trigger email notifications:
   - User creation (welcome email)
   - User invitation
   - Password reset
   - Account activation/deactivation

3. **Audit Logging**: All user management actions should be logged for audit purposes with:
   - Action type
   - Actor (who performed the action)
   - Target user
   - Timestamp
   - IP address

4. **Rate Limiting**: Implement rate limiting especially for:
   - Password change attempts
   - Password reset requests
   - Invitation emails

5. **Organization Scope**: All user queries should be scoped to the user's organization. Users should not be able to access users from other organizations.
