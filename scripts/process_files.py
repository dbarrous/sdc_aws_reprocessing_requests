import os
import sys
import json
import logging
from validator import RequestValidator
from payload_generator import PayloadGenerator
from lambda_invoker import LambdaInvoker

def process_file(file_path, validator, generator, invoker):
    try:
        logging.info(f"\nProcessing file: {file_path}")
        
        # Validate request
        if not validator.validate_file(file_path):
            logging.error(f"Invalid request: {file_path}")
            return (0, 0, 1)
        
        # Generate payloads
        with open(file_path, "r") as f:
            request_data = json.load(f)
        payloads = generator.generate_payloads(request_data)
        
        if not payloads:
            logging.warning("No payloads generated")
            return (0, 0, 1)

        # Invoke Lambda
        results = invoker.invoke_with_payloads(payloads)
        success = sum(1 for r in results if r.get("status_code") == 202)
        failure = len(results) - success
        
        logging.info(f"{success} successful, {failure} failed payloads")
        return (success, failure, 0)
        
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in {file_path}")
        return (0, 0, 1)
    except Exception as e:
        logging.error(f"Unexpected error processing {file_path}: {str(e)}")
        return (0, 0, 1)

def main():

    validator = RequestValidator()
    generator = PayloadGenerator()
    invoker = LambdaInvoker()
    
    total = {"success": 0, "failure": 0, "errors": 0}

    print("\nStarting request processing")
    for line in sys.stdin:
        file_path = line.strip()
        if not file_path:
            continue
            
        s, f, e = process_file(file_path, validator, generator, invoker)
        total["success"] += s
        total["failure"] += f
        total["errors"] += e

    print("\nFinal Results:")
    print(f"Total successful payloads: {total['success']}")
    print(f"Total failed payloads: {total['failure']}")
    print(f"Total errors/skipped files: {total['errors']}")
    
    if total["failure"] + total["errors"] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()