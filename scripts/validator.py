import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Union, Dict
from jsonschema import validate, ValidationError

os.environ["SWXSOC_MISSION"] = "padre"

import swxsoc
from swxsoc.util.util import parse_science_filename


class RequestValidator:
    """Validates reprocessing requests against JSON schema and business rules.

    Provides comprehensive validation of reprocessing request files, including:
    - Schema validation using JSON Schema Draft 7
    - Mission-specific instrument validation
    - Science filename format validation
    - Date range validation
    - Request type validation (date-range vs filename-based)

    Args:
        schema_path: Path to JSON Schema file. Defaults to 'schemas/request-schema.json'.

    Raises:
        ValueError: If schema file is invalid or not found.
    """

    def __init__(self, schema_path: Union[str, Path] = "schemas/request-schema.json"):
        """Initializes validator with specified JSON schema."""
        self.schema = self._load_json_file(schema_path)

    def _load_json_file(self, file_path: Union[str, Path]) -> Dict:
        """Load and parse a JSON file from the filesystem.

        Args:
            file_path: Path to JSON file to load

        Returns:
            Parsed JSON data as Python dictionary

        Raises:
            ValueError: For file not found or invalid JSON content
        """
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Error loading schema: {e}")

    def validate_file(self, request_path: Union[str, Path]) -> bool:
        """Validate a JSON request file against the schema and business rules.

        Args:
            request_path: Path to JSON request file to validate

        Returns:
            True if request is valid, False otherwise

        Raises:
            IOError: If file cannot be read
            JSONDecodeError: If file contains invalid JSON
        """
        try:
            with open(request_path, "r") as f:
                request_data = json.load(f)
            return self.validate_data(request_data, str(request_path))
        except Exception as e:
            swxsoc.log.error(f"Validation failed for {request_path}: {e}")
            return False

    def validate_data(self, request_data: Dict, label: str = "input") -> bool:
        """Validate request data dictionary against schema and business logic.

        Performs both structural validation (JSON Schema) and semantic validation:
        - Instrument name verification against mission configuration
        - Date range validation (from_date <= to_date)
        - Filename format validation
        - Mutual exclusivity of date-range and filename-based requests

        Args:
            request_data: Dictionary containing request data
            label: Identifier for logging purposes (default: "input")

        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Schema validation
            validate(instance=request_data, schema=self.schema)

            # Custom validation
            for request in request_data["requests"]:
                # Handle date-based vs filename-based requests
                if "request_filenames" in request:
                    self._validate_filename_request(request)
                else:
                    self._validate_range_request(request)

            swxsoc.log.info(f"Valid request: {label}")
            return True

        except ValidationError as e:
            swxsoc.log.error(f"Schema validation failed: {e.message}")
            return False
        except ValueError as e:
            swxsoc.log.error(f"Data validation failed: {e}")
            return False

    def _validate_filename_request(self, request: Dict):
        """Validate filename-based request structure and content.

        Args:
            request: Individual request dictionary

        Raises:
            ValueError: If request contains invalid fields or filenames

        Rules:
            - Must contain 'request_instrument' and 'request_filenames'
            - Must NOT contain date or level fields
            - All filenames must match mission-specific science filename format
        """
        # Check for forbidden fields
        forbidden_fields = [
            "request_from_date",
            "request_to_date",
            "request_from_level",
            "request_instrument",
        ]
        if any(f in request for f in forbidden_fields):
            raise ValueError("Filename requests cannot contain date/level fields")

        # Validate filenames
        for filename in request["request_filenames"]:
            try:
                parse_science_filename(filename.strip())
            except ValueError as e:
                raise ValueError(f"Invalid filename '{filename}': {e}")

    def _validate_range_request(self, request: Dict):
        """Validate and enhance date-range-based request.

        Args:
            request: Individual request dictionary

        Raises:
            ValueError: For invalid instrument or date ranges

        Behavior:
            - Sets default to_date (current date) if missing
            - Sets default from_level (l0) if missing
            - Validates instrument against mission configuration
            - Ensures from_date <= to_date
        """
        # Set defaults
        request.setdefault("request_from_level", "l0")

        # Instrument validation
        instrument = request["request_instrument"].lower().strip()
        if instrument not in swxsoc.config["mission"]["inst_names"]:
            raise ValueError(f"Invalid instrument: {instrument}")

        if "request_from_date" in request:
            # Convert dates
            try:
                request.setdefault("request_to_date", datetime.now().strftime("%Y%m%d"))
                from_date = datetime.strptime(request["request_from_date"], "%Y%m%d")
                to_date = datetime.strptime(request["request_to_date"], "%Y%m%d")
            except ValueError as e:
                raise ValueError(f"Invalid date format: {e}")

            # Validate date range
            if from_date > to_date:
                raise ValueError("From date cannot be after To date")


def main():
    """Command-line interface for request validation.

    Usage:
        python validator.py <request_file.json> [schema_file]

    Exit Codes:
        0 - Validation successful
        1 - Validation failed
        2 - Critical error

    Handles:
        - File I/O errors
        - Schema validation errors
        - Business rule violations
    """
    if len(sys.argv) < 2:
        print("Usage: python validator.py <request_file.json> [schema_file]")
        sys.exit(1)

    request_file = sys.argv[1]
    schema_file = sys.argv[2] if len(sys.argv) > 2 else "schemas/request-schema.json"

    try:
        validator = RequestValidator(schema_file)
        valid = validator.validate_file(request_file)
        sys.exit(0 if valid else 1)
    except Exception as e:
        swxsoc.log.error(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
