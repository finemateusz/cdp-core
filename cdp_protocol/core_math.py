# src/core_math.py
"""
Implements the core mathematical functions of the CDP, primarily the
Resonance function R(b).
"""
from functools import lru_cache
from gmpy2 import mpfr

from .constants import ALPHA_CONSTANTS, get_bit

@lru_cache(maxsize=256)
def calculate_resonance(byte_value: int) -> mpfr:
    """
    Calculates the resonance value R(b) for a given byte.

    Formula from `resonance-algebra-formalization.md`:
    R(b) = ∏(i=0 to 7) αᵢ^(bit_i(b))

    Args:
        byte_value: An integer from 0 to 255.

    Returns:
        The calculated resonance value as a high-precision gmpy2.mpfr.
    """
    if not (0 <= byte_value <= 255):
        raise ValueError("Input must be a valid byte (0-255).")

    resonance = mpfr("1.0")

    for i in range(8):
        if get_bit(byte_value, i) == 1:
            resonance *= ALPHA_CONSTANTS[i]

    return resonance