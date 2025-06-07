from django.contrib.auth.hashers import make_password, check_password
from django.utils.translation import gettext_lazy as _
from django.core.cache import caches
from django.conf import settings

import random
import requests
from requests.exceptions import RequestException
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed


class OTPService:
    """
    Service for generating and validating one-time passwords (OTPs).

    Utilizes Django's caching framework to temporarily store hashed OTPs for secure validation.
    Each OTP is stored in a hashed form and invalidated immediately after successful verification.
    """

    cache = caches["otp"]

    def generate(self, key):
        """
        Generate a new 5-digit OTP for the specified user and store it in the cache.

        Args:
            key (str): Unique identifier for the user.

        Returns:
            str: The plain-text OTP to be sent to the user.
        """
        # Create a 5-digit random OTP
        otp = str(random.randint(10000, 99999))
        # Hash the OTP for secure storage
        hashed_otp = make_password(otp)
        # Store the hashed OTP in the cache with the user ID as the key
        self.cache.set(key, hashed_otp)
        # Return the plain-text OTP for delivery to the user
        return otp

    def validate(self, key, otp):
        """
        Validate the OTP provided by the user against the stored hash.

        Args:
            key (str): Unique identifier for the user.
            otp (str): The plain-text OTP input provided by the user.

        Raises:
            AuthenticationFailed: If the OTP is invalid or missing.
        """
        # Retrieve the hashed OTP from the cache
        hashed_otp = self.cache.get(key)
        # If no OTP is found for the user, raise an authentication error
        if not hashed_otp:
            raise AuthenticationFailed(_("Invalid OTP."))
        # Compare the provided OTP against the stored hash
        is_valid = check_password(otp, hashed_otp)
        # Raise an exception if the OTP is invalid
        if not is_valid:
            raise AuthenticationFailed(_("Invalid OTP."))
        # Delete the OTP from cache after successful validation to prevent reuse
        self.cache.delete(key)
    
    def verify_and_mark_as_verified(self, key, otp):
        """
        Validate the OTP provided by the user against the stored hash.

        Args:
            key (str): Unique identifier for the user.
            otp (str): The plain-text OTP input provided by the user.

        Raises:
            AuthenticationFailed: If the OTP is invalid or missing.
        """
        # Retrieve the hashed OTP from the cache
        hashed_otp = self.cache.get(key)
        # If no OTP is found for the user, raise an authentication error
        if not hashed_otp:
            raise AuthenticationFailed(_("Invalid OTP."))
        # Compare the provided OTP against the stored hash
        is_valid = check_password(otp, hashed_otp)
        # Raise an exception if the OTP is invalid
        if not is_valid:
            raise AuthenticationFailed(_("Invalid OTP."))
        
        hashed_otp = make_password("VERIFIED")
        # Store the hashed OTP in the cache with the user ID as the key
        self.cache.set(key, hashed_otp)
        


class SMSService:
    """
    Service for sending SMS messages via the TextBee API.

    Attributes:
        api_key (str): API key for authenticating requests to TextBee.
        device_id (str): Identifier of the SMS sending device.
        url (str): Full endpoint URL for sending SMS messages.
    """

    def __init__(self):
        """
        Initialize the SMSService by loading configuration from Django settings.
        """
        # Load API credentials and device ID from Django settings
        self.api_key = settings.TEXTBEE_API_KEY
        self.device_id = settings.TEXTBEE_DEVICE_ID
        # Construct the URL for the send-sms endpoint
        self.url = (
            f"https://api.textbee.dev/api/v1/gateway/devices/{self.device_id}/send-sms"
        )

    def send_sms(self, recipient, message):
        """
        Send a single SMS message.

        Args:
            recipient (str): The phone number to which the SMS will be sent.
            message (str): The text content of the SMS.

        Returns:
            tuple: (success: bool, response: dict or str)
                   On success, response is the JSON data from the API.
                   On failure, response is an error message.
        """
        # Delegate to bulk send method for consistency
        return self.send_bulk_sms([recipient], message)

    def send_bulk_sms(self, recipients, message):
        """
        Send an SMS message to multiple recipients in a single request.

        Args:
            recipients (list of str): List of phone numbers for recipients.
            message (str): The text content of the SMS.

        Returns:
            tuple: (success: bool, response: dict or str)
                   On success, response is the JSON data from the API.
                   On failure, response is an error message.
        """
        # Prepare HTTP headers with API key for authentication
        headers = {
            "x-api-key": self.api_key,
        }
        # Prepare request payload containing recipients and message body
        payload = {
            "recipients": recipients,
            "message": message,
        }

        try:
            # Execute the POST request to the SMS gateway
            response = requests.post(self.url, json=payload, headers=headers)
            # Raise an exception for HTTP error codes (4xx, 5xx)
            response.raise_for_status()
            # Return success flag and parsed JSON response
            return True, response.json()
        except RequestException as e:
            # Handle exceptions and map to user-friendly messages
            return False, self._handle_exception(e)

    def _handle_exception(self, exception):
        """
        Map various RequestException types to readable error messages.

        Args:
            exception (RequestException): The caught exception instance.

        Returns:
            str: User-friendly error description.
        """
        # HTTP-level errors (status codes >=400)
        if isinstance(exception, requests.exceptions.HTTPError):
            status_code = exception.response.status_code
            # Unauthorized: invalid or missing API key
            if status_code == status.HTTP_401_UNAUTHORIZED:
                return "Invalid API credentials"
            # Not found: incorrect device ID
            elif status_code == status.HTTP_404_NOT_FOUND:
                return "Device not found"
            # Other API errors: include response body for debugging
            else:
                return f"API error: {exception.response.text}"
        # Network connectivity issues
        elif isinstance(exception, requests.exceptions.ConnectionError):
            return "Network connection failed"
        # Request timed out at server or network level
        elif isinstance(exception, requests.exceptions.Timeout):
            return "Request timed out"
        # Any other unexpected error
        else:
            return f"Unexpected error: {str(exception)}"
