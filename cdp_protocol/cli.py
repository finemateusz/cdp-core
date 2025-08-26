# cli.py
"""
Command-Line Interface for the Coherent Data Protocol tool.
"""
import argparse
import time
import os

from .cdp_protocol import CDPEncoder, CDPDecoder
from .structured_encoder import StructuredEncoder

def handle_encode(args):
    """Handles the encode subcommand."""
    print(f"Encoding file: {args.input_file} -> {args.output_file}")
    
    try:
        with open(args.input_file, 'rb') as f_in:
            data = f_in.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_file}'")
        return

    # --- THIS IS THE NEW SECTION ---
    original_size = len(data)
    if original_size == 0:
        print("Warning: Input file is empty.")
    
    encoder = CDPEncoder(compression_level=args.level)
    
    start_time = time.perf_counter()
    encoded_data = encoder.encode(data)
    end_time = time.perf_counter()
    
    encoded_size = len(encoded_data)

    with open(args.output_file, 'wb') as f_out:
        f_out.write(encoded_data)
        
    print(f"\nEncoding complete in {end_time - start_time:.4f} seconds.")
    
    # --- ADDED DETAILED LOGGING ---
    print("\n--- Compression Summary ---")
    print(f"  Original Size:   {original_size / 1024:.2f} KB ({original_size} bytes)")
    print(f"  Encoded Size:    {encoded_size / 1024:.2f} KB ({encoded_size} bytes)")
    
    if original_size > 0:
        ratio = encoded_size / original_size
        space_saved = 1 - ratio
        print(f"  Compression Ratio: {ratio:.2%}")
        print(f"  Space Saved:       {space_saved:.2%}")
    print("---------------------------")
    print(f"Output written to {args.output_file}")


def handle_decode(args):
    """Handles the decode subcommand."""
    print(f"Decoding file: {args.input_file} -> {args.output_file}")

    try:
        with open(args.input_file, 'rb') as f_in:
            encoded_data = f_in.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_file}'")
        return

    decoder = CDPDecoder()
    
    start_time = time.perf_counter()
    decoded_data = decoder.decode(encoded_data)
    end_time = time.perf_counter()
    
    with open(args.output_file, 'wb') as f_out:
        f_out.write(decoded_data)

    print(f"\nDecoding complete in {end_time - start_time:.4f} seconds.")
    print(f"Output written to {args.output_file}")
    
    # Optional: Verify integrity after decoding by comparing file sizes
    original_file_path = args.original_file
    if original_file_path:
        print("\n--- Verification ---")
        if os.path.exists(original_file_path):
            original_size = os.path.getsize(original_file_path)
            decoded_size = len(decoded_data)
            print(f"  Original file size:   {original_size} bytes")
            print(f"  Decoded file size:    {decoded_size} bytes")
            if decoded_size == original_size:
                print("  ✅ SUCCESS: Decoded file size matches original.")
            else:
                print("  ❌ FAILURE: Decoded size does not match original size.")
        else:
            print(f"  Warning: Original file for verification not found at '{original_file_path}'")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Coherent Data Protocol Tool (CDP)",
        formatter_class=argparse.RawTextHelpFormatter # For better help text formatting
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Encode command ---
    parser_encode = subparsers.add_parser("encode", help="Encode a file using CDP.")
    parser_encode.add_argument("input_file", help="Path to the input file.")
    parser_encode.add_argument("output_file", help="Path for the encoded output file.")
    parser_encode.add_argument("-l", "--level", type=int, default=19, help="Zstandard compression level (1-22). Default: 19")
    parser_encode.set_defaults(func=handle_encode)

    # --- Decode command ---
    parser_decode = subparsers.add_parser("decode", help="Decode a CDP-encoded file.")
    parser_decode.add_argument("input_file", help="Path to the CDP-encoded file.")
    parser_decode.add_argument("output_file", help="Path for the decoded output file.")
    parser_decode.add_argument("-o", "--original-file", help="Optional: Path to the original file to verify against.")
    parser_decode.set_defaults(func=handle_decode)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()