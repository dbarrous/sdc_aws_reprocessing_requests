import json
from scripts.validator import RequestValidator
from scripts.payload_generator import PayloadGenerator
from scripts.lambda_invoker import LambdaInvoker

request_file = "tests/valid_request.json"
validator = RequestValidator()

is_valid = validator.validate_file(request_file)

if is_valid:
    print("Request is valid. Proceeding to generate payloads.")
    generator = PayloadGenerator()
    # Load json request file
    with open(request_file, "r") as f:
        request_data = json.load(f)
    payloads = generator.generate_payloads(request_data)
    print("Generated payloads:")
    print(json.dumps(payloads, indent=4))

    if payloads:
        lambda_name = "padre_sdc_aws_processing_lambda_function"

        invoker = LambdaInvoker(lambda_name)

        results = invoker.invoke_with_payloads(payloads)
        print("Invocation results:")
        print(json.dumps(results, indent=4))
    success_count = sum(
        1 for r in results if "status_code" in r and r["status_code"] == 202
    )
    failure_count = len(results) - success_count
    print(f"Success: {success_count}, Failure: {failure_count}")
    print("Payloads processed successfully.")

else:
    print("Request is invalid. Please check the request file.")
