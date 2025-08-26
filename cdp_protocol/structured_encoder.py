# cdp_protocol/structured_encoder.py
import struct
from .schema_handler import Schema
from .cdp_protocol import CDPEncoder

class StructuredEncoder:
    """
    Encodes a Python dictionary into a structured byte stream according to a schema.
    This class handles the logic of serializing individual fields and then uses the
    main CDPEncoder to compress and finalize the stream.
    """

    def __init__(self):
        # We will use the existing CDPEncoder for the final compression stage.
        self.cdp_encoder = CDPEncoder()

    def _serialize_field(self, field_definition: dict, value: any) -> bytes:
        """
        Serializes a single Python value into bytes based on its type definition.
        
        Args:
            field_definition: The schema dictionary for the field.
            value: The Python value to serialize.

        Returns:
            The serialized value as bytes.
        """
        field_type = field_definition['type']

        if field_type == 'uint64':
            # 'Q' is the format character for unsigned long long (8 bytes)
            return struct.pack('!Q', value)
        elif field_type == 'float32':
            # 'f' is the format character for a float (4 bytes)
            return struct.pack('!f', value)
        elif field_type == 'bool':
            # '?' is the format character for a boolean (1 byte)
            return struct.pack('!?', value)
        elif field_type == 'string_utf8':
            return value.encode('utf-8')
        elif field_type == 'uint8':
            # 'B' is the format character for an unsigned char (1 byte)
            return struct.pack('!B', value)
        elif field_type == 'float32':
            # 'f' is the format character for a float (4 bytes)
            return struct.pack('!f', value)
        else:
            # This should ideally not be reached if the schema is validated.
            raise TypeError(f"Unsupported serialization type: {field_type}")

    def encode(self, data_object: dict, schema: Schema) -> bytes:
        """
        Takes a data dictionary and a schema, produces the final, compressed
        CDP byte stream.

        Args:
            data_object: The Python dictionary containing the data.
            schema: The loaded Schema object for this data.

        Returns:
            The final, compressed and verifiable CDP payload as bytes.
        """
        interleaved_parts = []

        # Iterate through the fields DEFINED IN THE SCHEMA to ensure order
        # and completeness.
        for field_def in schema.fields:
            field_name = field_def['name']
            
            # Check if the data object contains the required field
            if field_name not in data_object:
                raise ValueError(f"Missing field in data object: '{field_name}'")

            value = data_object[field_name]
            grade = field_def['grade']

            # 1. Serialize the field's value into its byte payload
            payload_bytes = self._serialize_field(field_def, value)
            
            # 2. Create the header: (grade: 1 byte) + (payload_length: 4 bytes)
            #    Using network byte order '!' for consistency.
            #    'B' is unsigned char (1 byte), 'I' is unsigned int (4 bytes).
            header = struct.pack('!BI', grade, len(payload_bytes))
            
            # 3. Append the full part (header + payload) to our list
            interleaved_parts.append(header + payload_bytes)

        # 4. Concatenate all parts into a single uncompressed stream
        uncompressed_stream = b''.join(interleaved_parts)
        
        # 5. Use the existing CDPEncoder to compress and add integrity layers
        final_cdp_payload = self.cdp_encoder.encode(uncompressed_stream)

        return final_cdp_payload