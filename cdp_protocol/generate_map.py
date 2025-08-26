# src/generate_map.py
"""
Phase 0: Foundational Mathematics & Verification Script.
... (docstring is the same) ...
"""
import json
import os
from collections import defaultdict
import pandas as pd

from .core_math import calculate_resonance

def generate_and_verify_partition():
    """
    Calculates the resonance partition and verifies its properties using a
    high-precision rounding strategy for grouping.
    """
    print("PHASE 0: Generating and Verifying Resonance Partition...")
    print("-" * 50)

    resonance_groups = defaultdict(list)
    # This rounding precision is the key to correct grouping. 60 decimal places
    # is high enough to be precise but low enough to group identical values.
    rounding_precision = 60

    for byte_val in range(256):
        r_val = calculate_resonance(byte_val)
        # Format the number to a fixed precision string to use as a stable key
        r_key = f"{r_val:.{rounding_precision}f}"
        resonance_groups[r_key].append(byte_val)

    print(f"Found {len(resonance_groups)} unique resonance values.")

    # --- Verification ---
    num_classes = len(resonance_groups)
    if num_classes != 96:
        raise AssertionError(f"VERIFICATION FAILED: Expected 96 classes, but found {num_classes}.")
    print("✅ PASS: Exactly 96 unique resonance values confirmed.")

    class_sizes = defaultdict(int)
    for r_key, members in resonance_groups.items():
        class_sizes[len(members)] += 1

    num_quads = class_sizes.get(4, 0)
    num_doubles = class_sizes.get(2, 0)

    print(f"Class size distribution: {dict(class_sizes)}")
    if num_quads != 32:
        raise AssertionError(f"VERIFICATION FAILED: Expected 32 classes of size 4, but found {num_quads}.")
    print("✅ PASS: Found 32 classes with 4 members.")
    
    if num_doubles != 64:
        raise AssertionError(f"VERIFICATION FAILED: Expected 64 classes of size 2, but found {num_doubles}.")
    print("✅ PASS: Found 64 classes with 2 members.")

    if not (num_quads * 4 + num_doubles * 2 == 256):
        raise AssertionError("VERIFICATION FAILED: Total members in classes do not sum to 256.")

    print("-" * 50)
    print("All foundational claims verified successfully.")

    return resonance_groups


def create_canonical_map(resonance_groups):
    """
    Creates the final lookup maps for the CDP protocol.
    """
    print("\nCreating canonical lookup maps...")
    # Sort the unique resonance keys (which are strings) based on their float value.
    sorted_r_keys = sorted(resonance_groups.keys(), key=lambda k: float(k))

    class_id_map = {r_key: i for i, r_key in enumerate(sorted_r_keys)}

    byte_to_class = {}
    class_to_byte = [[] for _ in range(96)]

    for r_key, members in resonance_groups.items():
        class_id = class_id_map[r_key]
        sorted_members = sorted(members)
        class_to_byte[class_id] = sorted_members

        for index, byte_val in enumerate(sorted_members):
            byte_to_class[byte_val] = {
                "class_id": class_id,
                "index": index
            }

    print("✅ Canonical maps created.")
    return {
        "byte_to_class": byte_to_class,
        "class_to_byte": class_to_byte
    }

def save_map_to_file(canonical_map, filepath):
    """Saves the generated map to a JSON file, ensuring the directory exists."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    canonical_map_json_ready = {
        "byte_to_class": {str(k): v for k, v in canonical_map["byte_to_class"].items()},
        "class_to_byte": canonical_map["class_to_byte"]
    }
    with open(filepath, 'w') as f:
        json.dump(canonical_map_json_ready, f, indent=2)
    print(f"\n✅ Resonance map saved to: {filepath}")

def display_partition_summary(canonical_map, resonance_groups):
    """Displays the partition details in a readable table."""
    df_data = []
    class_to_byte = canonical_map["class_to_byte"]
    
    # Create a reverse lookup from class_id to the string representation of its resonance value
    r_key_lookup = {}
    for r_key, members in resonance_groups.items():
        byte_val = members[0]
        class_id = canonical_map["byte_to_class"][byte_val]["class_id"]
        r_key_lookup[class_id] = r_key

    for class_id, members in enumerate(class_to_byte):
        r_key = r_key_lookup.get(class_id, "N/A")
        df_data.append({
            "ClassID": class_id,
            "Size": len(members),
            "Members": ", ".join(map(str, members)),
            "ResonanceValue": f"{r_key[:12]}..." # Show first few digits
        })
    df = pd.DataFrame(df_data).sort_values("ClassID")
    print("\n--- Resonance Partition Summary ---")
    print(df.to_string(index=False))
    print("-----------------------------------")


def main():
    """Main entry point for the script."""
    try:
        groups = generate_and_verify_partition()
        final_map = create_canonical_map(groups)
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        output_path = os.path.join(project_root, "data", "generated", "resonance_map.json")
        
        save_map_to_file(final_map, output_path)
        display_partition_summary(final_map, groups)

    except AssertionError as e:
        print("\n--- SCRIPT HALTED ---")
        print(f"Error: {e}")
        print("The foundational claims could not be verified. Please check the constants.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()