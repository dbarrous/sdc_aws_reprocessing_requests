import boto3
import json
import sys
from typing import List, Dict, Any


class LambdaInvoker:
    def __init__(self, lambda_name: str, region: str = "us-east-1"):
        self.lambda_client = boto3.client("lambda", region_name=region)
        self.lambda_name = lambda_name

    def invoke_with_payloads(
        self, payloads: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Invoke lambda with each payload wrapped in S3->SNS event structure."""
        results = []

        for original_payload in payloads:
            try:
                # Convert the simple payload format to S3 event structure
                s3_event_payload = {
                    "Records": [
                        {
                            "s3": {
                                "bucket": {"name": original_payload["bucket"]},
                                "object": {"key": original_payload["key"]},
                            }
                        }
                    ]
                }

                # Wrap in SNS message structure
                sns_event = {
                    "Records": [{"Sns": {"Message": json.dumps(s3_event_payload)}}]
                }

                response = self.lambda_client.invoke(
                    FunctionName=self.lambda_name,
                    InvocationType="Event",
                    Payload=json.dumps(sns_event).encode("utf-8"),
                )

                results.append(
                    {
                        "payload": original_payload,
                        "status_code": response["StatusCode"],
                        "response": (
                            response["Payload"].read().decode()
                            if response.get("Payload")
                            else None
                        ),
                    }
                )

                print(f"Invoked {self.lambda_name} with: {original_payload['key']}")

            except Exception as e:
                print(f"Error with {original_payload.get('key', 'unknown')}: {e}")
                results.append({"payload": original_payload, "error": str(e)})

        return results


def main():
    if len(sys.argv) < 3:
        print("Usage: python lambda_invoker.py <lambda_name> <payloads_file> [region]")
        sys.exit(1)

    lambda_name = sys.argv[1]
    payloads_file = sys.argv[2]
    region = sys.argv[3] if len(sys.argv) > 3 else "us-east-1"

    try:
        with open(payloads_file, "r") as f:
            payloads = json.load(f)

        invoker = LambdaInvoker(lambda_name, region)
        results = invoker.invoke_with_payloads(payloads)

        success = sum(
            1 for r in results if "status_code" in r and r["status_code"] == 202
        )
        print(
            f"\nInvocation summary: {success} successful, {len(results)-success} failed"
        )

        sys.exit(0 if success == len(results) else 1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
