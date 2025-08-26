# cdp_protocol.py
"""
Contains the core implementation of the Coherent Data Protocol (CDP)
encoder and decoder. V9: Numba-optimized for performance.
"""
import zstandard as zstd
import numpy as np
from gmpy2 import mpfr
import struct
from numba import jit # <-- Import Numba's JIT compiler

from .map_loader import resonance_map
from .core_math import calculate_resonance
from .constants import ALPHA_CONSTANTS, SP_PRIME_P

# --- V9 Binary Format (Version Bump for Optimization Change) ---
MAIN_HEADER_FORMAT = "! 4s B B Q I I"
MAIN_HEADER_SIZE = struct.calcsize(MAIN_HEADER_FORMAT)
CDP_MAGIC = b'CDP9'

CHECKSUM_FORMAT = "! d"
CHECKSUM_SIZE = struct.calcsize(CHECKSUM_FORMAT)


# ---!!!!!! START OF NUMBA OPTIMIZATION !!!!!! ---

# Prepare data for Numba: Convert complex objects to simple NumPy arrays.
# We do this once when the module is loaded.
BYTE_TO_CLASS_ID = np.array([resonance_map.get_class_info(i)['class_id'] for i in range(256)], dtype=np.uint8)
BYTE_TO_INDEX = np.array([resonance_map.get_class_info(i)['index'] for i in range(256)], dtype=np.uint8)

# Convert high-precision constants to standard float64 for Numba.
ALPHA_CONSTANTS_F64 = np.array([float(ALPHA_CONSTANTS[i]) for i in range(8)], dtype=np.float64)
RESONANCE_VALUES_F64 = np.array([float(calculate_resonance(i)) for i in range(256)], dtype=np.float64)

@jit(nopython=True, fastmath=True)
def _resonance_transform_jit(data_np: np.ndarray, 
                             class_ids_out: np.ndarray, 
                             indices_out: np.ndarray,
                             byte_to_class_map: np.ndarray,
                             byte_to_index_map: np.ndarray):
    """A Numba-JIT compiled function to accelerate the resonance transform."""
    for i in range(data_np.shape[0]):
        byte_val = data_np[i]
        class_ids_out[i] = byte_to_class_map[byte_val]
        indices_out[i] = byte_to_index_map[byte_val]

@jit(nopython=True, fastmath=True)
def _calculate_stream_hash_jit(data_np: np.ndarray,
                               resonance_values_map: np.ndarray,
                               alpha_values_map: np.ndarray,
                               sp_prime: int) -> int:
    """A Numba-JIT compiled function to accelerate the stream hash calculation."""
    total_hash = 0.0 # Use a standard float for Numba
    for i in range(data_np.shape[0]):
        byte_val = data_np[i]
        r_val = resonance_values_map[byte_val]
        alpha_val = alpha_values_map[i % 8]
        total_hash += r_val * alpha_val
    
    # Modulo must be done on an integer
    return int(total_hash) % sp_prime

# ---!!!!!! END OF NUMBA OPTIMIZATION !!!!!! ---


