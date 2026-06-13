import httpx

base = 'http://localhost:8080'
email = 'trash-check-test@example.com'
password = '12345678'

# Register
r = httpx.post(f'{base}/api/auth/register', json={'email': email, 'password': password})
print(f'Register: {r.status_code}')
if r.status_code == 201:
    token = r.json()['access_token']
elif r.status_code == 409:
    r = httpx.post(f'{base}/api/auth/login', json={'email': email, 'password': password})
    token = r.json()['access_token']
else:
    print(r.text[:300])
    exit(1)

h = {'Authorization': f'Bearer {token}'}

# Upload a file to ROOT
import io
files = {'file': ('root_file.txt', io.BytesIO(b'hello from root'), 'text/plain')}
r = httpx.post(f'{base}/api/files/upload', headers=h, files=files)
print(f'Upload to root: {r.status_code}')
if r.status_code == 201:
    file_id = r.json()['id']
    print(f'  File ID: {file_id}')
    
    # Delete it (move to trash)
    r = httpx.delete(f'{base}/api/files/{file_id}', headers=h)
    print(f'Delete: {r.status_code} {r.text[:200]}')
    
    # Check trash
    r = httpx.get(f'{base}/api/trash/', headers=h)
    print(f'Trash: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        items = data if isinstance(data, list) else data.get('items', [])
        print(f'  Items: {len(items)}')
        for item in items:
            print(f'    - {item["name"]} kind={item["kind"]} original_parent_id={item.get("original_parent_id")} deleted_at={item.get("deleted_at")}')

# Also check existing trash
r = httpx.get(f'{base}/api/trash/', headers=h)
data = r.json()
items = data if isinstance(data, list) else data.get('items', [])
print(f'\nAll trash items: {len(items)}')
for item in items:
    print(f'  - {item["name"]} kind={item["kind"]} parent={item.get("original_parent_id")} deleted={item.get("deleted_at")}')
