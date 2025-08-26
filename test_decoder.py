# test_decoder.py
from cdp_protocol.schema_handler import Schema
from cdp_protocol.structured_decoder import StructuredDecoder

# 1. Load the schema
try:
    schema = Schema('schemas/user_v1.json')
except Exception as e:
    print(f"Failed to load schema: {e}")
    exit()

# 2. Load the encoded data from the file
try:
    with open('user_v1.cdp', 'rb') as f:
        cdp_payload = f.read()
    print(f"Loaded {len(cdp_payload)} bytes from 'user_v1.cdp'.")
except FileNotFoundError:
    print("ERROR: 'user_v1.cdp' not found. Please run test_encoder.py first.")
    exit()

# 3. Initialize the decoder
try:
    print("\nInitializing StructuredDecoder...")
    decoder = StructuredDecoder(cdp_payload)
except Exception as e:
    print(f"❌ ERROR during decoding: {e}")
    exit()

# 4. Perform projections to test selective extraction
print("\n--- Running Projections ---")

# Test 1: Extract only the user_id (grade 1)
print("\nProjecting grade 1 (user_id)...")
data_p1 = decoder.project(schema, grades_to_extract=[1])
print(f"  Result: {data_p1}")
assert 'user_id' in data_p1 and 'email' not in data_p1

# Test 2: Extract email and reputation (grades 2 and 3)
print("\nProjecting grades 2 & 3 (email, reputation_score)...")
data_p2 = decoder.project(schema, grades_to_extract=[2, 3])
print(f"  Result: {data_p2}")
assert 'email' in data_p2 and 'reputation_score' in data_p2 and 'user_id' not in data_p2

# Test 3: Extract all known fields
print("\nProjecting all grades (1, 2, 3)...")
data_p3 = decoder.project(schema, grades_to_extract=[1, 2, 3])
print(f"  Result: {data_p3}")
assert 'user_id' in data_p3 and 'email' in data_p3 and 'reputation_score' in data_p3

print("\n✅ All projection tests passed successfully!")