# cdp_protocol/structured_decoder.py
import struct
from .schema_handler import Schema
from .cdp_protocol import CDPDecoder

class StructuredDecoder:
    """
    Decodes a CDP payload and allows for projecting out specific fields
    based on their grades, demonstrating the "schema-on-the-wire" capability.
    """

    def __init__(self, cdp_payload: bytes):
        """
        Initializes the decoder by decompressing and verifying the entire payload.
        
        Args:
            cdp_payload: The full, compressed CDP byte stream.
        """
        # Use the existing CDPDecoder to handle decompression and integrity checks
        cdp_decoder = CDPDecoder()
        try:
            # The result is the raw, grade-interleaved byte stream
            self.uncompressed_stream = cdp_decoder.decode(cdp_payload)
            print("CDP payload decompressed and verified successfully.")
        except ValueError as e:
            # This will catch checksum or hash failures from the underlying decoder
            raise ValueError(f"CDP payload is invalid or corrupt: {e}")
        
        self.stream_length = len(self.uncompressed_stream)

    def _deserialize_field(self, field_definition: dict, payload: bytes) -> any:
        """
        Deserializes a byte payload back into a Python value.
        """
        field_type = field_definition['type']
        
        if field_type == 'uint64':
            return struct.unpack('!Q', payload)[0]
        elif field_type == 'float32':
            return struct.unpack('!f', payload)[0]
        elif field_type == 'bool':
            return struct.unpack('!?', payload)[0]
        elif field_type == 'string_utf8':
            return payload.decode('utf-8')
        else:
            raise TypeError(f"Unsupported deserialization type: {field_type}")

    def project(self, schema: Schema, grades_to_extract: list[int]) -> dict:
        """
        Reads the uncompressed stream and extracts only the data for the
        specified grades. This is the core of grade-orthogonality.

        Args:
            schema: The Schema object to interpret the data.
            grades_to_extract: A list of integer grades to extract.

        Returns:
            A dictionary containing the data for the extracted fields.
        """
        extracted_data = {}
        position = 0
        
        # Convert to a set for fast lookups
        grades_set = set(grades_to_extract)

        while position < self.stream_length:
            # 1. Read the header: (grade: 1 byte) + (payload_length: 4 bytes)
            header_format = '!BI'
            header_size = struct.calcsize(header_format)
            
            if position + header_size > self.stream_length:
                raise ValueError("Malformed stream: incomplete header.")

            grade, payload_len = struct.unpack(header_format, self.uncompressed_stream[position : position + header_size])
            position += header_size
            
            payload_end = position + payload_len
            if payload_end > self.stream_length:
                raise ValueError("Malformed stream: payload length exceeds stream size.")

            # 2. Check if this grade is one we want to extract
            if grade in grades_set:
                # Get the field definition from the schema using the grade
                field_def = schema.get_field_by_grade(grade)
                if not field_def:
                    # This case happens if the decoder's schema is older and
                    # doesn't know about this grade. We simply ignore it.
                    print(f"Warning: Data found for unknown grade {grade}. Skipping.")
                else:
                    # Read the payload
                    payload = self.uncompressed_stream[position : payload_end]
                    
                    # Deserialize it
                    value = self._deserialize_field(field_def, payload)
                    
                    # Add to our results dictionary
                    extracted_data[field_def['name']] = value
            
            # 3. Move the position marker to the start of the next field,
            #    regardless of whether we extracted the data or not.
            position = payload_end
            
        return extracted_data