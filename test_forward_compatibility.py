# test_forward_compatibility.py
import os
from cdp_protocol.schema_handler import Schema
from cdp_protocol.structured_encoder import StructuredEncoder
from cdp_protocol.structured_decoder import StructuredDecoder

print("--- PHASE 2: FORWARD COMPATIBILITY TEST ---")
print("="*45)
print("Goal: Prove a v1 decoder can read v2 data without errors.")
print("="*45)

# --- SETUP ---
V1_SCHEMA_PATH = 'schemas/user_v1.json'
V2_SCHEMA_PATH = 'schemas/user_v2.json'
OUTPUT_FILE = 'user_v2.cdp'

# 1. Load both schemas
print("\n[Step 1] Loading schemas...")
try:
    schema_v1 = Schema(V1_SCHEMA_PATH)
    schema_v2 = Schema(V2_SCHEMA_PATH)
    print("✅ Schemas loaded successfully.")
except Exception as e:
    print(f"❌ ERROR: Failed to load schemas: {e}")
    exit()

# 2. Create a complete data object matching the NEW (v2) schema
user_data_v2 = {
    "user_id": 987654321098765432,
    "email": "future_user@example.com",
    "reputation_score": 0.99,
    "is_active": True
}
print(f"\n[Step 2] Created sample v2 data object:\n{user_data_v2}")

# 3. Encode the v2 data using the v2 schema
print("\n[Step 3] Encoding v2 data with v2 schema...")
try:
    encoder = StructuredEncoder()
    cdp_payload_v2 = encoder.encode(user_data_v2, schema_v2)
    with open(OUTPUT_FILE, 'wb') as f:
        f.write(cdp_payload_v2)
    print(f"✅ Data encoded successfully to '{OUTPUT_FILE}' ({len(cdp_payload_v2)} bytes).")
except Exception as e:
    print(f"❌ ERROR: Failed during encoding: {e}")
    exit()

# --- THE EXPERIMENT ---
# 4. An OLD application (v1 decoder) now receives the NEW data (v2 payload).
#    It only knows about the v1 schema.
print("\n[Step 4] Simulating a v1 decoder reading the v2 data...")
try:
    # The decoder itself doesn't need a schema to decompress, only for projection
    decoder_for_v1_app = StructuredDecoder(cdp_payload_v2)
    
    # The v1 application asks for the fields it knows (grades 1 and 2)
    grades_v1_app_knows = [1, 2]
    print(f"  v1 decoder will project grades: {grades_v1_app_knows}")
    
    extracted_data = decoder_for_v1_app.project(schema_v1, grades_v1_app_knows)
    
    print("\n[Step 5] Analyzing the result...")
    print(f"  Data extracted by v1 decoder:\n{extracted_data}")

    # --- VERIFICATION ---
    # Did it crash? No, because we got here.
    print("\n✅ TEST PASSED: Decoder did not crash on unknown grades.")
    
    # Does the extracted data contain ONLY the v1 fields?
    expected_keys = {'user_id', 'email'}
    extracted_keys = set(extracted_data.keys())
    assert expected_keys == extracted_keys
    print("✅ TEST PASSED: Extracted data contains exactly the expected v1 fields.")
    
    # Is the data correct?
    assert extracted_data['user_id'] == user_data_v2['user_id']
    assert extracted_data['email'] == user_data_v2['email']
    print("✅ TEST PASSED: Extracted v1 data is correct.")

    print("\n" + "="*45)
    print("🎉 SUCCESS: Forward compatibility has been verified! 🎉")
    print("="*45)

except Exception as e:
    print(f"\n❌ TEST FAILED: An unexpected error occurred: {e}")

finally:
    # Clean up the test file
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        print(f"\nCleanup: Removed '{OUTPUT_FILE}'.")