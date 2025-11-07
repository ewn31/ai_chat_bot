# Quick Reference: Counsellor API Endpoints

## Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/counsellors` | List all counsellors |
| GET | `/api/counsellors/{username}` | Get specific counsellor |
| POST | `/api/counsellors` | Create new counsellor |
| PUT/PATCH | `/api/counsellors/{username}` | Update counsellor |
| DELETE | `/api/counsellors/{username}` | Delete counsellor |
| POST | `/api/counsellors/{username}/channels` | Add channel to counsellor |

## Quick Examples

### Create Counsellor
```bash
curl -X POST http://localhost:5000/api/counsellors \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "name": "Alice"}'
```

### Get All Counsellors
```bash
curl http://localhost:5000/api/counsellors
```

### Update Counsellor
```bash
curl -X PUT http://localhost:5000/api/counsellors/alice \
  -H "Content-Type: application/json" \
  -d '{"phone": "237612345678"}'
```

### Delete Counsellor
```bash
curl -X DELETE http://localhost:5000/api/counsellors/alice
```

## Testing
```bash
# Start server
python index.py

# Run tests (in another terminal)
python tests/test_counsellor_api.py
```

For full documentation, see: [docs/counsellor_api.md](counsellor_api.md)
