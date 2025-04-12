import requests
import sys
import json

API_ENDPOINT = "http://127.0.0.1:8000/api/payouts/process-auto"

def run_processor():
    """Sends a POST request to trigger the payout processor and prints the result."""
    print(f"Attempting to trigger payout processor at {API_ENDPOINT}...")
    
    try:
        response = requests.post(API_ENDPOINT, timeout=60) # Added a timeout

        # Check if the request was successful
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

        # Parse the JSON response (summary)
        summary = response.json()

        # Print success message with summary details
        print("\nPayout processing triggered successfully!")
        print("-------------------------------------")
        print(f"Total Pending Payouts Checked: {summary.get('total_pending', 'N/A')}")
        print(f"Total Processed in this run:   {summary.get('processed', 'N/A')}")
        print(f"Successfully Marked as Paid:   {summary.get('marked_paid', 'N/A')}")
        print(f"Skipped (Low Trust Score):     {summary.get('skipped_low_trust', 'N/A')}")
        print(f"Skipped (Amount > $50.00):   {summary.get('skipped_high_amount', 'N/A')}")
        print(f"Skipped (Other Error):         {summary.get('skipped_other_error', 'N/A')}")
        print("-------------------------------------")
        
        # Indicate success exit
        return 0 

    except requests.exceptions.ConnectionError as e:
        print(f"\nError: Could not connect to the API endpoint at {API_ENDPOINT}", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        return 1 # Indicate failure exit
    except requests.exceptions.Timeout as e:
        print(f"\nError: Request timed out after 60 seconds.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        return 1
    except requests.exceptions.HTTPError as e:
        print(f"\nError: HTTP error occurred while contacting the API.", file=sys.stderr)
        print(f"Status Code: {e.response.status_code}", file=sys.stderr)
        try:
            # Try to print JSON error detail from response
            error_details = e.response.json()
            print(f"Server Response: {json.dumps(error_details)}", file=sys.stderr)
        except json.JSONDecodeError:
            # If response is not JSON, print raw text
            print(f"Server Response (non-JSON): {e.response.text}", file=sys.stderr)
        return 1
    except requests.exceptions.RequestException as e:
        print(f"\nError: An unexpected error occurred during the request.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nError: An unexpected error occurred in the script.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    exit_code = run_processor()
    sys.exit(exit_code) 