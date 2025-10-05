# Error Handling Standards for Server Functions

## Overview

This document defines the standard error handling patterns for all server-side API functions in the codebase.

## Core Principles

1. **User feedback comes from the UI layer** - Server functions focus on data retrieval/mutation
2. **Consistent patterns** - Similar operations should handle errors the same way
3. **Graceful degradation** - Read operations should fail gracefully with empty data
4. **Clear failure signals** - Write operations should throw errors for the UI to catch

---

## Standard Patterns

### Pattern A: Read Operations (GET)

**Use for:** Fetching data, list operations, queries

```typescript
export async function getData(id: string): Promise<Data[]> {
    const result = await fetchApi<Data[]>(`/endpoint/${id}`);

    // Return empty array/null on failure - UI will show "no data" state
    if (!result) {
        return []; // or null for single items
    }

    return result;
}
```

**Why:**

-   Users can still use the app even if one data source fails
-   UI naturally shows "no data" or "empty" states
-   Errors are already logged by `fetchApi`

### Pattern B: Write Operations (POST/PUT/PATCH/DELETE)

**Use for:** Creating, updating, deleting data

```typescript
export async function createData(data: Data): Promise<Data> {
    const result = await fetchApi<Data>("/endpoint", {
        method: "POST",
        body: JSON.stringify(data),
    });

    // Throw error - UI will catch and show toast/error message
    if (!result) {
        throw new Error("Failed to create data");
    }

    return result;
}
```

**Why:**

-   Write operations are user-initiated actions that need feedback
-   UI layer can catch the error and show appropriate toast/modal
-   Clear signal that the operation failed

### Pattern C: Critical Read Operations

**Use for:** Data required for the page to function (rare)

```typescript
export async function getCriticalData(id: string): Promise<Data> {
    const result = await fetchApi<Data>(`/critical/${id}`);

    if (!result) {
        throw new Error("Failed to load required data");
    }

    return result;
}
```

**Why:**

-   Some data is essential for the page to work
-   UI can show error boundary or redirect

---

## Migration Guide

### ❌ Avoid Try-Catch in Server Functions

```typescript
// DON'T DO THIS - fetchApi already handles errors
try {
    const result = await fetchApi<T>(endpoint);
    return result || [];
} catch (error) {
    console.error(error);
    return [];
}
```

```typescript
// DO THIS - Let fetchApi handle errors, check result
const result = await fetchApi<T>(endpoint);
return result || [];
```

### UI Layer Responsibilities

The UI components should handle errors from write operations:

```typescript
// In React component
const handleCreate = async () => {
    try {
        await createData(formData);
        toast.success("Created successfully");
    } catch (error) {
        toast.error(error.message || "Failed to create");
    }
};
```

---

## Examples by Function Type

| Function Type        | Pattern | Return on Error | Example            |
| -------------------- | ------- | --------------- | ------------------ |
| `getProjects()`      | A       | `[]`            | List of projects   |
| `getOneProject()`    | A       | `null`          | Single project     |
| `createProject()`    | B       | `throw`         | Create new project |
| `updateProject()`    | B       | `throw`         | Update project     |
| `deleteProject()`    | B       | `void` (throws) | Delete project     |
| `getOrganizations()` | A       | `[]`            | List of orgs       |
| `getUserProfile()`   | C       | `throw`         | Required for auth  |

---

## Decision Tree

```
Is this a READ operation?
├─ Yes: Is the data critical for the page?
│   ├─ Yes: Use Pattern C (throw)
│   └─ No: Use Pattern A (return empty)
└─ No (WRITE operation): Use Pattern B (throw)
```
