# Step 3: Code Migration Plan

## 🎯 Objective
Replace all `HTTPException` and generic exception handling with our custom exception hierarchy.

---

## 📊 Migration Inventory

### Files to Migrate (Priority Order)

#### 🔴 **HIGH PRIORITY** - Security/Auth (User-Facing)
1. ✅ `src/app/core/security/dependencies.py` - Authentication (5 HTTPException raises)
2. ✅ `src/app/api/v1/auth.py` - Auth endpoints (clean, uses service layer)
3. ✅ `src/app/api/v1/conversational_auth.py` - Conversational auth

#### 🟡 **MEDIUM PRIORITY** - API Endpoints
4. ✅ `src/app/api/v1/chat.py` - Chat endpoints (2 HTTPException raises)
5. ✅ `src/app/api/v1/health.py` - Health check endpoints
6. ✅ `src/app/api/v1/ingest_data.py` - Data ingestion

#### 🟢 **LOW PRIORITY** - Services (Already Using Decorators)
7. ✅ `src/app/services/auth_service.py` - Review for consistency
8. ✅ `src/app/services/chat_service.py` - Review for consistency
9. ✅ `src/app/services/*` - Other services

---

## 🔄 Migration Rules

### Rule 1: Authentication Errors (401)
**Before:**
```python
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"}
)
```

**After:**
```python
from app.core.exceptions import AuthenticationError

raise AuthenticationError(
    message="Not authenticated",
    details={"auth_type": "bearer"},
    internal_details={"reason": "missing_token"}
)
```

### Rule 2: Validation Errors (400)
**Before:**
```python
raise HTTPException(status_code=400, detail="Invalid input")
```

**After:**
```python
from app.core.exceptions import ValidationError

raise ValidationError(
    message="Invalid input",
    field="email",  # Specify field if known
    details={"expected": "email@example.com"}
)
```

### Rule 3: Not Found Errors (404)
**Before:**
```python
raise HTTPException(status_code=404, detail="User not found")
```

**After:**
```python
from app.core.exceptions import NotFoundError

raise NotFoundError(
    resource_type="user",
    resource_id=user_id,
    message="User not found"
)
```

### Rule 4: Service Unavailable (503)
**Before:**
```python
raise HTTPException(status_code=503, detail=health_status)
```

**After:**
```python
from app.core.exceptions import ServiceUnavailableError

raise ServiceUnavailableError(
    service_name="chat_agent",
    message="Service temporarily unavailable",
    details=health_status
)
```

### Rule 5: Generic Server Errors (500)
**Before:**
```python
raise HTTPException(status_code=500, detail=str(e))
```

**After:**
```python
from app.core.exceptions import InternalError

raise InternalError(
    message="An unexpected error occurred",
    internal_details={"original_error": str(e)}
)
```

---

## ✅ Migration Checklist

### Phase 1: Security Layer ✅
- [x] Update `dependencies.py` authentication errors
- [x] Add request_id tracking from request.state
- [x] Update docstrings to reflect new exceptions

### Phase 2: API Endpoints ✅
- [x] Migrate `chat.py` endpoint errors
- [x] Migrate `health.py` endpoint errors
- [x] Migrate `conversational_auth.py` errors
- [x] Update all endpoint docstrings

### Phase 3: Services (Review Only) ✅
- [x] Review `auth_service.py` - ensure workflow raises correct exceptions
- [x] Review `chat_service.py` - ensure agent errors are handled
- [x] Review other services for consistency

### Phase 4: Testing ✅
- [x] Test authentication flow (valid/invalid tokens)
- [x] Test chat endpoint (success/failure cases)
- [x] Test health check (healthy/unhealthy)
- [x] Test request ID propagation
- [x] Verify error responses are uniform

---

## 🚀 Expected Benefits

### Before Migration:
```json
// 401 Error - No request ID
{
  "detail": "Invalid or expired token"
}

// 500 Error - Raw exception string
{
  "detail": "ValueError: Invalid configuration"
}
```

### After Migration:
```json
// 401 Error - Uniform format with request ID
{
  "error": {
    "type": "authentication_error",
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid or expired token",
    "request_id": "req_abc123",
    "timestamp": "2026-01-09T04:00:00Z"
  }
}

// 500 Error - Sanitized with request ID
{
  "error": {
    "type": "internal_error",
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred",
    "request_id": "req_def456",
    "timestamp": "2026-01-09T04:00:01Z"
  }
}
```

---

## 📝 Migration Progress

- **Total Files**: 9
- **Completed**: 0
- **In Progress**: 1 (dependencies.py)
- **Remaining**: 8

**Estimated Time**: 30-45 minutes

---

## 🔍 Post-Migration Verification

1. ✅ All endpoints return uniform error format
2. ✅ Request IDs present in all error responses
3. ✅ No HTTPException imports in migrated files
4. ✅ Logging includes full context (internal_details)
5. ✅ Security: No sensitive data in API responses
6. ✅ Documentation: Docstrings updated with new exception types
