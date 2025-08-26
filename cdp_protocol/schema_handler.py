# cdp_protocol/schema_handler.py
import json

class Schema:
    """
    Loads, validates, and provides access to a CDP schema definition from a JSON file.
    """
    def __init__(self, schema_filepath: str):
        """
        Initializes the Schema object by loading and validating the schema file.

        Args:
            schema_filepath: The path to the .json schema definition file.
        """
        try:
            with open(schema_filepath, 'r') as f:
                self.raw_schema = json.load(f)
        except FileNotFoundError:
            raise ValueError(f"Schema file not found at: {schema_filepath}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in schema file: {schema_filepath}")

        # --- Validation ---
        self._validate_schema()

        # --- Create fast lookup maps for convenience ---
        self.name_to_field = {field['name']: field for field in self.raw_schema['fields']}
        self.grade_to_field = {field['grade']: field for field in self.raw_schema['fields']}
        
        print(f"Schema '{self.raw_schema.get('name', 'Untitled')}' loaded and validated successfully.")

    def _validate_schema(self):
        """
        Performs a series of checks to ensure the loaded schema is valid.
        Raises ValueError if any check fails.
        """
        if 'fields' not in self.raw_schema or not isinstance(self.raw_schema['fields'], list):
            raise ValueError("Schema must contain a top-level 'fields' list.")

        if not self.raw_schema['fields']:
            raise ValueError("Schema 'fields' list cannot be empty.")

        seen_grades = set()
        seen_names = set()

        for i, field in enumerate(self.raw_schema['fields']):
            if not isinstance(field, dict):
                raise ValueError(f"Field at index {i} is not a valid object.")

            # Check for required keys in each field
            required_keys = {'name', 'type', 'grade'}
            if not required_keys.issubset(field.keys()):
                missing = required_keys - field.keys()
                raise ValueError(f"Field '{field.get('name', 'N/A')}' is missing required keys: {missing}")

            # Validate 'name'
            name = field['name']
            if not isinstance(name, str) or not name:
                raise ValueError(f"Field at index {i} has an invalid 'name'.")
            if name in seen_names:
                raise ValueError(f"Duplicate field name found: '{name}'")
            seen_names.add(name)
            
            # Validate 'grade'
            grade = field['grade']
            if not isinstance(grade, int) or not (0 <= grade <= 255):
                raise ValueError(f"Field '{name}' has an invalid grade: must be an integer between 0-255.")
            if grade in seen_grades:
                raise ValueError(f"Duplicate grade found: {grade}. Grades must be unique.")
            seen_grades.add(grade)

            # Validate 'type' (we will add more supported types later)
            supported_types = {'uint64', 'string_utf8', 'float32', 'bool', 'uint8', 'float32'}
            if field['type'] not in supported_types:
                raise ValueError(f"Field '{name}' has an unsupported type: '{field['type']}'.")

    def get_field_by_name(self, name: str) -> dict | None:
        """Returns the field definition dictionary for a given name."""
        return self.name_to_field.get(name)

    def get_field_by_grade(self, grade: int) -> dict | None:
        """Returns the field definition dictionary for a given grade."""
        return self.grade_to_field.get(grade)

    @property
    def fields(self) -> list:
        """Returns the list of all field definitions."""
        return self.raw_schema['fields']