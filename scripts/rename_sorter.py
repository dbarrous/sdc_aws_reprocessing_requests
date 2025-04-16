"""File sorter for reprocessing requests in a CI/CD pipeline.

This script handles validation, payload simulation, and organization of reprocessing request files
into a structured directory format. It's designed to run during GitHub pull request workflows.
"""

import json
import argparse
from pathlib import Path
import shutil
from typing import Dict, List, Any
import os
os.environ["SWXSOC_MISSION"] = (
    "padre"  # Set the environment variable for SWXSOC mission
)
import swxsoc
from validator import RequestValidator
from payload_generator import PayloadGenerator


def main() -> None:
    """Main execution flow for processing reprocessing requests.
    
    Handles:
    - Command line argument parsing
    - JSON schema validation
    - Payload generation simulation
    - File organization in YYYY/MM directory structure
    """
    parser = argparse.ArgumentParser(
        description="Process and organize reprocessing requests",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--request-file",
        required=True,
        help="Path to the request.json file for processing"
    )
    parser.add_argument(
        "--username",
        required=True,
        help="GitHub username associated with the pull request"
    )
    parser.add_argument(
        "--timestamp",
        required=True,
        help="Timestamp in YYYYMMDDHHMMSS format for unique file naming"
    )
    args = parser.parse_args()

    # Validate request against JSON schema
    validator = RequestValidator()
    if not validator.validate_file(args.request_file):
        swxsoc.log.error("Validation failed: Request does not conform to schema")
        exit(1)

    # Simulate payload generation without Lambda invocation
    try:
        with open(args.request_file, "r") as f:
            request_data: Dict[str, Any] = json.load(f)
        
        generator = PayloadGenerator()
        payloads: List[Dict[str, Any]] = generator.generate_payloads(request_data)
        
        swxsoc.log.info("Payload generation successful")
        swxsoc.log.info("Generated payload preview:")
        swxsoc.log.info(json.dumps(payloads[:1], indent=4))  # Show first payload as sample
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        swxsoc.log.error(f"Payload generation failed: {str(e)}")
        exit(1)

    # Organize validated request into directory structure
    year: str = args.timestamp[:4]
    month: str = args.timestamp[4:6]
    new_filename: str = f"request_{args.username}_{args.timestamp}.json"
    
    target_dir: Path = Path("requests") / year / month
    target_dir.mkdir(parents=True, exist_ok=True)
    
    target_path: Path = target_dir / new_filename
    shutil.move(args.request_file, target_path)
    
    swxsoc.log.info(f"Successfully archived request to: {target_path}")


if __name__ == "__main__":
    main()