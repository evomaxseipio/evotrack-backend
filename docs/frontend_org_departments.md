# Organization Departments API Documentation

This document provides the necessary information for the frontend team to integrate the Organization Department features into the application.

## Overview

- **Base URL**: `/api/v1/organizations/{org_id}/departments`
- **Naming Convention**: `camelCase` (JSON response keys)
- **Authentication**: Bearer Token required for all endpoints.

## Responses Wrapper

All successful responses follow the `ApiResponse` structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Success message",
  "meta": { ... }
}
```

## Endpoints

### 1. Search Departments (Paginated)
Get all departments in an organization with advanced filters using cursor-based pagination.

- **URL**: `POST /organizations/{orgId}/departments/search`
- **Request Body**:
  ```json
  {
    "limit": 20,
    "nextCursor": {
      "id": "uuid",
      "ts": "iso_datetime"
    },
    "search": "string",
    "includeInactive": false
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "uuid",
        "name": "Human Resources",
        "description": "HR Department",
        "budget": 50000.00,
        "isActive": true,
        "createdAt": "2024-02-05T10:00:00Z",
        "updatedAt": "2024-02-05T10:00:00Z",
        "parentDepartmentId": null,
        "parentDepartmentName": null,
        "departmentHeadId": "uuid",
        "departmentHeadName": "John Doe",
        "departmentHeadAvatar": "https://...",
        "employeeCount": 15,
        "meta": {}
      }
    ],
    "stats": {
      "totalDepartments": 10,
      "activeDepartments": 8,
      "inactiveDepartments": 2,
      "rootDepartments": 2
    },
    "pagination": {
      "count": 1,
      "limit": 20,
      "hasMore": false,
      "nextCursor": null
    },
    "meta": {
      "userRole": "admin",
      "organizationId": "uuid"
    }
  }
  ```

### 2. Get Department Tree
Get all departments for an organization in a hierarchical tree format.

- **URL**: `GET /organizations/{orgId}/departments`
- **Query Parameters**:
  - `isActive`: (bool, optional) Filter by active status
  - `search`: (string, optional) Search in name/description
- **Success Response (200 OK)**:
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "uuid",
        "name": "Engineering",
        "subDepartments": [
          {
            "id": "uuid",
            "name": "Backend",
            "userCount": 5,
            "teamCount": 1,
            "subDepartments": []
          }
        ],
        "userCount": 10,
        "teamCount": 2
      }
    ],
    "stats": { ... },
    "message": "Departments retrieved successfully"
  }
  ```

### 3. Create Department

- **URL**: `POST /organizations/{orgId}/departments`
- **Request Body**:

  ```json
  {
    "name": "New Department",
    "description": "Optional description",
    "parentDepartmentId": "uuid",
    "departmentHeadId": "uuid",
    "budget": 1000.00
  }
  ```

### 4. Get Department Details
- **URL**: `GET /organizations/{orgId}/departments/{deptId}`
- **Success Response**: Detailed object including `teams`, `users`, and `parentDepartment`.

### 5. Update Department
- **URL**: `PUT /organizations/{orgId}/departments/{deptId}`
- **Request Body**: Partial update supported.

### 6. Delete Department (Soft Delete)
- **URL**: `DELETE /organizations/{orgId}/departments/{deptId}`

### 7. Assign User to Department
- **URL**: `PUT /organizations/{orgId}/departments/users/{userId}`
- **Request Body**:
  ```json
  {
    "departmentId": "uuid"
  }
  ```

## Important Notes
- **soft delete**: All deletions are soft deletes unless otherwise specified.
- **camelCase**: The backend expects input in `snake_case` but returns `camelCase`. However, models configured with `alias_generator` in Pydantic will accept `camelCase` in requests as well.
- **Hierarchy**: Use the tree response for navigation and the search response for lists/tables.
