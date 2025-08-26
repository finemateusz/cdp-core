# src/map_loader.py
"""
This module loads the canonical resonance map from the generated JSON file
and provides easy-to-use lookup functions.
"""
import json
import os

class ResonanceMap:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResonanceMap, cls).__new__(cls)
            cls._instance._load_map()
        return cls._instance

    def _load_map(self):
        """Loads the map from the file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            map_path = os.path.join(project_root, "data", "generated", "resonance_map.json")

            with open(map_path, 'r') as f:
                data = json.load(f)
            
            # Convert string keys back to integers for fast lookup
            self.byte_to_class = {int(k): v for k, v in data['byte_to_class'].items()}
            self.class_to_byte = data['class_to_byte']
            
            if len(self.byte_to_class) != 256 or len(self.class_to_byte) != 96:
                raise ValueError("Resonance map is malformed or incomplete.")

        except FileNotFoundError:
            raise RuntimeError(
                "resonance_map.json not found. "
                "Please run `generate-map` first to create it."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load or parse resonance map: {e}")

    def get_class_info(self, byte_value: int) -> dict:
        """Returns {'class_id': int, 'index': int} for a given byte."""
        return self.byte_to_class[byte_value]

    def get_byte_from_class(self, class_id: int, index: int) -> int:
        """Returns the byte value from a class_id and index."""
        return self.class_to_byte[class_id][index]

# Create a singleton instance for easy access throughout the application
resonance_map = ResonanceMap()