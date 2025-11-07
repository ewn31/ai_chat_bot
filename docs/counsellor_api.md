# Counsellor CRUD API Documentation

RESTful API endpoints for managing counsellors in the chatbot system.

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### 1. Get All Counsellors
**GET** `/api/counsellors`

Retrieve a list of all counsellors with their details.

**Response:**
```json
{
  "success": true,
  "count": 2,
  "counsellors": [
    {
      "id": 1,
      "name": "Alice Smith",
      "username": "alice",
      "email": "alice@example.com",
      "phone": "237612345678",
      "channels": null,
      "current_ticket": null
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Server error

---

### 2. Get Specific Counsellor
**GET** `/api/counsellors/{username}`

Retrieve details of a specific counsellor by username.

**Parameters:**
- `username` (path): Counsellor's username

**Response:**
```json
{
  "success": true,
  "counsellor": {
    "id": 1,
    "name": "Alice Smith",
    "username": "alice",
    "email": "alice@example.com",
    "phone": "237612345678",
    "channels": null,
    "current_ticket": null
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Counsellor not found
- `500 Internal Server Error`: Server error

---

### 3. Create Counsellor
**POST** `/api/counsellors`

Create a new counsellor account with full integration.

**This endpoint performs multiple operations:**
1. Creates counsellor in local database
2. Adds WhatsApp channel (if provided)
3. Provisions account on chat app backend
4. Generates and sends magic link via WhatsApp/Email

**Request Body:**
```json
{
  "username": "alice",          // Required
  "email": "alice@example.com", // Required
  "name": "Alice Smith",        // Optional (defaults to username)
  "password": "secret123",      // Optional
  "phone": "237612345678",      // Optional
  "whatsapp": "237612345678"    // Optional (triggers WhatsApp channel setup)
}
```

**Response:**
```json
{
  "success": true,
  "message": "Counsellor \"alice\" created successfully",
  "counsellor": {
    "username": "alice",
    "email": "alice@example.com",
    "name": "Alice Smith",
    "whatsapp": "237612345678"
  }
}
```

**Status Codes:**
- `201 Created`: Successfully created
- `400 Bad Request`: Missing required fields
- `500 Internal Server Error`: Server error

**Note:** This endpoint uses the `counsellor_handler.create_counsellor()` function which handles the complete counsellor provisioning workflow including chat app integration.

---

### 4. Update Counsellor
**PUT** `/api/counsellors/{username}` or **PATCH** `/api/counsellors/{username}`

Update a counsellor's information.

**Parameters:**
- `username` (path): Counsellor's username

**Request Body:**
```json
{
  "name": "Alice Johnson",      // Optional
  "email": "alice.j@example.com", // Optional
  "phone": "237698765432",      // Optional
  "password": "newsecret456"    // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Counsellor \"alice\" updated successfully",
  "updated_fields": ["name", "email", "phone"]
}
```

**Status Codes:**
- `200 OK`: Successfully updated
- `400 Bad Request`: No valid fields to update
- `404 Not Found`: Counsellor not found
- `500 Internal Server Error`: Server error

---

### 5. Delete Counsellor
**DELETE** `/api/counsellors/{username}`

Delete a counsellor from the system.

**Parameters:**
- `username` (path): Counsellor's username

**Response:**
```json
{
  "success": true,
  "message": "Counsellor \"alice\" deleted successfully"
}
```

**Status Codes:**
- `200 OK`: Successfully deleted
- `404 Not Found`: Counsellor not found
- `500 Internal Server Error`: Server error

---

### 6. Add Channel to Counsellor
**POST** `/api/counsellors/{username}/channels`

Add a communication channel (e.g., WhatsApp) to a counsellor.

**Parameters:**
- `username` (path): Counsellor's username

**Request Body:**
```json
{
  "channel": "whatsapp",                      // Required
  "channel_id": "237612345678@s.whatsapp.net", // Required
  "auth_key": "abc123token",                  // Optional
  "order": 1                                  // Optional (priority order)
}
```

**Response:**
```json
{
  "success": true,
  "message": "Channel \"whatsapp\" added to counsellor \"alice\""
}
```

**Status Codes:**
- `201 Created`: Successfully added
- `400 Bad Request`: Missing required fields
- `404 Not Found`: Counsellor not found
- `500 Internal Server Error`: Server error

---

## Error Response Format

All error responses follow this format:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

---

## Usage Examples

### Using cURL

**Create a counsellor:**
```bash
curl -X POST http://localhost:5000/api/counsellors \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "name": "Alice Smith",
    "password": "secret123"
  }'
```

**Get all counsellors:**
```bash
curl http://localhost:5000/api/counsellors
```

**Get specific counsellor:**
```bash
curl http://localhost:5000/api/counsellors/alice
```

**Update counsellor:**
```bash
curl -X PUT http://localhost:5000/api/counsellors/alice \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson", "phone": "237698765432"}'
```

**Add channel:**
```bash
curl -X POST http://localhost:5000/api/counsellors/alice/channels \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "whatsapp",
    "channel_id": "237612345678@s.whatsapp.net",
    "auth_key": "token123"
  }'
```

**Delete counsellor:**
```bash
curl -X DELETE http://localhost:5000/api/counsellors/alice
```

### Using Python (requests library)

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Create counsellor
response = requests.post(f"{BASE_URL}/counsellors", json={
    "username": "alice",
    "email": "alice@example.com",
    "name": "Alice Smith"
})
print(response.json())

# Get all counsellors
response = requests.get(f"{BASE_URL}/counsellors")
print(response.json())

# Update counsellor
response = requests.put(f"{BASE_URL}/counsellors/alice", json={
    "phone": "237612345678"
})
print(response.json())

# Delete counsellor
response = requests.delete(f"{BASE_URL}/counsellors/alice")
print(response.json())
```

---

## Notes

1. **Authentication**: Currently, the API does not require authentication. Consider adding authentication middleware for production use.

2. **Password Security**: The password field is currently returned in GET responses. In production, passwords should:
   - Be hashed before storage
   - Never be returned in API responses
   - Be handled securely

3. **Validation**: Additional validation may be needed for:
   - Email format
   - Username uniqueness
   - Phone number format
   - Channel types

4. **Rate Limiting**: Consider implementing rate limiting for production use.

5. **Logging**: All operations are logged. Check logs for debugging and audit purposes.

---

## Testing

Run the automated test suite:

```bash
# Make sure the Flask server is running first
python index.py

# In another terminal, run tests
python tests/test_counsellor_api.py
```

The test script will:
- Create a test counsellor
- Retrieve counsellor details
- Update counsellor information
- Add a channel
- Delete the counsellor
- Test error handling