class CDPEncoder:
    """Encapsulates the logic for the final V9 (Numba-optimized) CDP format."""
    
    def __init__(self, compression_level=3):
        self.cctx = zstd.ZstdCompressor(level=compression_level)
        self.block_size = 768

    def _resonance_transform(self, data_bytes: bytes) -> tuple[bytes, bytes]:
        """Wrapper function that calls the high-speed JIT version."""
        # Convert input bytes to a NumPy array for Numba
        data_np = np.frombuffer(data_bytes, dtype=np.uint8)
        
        # Prepare empty output arrays
        class_ids_out = np.empty_like(data_np)
        indices_out = np.empty_like(data_np)

        # Call the JIT-compiled function
        _resonance_transform_jit(data_np, class_ids_out, indices_out, 
                                 BYTE_TO_CLASS_ID, BYTE_TO_INDEX)
        
        return class_ids_out.tobytes(), indices_out.tobytes()

    def _calculate_stream_hash(self, original_data: bytes) -> int:
        """Wrapper function that calls the high-speed JIT version."""
        data_np = np.frombuffer(original_data, dtype=np.uint8)

        # Call the JIT-compiled function
        return _calculate_stream_hash_jit(data_np, RESONANCE_VALUES_F64, 
                                          ALPHA_CONSTANTS_F64, SP_PRIME_P)

    def encode(self, data: bytes):
        """The main encoding pipeline using Numba-accelerated components."""
        
        class_stream, index_stream = self._resonance_transform(data)
        comp_class_stream = self.cctx.compress(class_stream)
        comp_index_stream = self.cctx.compress(index_stream)
        
        stream_hash = self._calculate_stream_hash(data)
        checksum_entries = []
        num_blocks = (len(data) + self.block_size - 1) // self.block_size
        for i in range(num_blocks):
            start = i * self.block_size
            end = min(start + self.block_size, len(data))
            block_data = data[start:end]
            # Checksum calculation is not JIT-ted yet as it's less critical
            # and requires the high-precision mpfr values.
            checksum = sum(calculate_resonance(b) for b in block_data)
            checksum_entries.append(struct.pack(CHECKSUM_FORMAT, float(checksum)))

        compressed_manifest = self.cctx.compress(b''.join(checksum_entries))
        
        main_header = struct.pack(
            MAIN_HEADER_FORMAT, 
            CDP_MAGIC, 9, 0, 
            stream_hash, 
            len(comp_class_stream), 
            len(comp_index_stream)
        )
        
        manifest_size_bytes = len(compressed_manifest).to_bytes(4, 'little')
        final_payload = main_header + manifest_size_bytes + compressed_manifest + comp_class_stream + comp_index_stream
        return final_payload


class CDPDecoder:
    """Decodes data from the CDP format. (No optimization needed here yet)."""
    # ... The CDPDecoder class remains completely unchanged from the V8 version ...
    def __init__(self):
        self.dctx = zstd.ZstdDecompressor()
        self._encoder = CDPEncoder() # For verification

    def decode(self, encoded_data: bytes) -> bytes:
        magic, major, minor, stream_hash, s_cls, s_idx = struct.unpack(
            MAIN_HEADER_FORMAT, encoded_data[:MAIN_HEADER_SIZE]
        )
        if magic != CDP_MAGIC or major != 9:
            raise ValueError(f"Not a valid CDP v9 file.")

        current_pos = MAIN_HEADER_SIZE
        manifest_size = int.from_bytes(encoded_data[current_pos:current_pos+4], 'little')
        current_pos += 4
        
        compressed_manifest = encoded_data[current_pos : current_pos + manifest_size]
        current_pos += manifest_size
        
        comp_class = encoded_data[current_pos : current_pos + s_cls]
        current_pos += s_cls
        comp_index = encoded_data[current_pos : current_pos + s_idx]

        class_stream = self.dctx.decompress(comp_class)
        index_stream = self.dctx.decompress(comp_index)
        
        original_data = bytearray(len(class_stream))
        for i in range(len(class_stream)):
            original_data[i] = resonance_map.get_byte_from_class(class_stream[i], index_stream[i])
        original_data = bytes(original_data)

        binary_manifest = self.dctx.decompress(compressed_manifest)
        num_blocks = len(binary_manifest) // CHECKSUM_SIZE
        for i in range(num_blocks):
            start = i * self._encoder.block_size
            end = min(start + self._encoder.block_size, len(original_data))
            block_data = original_data[start:end]
            
            stored_checksum, = struct.unpack(CHECKSUM_FORMAT, binary_manifest[i*CHECKSUM_SIZE:(i+1)*CHECKSUM_SIZE])
            calculated_checksum = sum(calculate_resonance(b) for b in block_data)

            if abs(float(calculated_checksum) - stored_checksum) > 1e-9:
                raise ValueError(f"Block {i} integrity check failed!")
        print(f"✅ All {num_blocks} block checksums verified.")

        calculated_hash = self._encoder._calculate_stream_hash(original_data)
        if stream_hash != calculated_hash:
            raise ValueError("FATAL: Final stream hash mismatch!")
        print("✅ Final stream hash verified.")
        
        return original_data