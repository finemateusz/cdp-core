# benchmark.py
"""
V5: Final benchmark script with restored detailed reporting (size, ratio, time)
and entropy analysis.
"""
import os
import time
import zlib
import zstandard as zstd
import pandas as pd
import numpy as np
import subprocess
import sys

from cdp_protocol import CDPEncoder

# --- Entropy Calculation Function (Unchanged) ---
def calculate_entropy(data: bytes) -> float:
    """Calculates the Shannon entropy of a byte stream."""
    if not data:
        return 0
    counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
    probabilities = counts / len(data)
    non_zero_probabilities = probabilities[probabilities > 0]
    entropy = -np.sum(non_zero_probabilities * np.log2(non_zero_probabilities))
    return entropy

def benchmark_file(filepath):
    """Runs all compression benchmarks and entropy analysis on a single file."""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}. Skipping.")
        return None

    with open(filepath, 'rb') as f:
        data = f.read()

    original_size = len(data)
    if original_size == 0: return None

    results = {'file': os.path.basename(filepath), 'original_size': original_size}
    
    print(f"\n--- Analyzing {results['file']} ({original_size/1024/1024:.2f} MB) ---")

    # --- CDP Transforms and Entropy Analysis ---
    encoder = CDPEncoder(compression_level=19)
    class_stream, index_stream = encoder._resonance_transform(data)
    results['entropy_original'] = calculate_entropy(data)
    results['entropy_class'] = calculate_entropy(class_stream)
    results['entropy_index'] = calculate_entropy(index_stream)
    
    # --- CDP Benchmark ---
    print("Encoding with CDP...")
    start_time = time.perf_counter()
    cdp_encoded = encoder.encode(data)
    end_time = time.perf_counter()
    results['cdp_size'] = len(cdp_encoded)
    results['cdp_ratio'] = len(cdp_encoded) / original_size
    results['cdp_time'] = end_time - start_time
    
    # --- zstd Benchmark ---
    print("Encoding with zstd...")
    cctx = zstd.ZstdCompressor(level=19)
    start_time = time.perf_counter()
    zstd_encoded = cctx.compress(data)
    end_time = time.perf_counter()
    results['zstd_size'] = len(zstd_encoded)
    results['zstd_ratio'] = len(zstd_encoded) / original_size
    results['zstd_time'] = end_time - start_time

    # --- gzip Benchmark ---
    print("Encoding with gzip...")
    start_time = time.perf_counter()
    gzip_encoded = zlib.compress(data, level=9)
    end_time = time.perf_counter()
    results['gzip_size'] = len(gzip_encoded)
    results['gzip_ratio'] = len(gzip_encoded) / original_size
    results['gzip_time'] = end_time - start_time

    return results

def main():
    """Main function to generate datasets and run analysis."""
    print("="*50)
    print("Generating benchmark datasets...")
    print("="*50)
    klein_script_path = os.path.join("data", "testsets", "generate_klein_dataset.py")
    canonical_script_path = os.path.join("data", "testsets", "generate_canonical_dataset.py")
    subprocess.run([sys.executable, klein_script_path], check=True)
    subprocess.run([sys.executable, canonical_script_path], check=True)
    
    datasets = [
        "data/testsets/AE005176.mark.asn",
        "data/testsets/etherscan_transactions.json",
        "data/testsets/nci",
        "data/testsets/sao",
        "data/testsets/dickens",
        "data/testsets/osdb",
    ]
    
    all_results = []
    for dataset_path in datasets:
        result = benchmark_file(dataset_path)
        if result:
            all_results.append(result)
            
    df = pd.DataFrame(all_results)
    
    pd.set_option('display.width', 200)
    pd.set_option('display.max_columns', 20)
    
    # --- DETAILED COMPRESSION RATIO TABLE ---
    print("\n\n" + "="*120)
    print("--- DETAILED COMPRESSION SUMMARY ---")
    print("="*120)
    
    df_display = df[['file', 'original_size', 
                     'cdp_size', 'cdp_ratio', 'cdp_time',
                     'zstd_size', 'zstd_ratio', 'zstd_time',
                     'gzip_size', 'gzip_ratio', 'gzip_time']].copy()

    # Helper function to format bytes into a readable string
    def format_bytes(b):
        if b > 1024 * 1024: return f"{b / (1024*1024):.2f} MB"
        return f"{b / 1024:.2f} KB"

    # Apply formatting
    for col in ['original_size', 'cdp_size', 'zstd_size', 'gzip_size']:
        df_display[col] = df_display[col].apply(format_bytes)
    
    for col in ['cdp_ratio', 'zstd_ratio', 'gzip_ratio']:
        df_display[col] = df_display[col].apply(lambda x: f"{x:.2%}")
        
    for col in ['cdp_time', 'zstd_time', 'gzip_time']:
        df_display[col] = df_display[col].apply(lambda x: f"{x:.4f}s")

    print(df_display.to_string(index=False))
    print("\nLOWER ratio is BETTER.")
    print("="*120)

    # --- ENTROPY ANALYSIS TABLE ---
    print("\n\n" + "="*120)
    print("--- ENTROPY ANALYSIS (LOWER IS BETTER) ---")
    print("="*120)
    df_entropy = df[['file', 'entropy_original', 'entropy_class', 'entropy_index']].copy()
    for col in df_entropy.columns[1:]:
        df_entropy[col] = df_entropy[col].apply(lambda x: f"{x:.4f} bits/byte")
    print(df_entropy.to_string(index=False))
    print("\n(Note: Ideal zstd compression ratio should be close to the lowest component Entropy / 8.0)")
    print("="*120)

if __name__ == "__main__":
    main()