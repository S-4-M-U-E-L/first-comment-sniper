import os
import sys
import time
import logging
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import TransportError, RefreshError
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# We only request read-only access for 100% safe dry-run mode
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

# Fix 2 (Path Safety): Anchor to project root regardless of working directory.
# __file__ is execution/auth.py → .parent = execution/ → .parent = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_credentials():
    """
    Handles OAuth 2.0 flow, token caching, and automatic token refreshes.
    Returns valid credentials or exits on fatal errors.

    Fix 2: All file paths are resolved against PROJECT_ROOT (absolute).
    Fix 3: Token refresh distinguishes TransportError (transient → retry)
           from RefreshError (fatal → exit) instead of a bare except Exception.
    """
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

    # Fix 2: anchor env-var value against PROJECT_ROOT; handles both bare filenames
    # and absolute paths (pathlib replaces left side when right side is absolute)
    _secrets_raw = os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "client_secrets.json")
    client_secrets_file = PROJECT_ROOT / _secrets_raw
    token_file = PROJECT_ROOT / "token.json"   # Fix 2: was bare "token.json"
    creds = None

    # token.json stores access and refresh tokens; created on first successful auth.
    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load credentials from {token_file}: {e}")
            creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Credentials expired. Refreshing token...")

            # Fix 3: Classified retry — transient network errors retry with backoff;
            # revoked/expired refresh tokens exit immediately (no point retrying).
            max_retries = 3
            delay = 2.0
            for attempt in range(max_retries):
                try:
                    creds.refresh(Request())
                    break  # refresh succeeded
                except TransportError as e:
                    # Transient network failure — retry with exponential backoff
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Network error during token refresh "
                            f"(attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay:.0f}s..."
                        )
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.error(f"Token refresh failed after {max_retries} attempts: {e}")
                        creds = None
                except RefreshError as e:
                    # Fatal — refresh token revoked or expired; browser re-auth required
                    logger.error(f"Refresh token revoked or expired: {e}")
                    logger.error("Please delete token.json and re-authenticate.")
                    sys.exit(1)
                except Exception as e:
                    logger.error(f"Unexpected error during token refresh: {e}")
                    creds = None
                    break

        if not creds:
            logger.info(f"Starting new OAuth flow using {client_secrets_file}...")
            if not client_secrets_file.exists():
                logger.error(f"Client secrets file '{client_secrets_file}' not found.")
                logger.error("Please download it from Google Cloud Console and place it in the project root.")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets_file), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Persist credentials for the next run
        try:
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
                logger.info(f"Credentials saved to {token_file}")
        except IOError as e:
            logger.warning(f"Could not save credentials to file: {e}")

    return creds


if __name__ == "__main__":
    logger.info("Testing Authentication Flow...")
    try:
        credentials = get_credentials()
        if credentials and credentials.valid:
            logger.info("Authentication Successful!")
            logger.info(f"Token Scopes: {credentials.scopes}")
        else:
            logger.error("Authentication Failed: Credentials invalid.")
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
