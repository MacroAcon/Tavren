"""
Status constants used throughout the application.
"""

# HTTP Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_500_INTERNAL_SERVER_ERROR = 500

# Common Response Status Values
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_PENDING = "pending"
STATUS_FAILED = "failed"
STATUS_PAID = "paid"

# Common Error Details
DETAIL_INTERNAL_SERVER_ERROR = "Internal server error occurred."
DETAIL_NOT_FOUND = "Resource not found."
DETAIL_INVALID_REQUEST = "Invalid request parameters." 