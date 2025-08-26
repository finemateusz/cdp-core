---

### **The Coherent Data Format (CDF) Specification**

The core principle of CDF is to **intentionally map semantic meaning to the structure of the Resonance Classes.** We will use the two streams exactly as we hypothesized in the medical record example, but we will force it to be true by design.

**Design Principle:**
*   **Labels (Keys/Field Names)** will be represented by bytes that fall into a small, predictable set of **Resonance Classes**.
*   **Values (Sensitive Data)** will be represented by bytes that are overwhelmingly the **canonical members (Index 0)** of their respective Resonance Classes.

#### **Step 1: The Canonical Dictionary**

First, we pre-compute a "Canonical Dictionary" from our `resonance_map.json`. This is a one-time setup.

The dictionary maps every possible byte (0-255) to its **canonical representative**, which is the first byte (index 0) in its Resonance Class.
*   `canonical_rep[0] = 0` (since 0 is index 0 of Class 76)
*   `canonical_rep[1] = 0` (since 1 is index 1 of Class 76, its canonical rep is 0)
*   `canonical_rep[2] = 2` (since 2 is index 0 of Class 82)
*   ...and so on for all 256 bytes.

#### **Step 2: The CDF Encoding Rule**

When we want to serialize a key-value pair, like a patient's heart rate (`"heart_rate": 75`), we do the following:

1.  **Encode the Key (Label):**
    *   Take the string `"heart_rate"`.
    *   Hash it to a single byte using a simple, non-cryptographic hash (e.g., CRC8). Let's say `CRC8("heart_rate") = 110`.
    *   This byte, `110`, is our **Tag** for the "heart rate" field. We write this byte to the stream.

2.  **Encode the Value (Sensitive Data):**
    *   Take the numerical value `75`.
    *   **Find its canonical representative** from our pre-computed dictionary: `canonical_rep[75] = 74`.
    *   **Calculate the difference (delta):** `delta = 75 - 74 = 1`.
    *   We write two bytes to the stream:
        *   The **canonical byte**: `74`.
        *   The **delta byte**: `1`.

**Our final serialized data for `"heart_rate": 75` is the three-byte sequence: `[110, 74, 1]`**

---

### **Why This is a Perfect Fit for CDP and HE**

Let's see what happens when we feed a stream of this CDF-encoded data into our CDP encoder.

**The Input Stream:**
`[Tag_HR, Rep_HR, Delta_HR, Tag_Temp, Rep_Temp, Delta_Temp, ...]`
`[110, 74, 1, 15, 66, 2, ...]`

**The CDP Transform Output:**

1.  **The `class_stream`:**
    *   This stream will contain the sequence of Resonance Classes for `[110, 74, 1, 15, 66, 2, ...]`.
    *   It will represent the high-level structure: `[Class(Tag), Class(Rep), Class(Delta), Class(Tag), ...]`.
    *   Since there are only a few types of fields (tags), and the delta values are almost always very small numbers (`0, 1, 2, ...`), this stream will have **low-to-moderate entropy**. It's structured and compressible.

2.  **The `index_stream`:**
    *   This is the magic part.
    *   When the transform processes a **Tag byte** (like `110`), it produces some `index` value.
    *   When it processes a **Canonical Representative byte** (like `74`), by definition, its index in its own Resonance Class is **always 0**.
    *   When it processes a **Delta byte** (like `1` or `2`), these are very small numbers. Small numbers tend to belong to a few specific Resonance Classes (like Class 76 and 82), and they are often the canonical representative (index 0) themselves.
    *   The result is that the `index_stream` will be **overwhelmingly composed of zeros.**

**The Result:**

*   The **`index_stream`** becomes a sparse, simple signal with extremely low entropy. It is the perfect candidate for efficient Homomorphic Encryption. It represents the "fine-tuning" or "error term" of the data.
*   The **`class_stream`** contains the high-level structural information. It is less sensitive and can be protected with standard, fast encryption.

This CDF format is a concrete, practical way to create that "sparse, simple signal" you envisioned. It's a data representation that is co-designed to be perfectly optimized for the unique analytical capabilities of the Coherent Data Protocol.