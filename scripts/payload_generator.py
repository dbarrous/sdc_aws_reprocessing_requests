import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import os

os.environ["SWXSOC_MISSION"] = (
    "padre"  # Set the environment variable for SWXSOC mission
)
from typing import List, Dict, Optional
from swxsoc.util.util import (
    SWXSOCClient,
    SearchTime,
    Instrument,
    Level,
    DevelopmentBucket,
    AttrAnd,
)


class PayloadGenerator:
    """Generates reprocessing payloads using FIDO client with proper attribute handling"""

    def __init__(self):
        self.client = SWXSOCClient()
        self.logger = logging.getLogger(__name__)

    def generate_payloads(self, request_data: Dict) -> List[Dict]:
        """Generate verified payloads using FIDO-compatible queries"""
        payloads = []

        for request in request_data.get("requests", []):
            if "request_filenames" in request:
                payloads.extend(self._process_filename_request(request))
            else:
                payloads.extend(self._process_date_request(request))

        self.logger.info(f"Generated {len(payloads)} verified payloads")
        return payloads

    def _process_date_request(self, request: Dict) -> List[Dict]:
        """Process date-range request using existing FIDO search logic"""
        instrument = request["request_instrument"]
        from_date = request.get("request_from_date", None)
        to_date = request.get("request_to_date", None)
        
        from_date = self._parse_date(from_date) if from_date else None
        to_date = self._parse_date(to_date) if to_date else datetime.now()
        
        from_level = request.get("request_from_level", None)
        use_dev = request.get("use_dev", False)

        payloads = []

        try:

            query = []

            query.append(Instrument(instrument))

            if from_level:
                query.append(Level(from_level))

            if use_dev:  # Check if development bucket is used
                query.append(DevelopmentBucket(True))

            # Add date range to query
            if from_date and to_date:
                query.append(SearchTime(from_date.isoformat(), to_date.isoformat()))

            if from_date and not to_date:
                query.append(SearchTime(from_date.isoformat()))

            results = self.client.search(AttrAnd(query))

            print(
                f"Found {len(results)} files for {instrument} from {from_date} to {to_date}"
            )

            for result in results:
                # Get bucket and key from result
                bucket = result["bucket"]
                key = result["key"]

                payloads.append(
                    {
                        "bucket": bucket,
                        "key": key,
                    }
                )

        except Exception as e:
            self.logger.error(
                f"Search failed for {instrument} ({from_date} to {to_date}): {e}"
            )

        return payloads

    def _process_filename_request(self, request: Dict) -> List[Dict]:
        """Process date-range request using existing FIDO search logic"""
        requested_filenames = request.get("request_filenames", [])
        use_dev = request.get("use_dev", False)

        if not requested_filenames:
            self.logger.error("No filenames provided in request")
            return []

        payloads = []

        try:

            query = []

            if use_dev:  # Check if development bucket is used
                query.append(DevelopmentBucket(True))

            results = self.client.search(AttrAnd(query))

            print(f"Found {len(results)} files in total")

            for result in results:
                # Get bucket and key from result
                bucket = result["bucket"]
                key = result["key"]
                parsed_key = Path(key).name

                if parsed_key not in requested_filenames:
                    continue

                payloads.append(
                    {
                        "bucket": bucket,
                        "key": key,
                    }
                )

                print(f"Found file: {key} in bucket: {bucket}")

        except Exception as e:
            self.logger.error(f"Search failed for filenames: {e}")
        return payloads

    def _create_payload(self, request: Dict, date: datetime, level: str) -> Dict:
        """Create payload with FIDO-compatible structure"""
        return {
            "instrument": request["request_instrument"],
            "date": date.date().isoformat(),
            "level": level,
            "processing_parameters": {
                "reprocess_level": request.get("reprocess_level", "l2"),
                "calibration_version": request.get("calibration_version", "latest"),
            },
            "metadata": {
                "request_source": "date_range",
                "description": request.get("request_description", ""),
            },
        }

    def _create_filename_payload(self, request: Dict, result: Dict) -> Dict:
        """Create filename-based payload with S3 metadata"""
        return {
            "s3_metadata": {
                "bucket": result["bucket"],
                "key": result["key"],
                "etag": result["etag"],
                "last_modified": result["last_modified"].isoformat(),
            },
            "instrument": result["instrument"],
            "processing_parameters": {
                "reprocess_level": request.get("reprocess_level", "l2"),
                "calibration_version": request.get("calibration_version", "latest"),
            },
            "metadata": {
                "request_source": "filename",
                "original_filename": Path(result["key"]).name,
                "description": request.get("request_description", ""),
            },
        }

    def _parse_date(self, date_str: str) -> datetime:
        """Validate and parse date string"""
        try:
            return datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            self.logger.error(f"Invalid date format: {date_str}")
            raise ValueError("Date must be in YYYYMMDD format")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Example usage
    generator = PayloadGenerator()

    sample_request = {
        "requests": [
            {
                "request_filenames": ["padreMDA0_250403185914.dat"],
                "request_description": "Test filename request",
            },
        ]
    }

    payloads = generator.generate_payloads(sample_request)
    print(json.dumps(payloads, indent=2))
