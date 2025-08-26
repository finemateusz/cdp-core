# src/constants.py
"""
This module contains the foundational constants for Coherent Data Protocol (CDP).
It uses the gmpy2 library for high-precision arithmetic.
"""
import gmpy2
from gmpy2 import mpfr

# Set precision for gmpy2 calculations. 256 bits is ample.
gmpy2.get_context().precision = 256

# --- The 8 Field Constants (Alpha values) ---
# This set uses mathematical definitions for maximum accuracy.
ALPHA_CONSTANTS = {
    # α₀: Unity
    0: mpfr(1.0),

    # α₁: Tribonacci constant, the real root of x³ - x² - x - 1 = 0
    1: (mpfr(1) + (19 + 3 * gmpy2.sqrt(33))**(mpfr(1)/3) + (19 - 3 * gmpy2.sqrt(33))**(mpfr(1)/3)) / 3,

    # α₂: Golden Ratio, the positive root of x² - x - 1 = 0
    2: (mpfr(1) + gmpy2.sqrt(5)) / 2,

    # α₃: Binary generator
    3: mpfr(0.5),

    # α₄: 1 / (2 * pi)
    4: mpfr(1) / (2 * gmpy2.const_pi()),

    # α₅: 2 * pi
    5: 2 * gmpy2.const_pi(),

    # α₆: A specified constant
    6: mpfr('0.19961197478400415'),

    # α₇: Another specified constant (Note: the /1000 from library.py seems to be
    # an artifact; the direct value is what's in the spec docs)
    7: mpfr('0.014134725141734695'),
}

# --- Structural Constants ---
GAMMA = 24
MU = 48
EPSILON = 96

# --- Conservation & Integrity Constants ---
CONSERVATION_CHECKSUM_768_CYCLE = mpfr("687.110133051847")
CONSERVATION_TOLERANCE = mpfr("1e-76") # Increased precision for gmpy2

SP_PRIME_P = 11

# --- Helper for bit extraction ---
def get_bit(byte_value, bit_index):
    """Extracts the value of a specific bit from a byte."""
    if not (0 <= byte_value <= 255):
        raise ValueError("byte_value must be between 0 and 255.")
    if not (0 <= bit_index <= 7):
        raise ValueError("bit_index must be between 0 and 7.")
    return (byte_value >> bit_index) & 1