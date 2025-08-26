# test_encoder.py
from cdp_protocol.schema_handler import Schema
from cdp_protocol.structured_encoder import StructuredEncoder

# 1. Load the schema we created earlier
try:
    schema = Schema('schemas/user_v1.json')
except Exception as e:
    print(f"Failed to load schema: {e}")
    exit()

# 2. Create a sample data object that matches the schema
sample_user_data = {
    "user_id": 1234567890123456789,
    "email": "test@example.com",
    "reputation_score": 0.85
}

# 3. Initialize the encoder and encode the data
print("Initializing StructuredEncoder...")
encoder = StructuredEncoder()

print("Encoding sample data...")
try:
    final_payload = encoder.encode(sample_user_data, schema)
    print("✅ Encoding process completed successfully.")
    print(f"Final compressed payload size: {len(final_payload)} bytes")
    
    # Save the output for the next step (the decoder)
    with open('user_v1.cdp', 'wb') as f:
        f.write(final_payload)
    print("Saved encoded data to 'user_v1.cdp'")

except Exception as e:
    print(f"❌ ERROR during encoding: {e}")