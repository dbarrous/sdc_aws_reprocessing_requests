# SDC AWS Reprocessing Requests - (PADRE)

This repository handles requests for reprocessing instrument data stored in AWS. Follow the instructions below to submit your reprocessing request.

## Important Notes

- **DO NOT FORK THIS REPOSITORY**. The GitHub workflows will not run correctly in a forked repository.
- Always clone the original repository and create a new branch for your request.
- First-time contributors may need a SOC Admin to approve workflow runs.
- All submissions require approval before merging, unless part of the GitHub Organization.

## Submission Process

### Step 1: Clone the Repository

```bash
git clone https://github.com/dbarrous/sdc_aws_reprocessing_requests.git
cd sdc_aws_reprocessing_requests
```

### Step 2: Create a New Branch

Create a branch with a descriptive name for your request:

```bash
git checkout -b request/your-username/YYYYMMDD
```

### Step 3: Create Your Request

1. Navigate to the `requests/submit` directory
2. Create a `request.json` file with your reprocessing request details
3. Ensure your request follows one of the supported request types (see Requests Types below)

### Step 4: Validate Your Request Locally (Optional)

You can validate your request locally before submitting:

```bash
pip install -r requirements.txt
python scripts/validator.py requests/submit/request.json
```

### Step 5: Commit and Push Your Changes

```bash
git add requests/submit/request.json
git commit -m "Add reprocessing request for <brief description>"
git push origin request/your-username/YYYYMMDD
```

### Step 6: Create a Pull Request

1. Go to the repository on GitHub
2. Click "New Pull Request"
3. Select your branch as the source
4. Add a descriptive title and description
5. Submit the PR

### Step 7: Wait for Workflow Validation

The GitHub workflow will:
1. Validate your request against the schema
2. Sort and rename the request file to the appropriate directory
3. Comment on your PR with the validation result

### Step 8: Pull the Changes After Successful Validation

If the workflow ran successfully:

```bash
git pull origin request/your-username/YYYYMMDD
```

### Step 9: Remove the Sorted Request File and Reset request.json

After the workflow moves your request file:

```bash
# Remove the sorted request file from your commit
git rm requests/YYYY/MM/request_username_YYYYMMDDHHMMSS.json

# Reset the submit request.json to empty or default state
echo '{"requests": []}' > requests/submit/request.json

# Commit these changes
git add .
git commit -m "Clean up after successful validation"
git push origin request/your-username/YYYYMMDD
```

### Step 10: Wait for PR Approval and Merge

A maintainer will review and approve your PR. Once merged, your reprocessing request will be processed.

## Request Types

The system supports two types of reprocessing requests:

### 1. Date Range Request

Use this to reprocess data for a specific instrument within a date range:

```json
{
  "requests": [
    {
      "request_instrument": "INSTRUMENT_NAME",
      "request_from_date": "YYYYMMDD",
      "request_to_date": "YYYYMMDD",
      "request_from_level": "l0",
      "request_description": "Optional description",
      "use_dev": false
    }
  ]
}
```

**Fields:**
- `request_instrument`: Instrument name (required)
- `request_from_date`: Start date in YYYYMMDD format (optional)
- `request_to_date`: End date in YYYYMMDD format (optional)
- `request_from_level`: Data level to start reprocessing from (default: "l0")
- `request_description`: Optional description of the request
- `use_dev`: Use development data instead of production (default: false)

### 2. Specific Files Request

Use this to reprocess specific files:

```json
{
  "requests": [
    {
      "request_filenames": [
        "file1.dat",
        "file2.dat"
      ],
      "request_description": "Optional description",
      "use_dev": false
    }
  ]
}
```

**Fields:**
- `request_filenames`: Array of filenames to reprocess (required)
- `request_description`: Optional description of the request
- `use_dev`: Use development data instead of production (default: false)

### Multiple Requests

You can include multiple requests in a single submission:

```json
{
  "requests": [
    {
      "request_instrument": "INSTRUMENT1",
      "request_from_date": "20250101",
      "request_to_date": "20250131"
    },
    {
      "request_filenames": [
        "specific_file.dat"
      ]
    }
  ]
}
```

## Troubleshooting

### Workflow Not Running

If you're a first-time contributor, GitHub may require approval to run workflows. A SOC Admin will need to approve this.

### Validation Errors

If your request fails validation:
1. Check the PR comments for specific error messages
2. Update your `request.json` file accordingly
3. Commit and push your changes
4. The workflow will automatically re-run

### If you need to make changes after a Successful Validation

After the workflow successfully runs and sorts your file, you'll need to:
1. Pull the changes to your local branch
2. Remove the sorted file from your branch
3. Reset the `requests/submit/request.json` file
4. Commit these changes
5. Push your updated branch

## Need Help?

Contact the SOC team for assistance with your reprocessing requests.