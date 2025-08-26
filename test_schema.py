# test_schema.py
from cdp_protocol.schema_handler import Schema

print("--- Testing Valid Schema ---")
try:
    schema = Schema('schemas/user_v1.json')
    print(f"Field for grade 2: {schema.get_field_by_grade(2)}")
    print(f"Field for name 'user_id': {schema.get_field_by_name('user_id')}")
except ValueError as e:
    print(f"ERROR: {e}")

print("\n--- Testing Invalid Schema (Duplicate Grade) ---")
# Create a bad schema in memory for testing
import json
with open('schemas/bad_schema.json', 'w') as f:
    json.dump({
        "fields": [
            { "name": "field_a", "type": "uint64", "grade": 1 },
            { "name": "field_b", "type": "bool", "grade": 1 }
        ]
    }, f)

try:
    Schema('schemas/bad_schema.json')
except ValueError as e:
    print(f"SUCCESSFULLY CAUGHT ERROR: {e}")