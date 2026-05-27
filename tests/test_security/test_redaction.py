"""Tests for governai.security.redaction.BasicPiiRedactor."""

import unittest

from governai.security.redaction import BasicPiiRedactor


class TestBasicPiiRedactorInit(unittest.TestCase):
    def setUp(self) -> None:
        self.redactor = BasicPiiRedactor()

    # ------------------------------------------------------------------
    # Null / empty
    # ------------------------------------------------------------------

    def test_none_input_returns_empty_string(self) -> None:
        self.assertEqual(self.redactor.redact(None), "")

    def test_empty_string_returns_empty_string(self) -> None:
        self.assertEqual(self.redactor.redact(""), "")

    def test_plain_text_unchanged(self) -> None:
        text = "Hello, world! This text has no sensitive data."
        self.assertEqual(self.redactor.redact(text), text)

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------

    def test_email_redacted(self) -> None:
        result = self.redactor.redact("Contact me at user@example.com for details.")
        self.assertNotIn("user@example.com", result)
        self.assertIn("[REDACTED_EMAIL]", result)

    def test_multiple_emails_all_redacted(self) -> None:
        result = self.redactor.redact("a@b.com and c@d.org are contacts.")
        self.assertNotIn("a@b.com", result)
        self.assertNotIn("c@d.org", result)

    # ------------------------------------------------------------------
    # Phone
    # ------------------------------------------------------------------

    def test_us_phone_redacted(self) -> None:
        result = self.redactor.redact("Call me at 555-867-5309.")
        self.assertNotIn("555-867-5309", result)
        self.assertIn("[REDACTED_PHONE]", result)

    def test_phone_with_parens_redacted(self) -> None:
        result = self.redactor.redact("(555) 867-5309")
        self.assertNotIn("867-5309", result)

    # ------------------------------------------------------------------
    # Credit card
    # ------------------------------------------------------------------

    def test_credit_card_redacted(self) -> None:
        result = self.redactor.redact("Card: 4111 1111 1111 1111")
        self.assertNotIn("4111 1111 1111 1111", result)
        self.assertIn("[REDACTED_CARD]", result)

    def test_dashed_credit_card_redacted(self) -> None:
        result = self.redactor.redact("4111-1111-1111-1111")
        self.assertNotIn("4111-1111-1111-1111", result)

    # ------------------------------------------------------------------
    # Bearer token
    # ------------------------------------------------------------------

    def test_bearer_token_redacted(self) -> None:
        result = self.redactor.redact("Authorization: Bearer eyJhbGciOiJSUzI1NiJ9.payload.signature")
        self.assertNotIn("eyJhbGciOiJSUzI1NiJ9", result)
        self.assertIn("Bearer [REDACTED_TOKEN]", result)

    def test_bearer_case_insensitive(self) -> None:
        result = self.redactor.redact("bearer some-token-value-here")
        self.assertIn("[REDACTED_TOKEN]", result)

    # ------------------------------------------------------------------
    # API key
    # ------------------------------------------------------------------

    def test_api_key_query_param_redacted(self) -> None:
        result = self.redactor.redact("api_key=ABCDEFGHIJKLMNOP1234567890")
        self.assertNotIn("ABCDEFGHIJKLMNOP1234567890", result)
        self.assertIn("[REDACTED_API_KEY]", result)

    def test_apikey_colon_redacted(self) -> None:
        result = self.redactor.redact("apikey: my-secret-key-value1234567890")
        self.assertIn("[REDACTED_API_KEY]", result)

    # ------------------------------------------------------------------
    # Password / secret
    # ------------------------------------------------------------------

    def test_password_field_redacted(self) -> None:
        result = self.redactor.redact("password=myS3cretP@ss")
        self.assertNotIn("myS3cretP@ss", result)
        self.assertIn("[REDACTED_SECRET]", result)

    def test_secret_field_redacted(self) -> None:
        result = self.redactor.redact("client_secret=abcd1234")
        self.assertIn("[REDACTED_SECRET]", result)

    # ------------------------------------------------------------------
    # Connection strings
    # ------------------------------------------------------------------

    def test_sql_connection_string_redacted(self) -> None:
        conn = "Server=myserver;Database=mydb;User Id=admin;Password=secret;"
        result = self.redactor.redact(conn)
        self.assertNotIn("myserver", result)
        self.assertIn("[REDACTED_CONNECTION_STRING]", result)

    def test_azure_storage_connection_string_redacted(self) -> None:
        conn = (
            "DefaultEndpointsProtocol=https;AccountName=myaccount;"
            "AccountKey=ABC123==;EndpointSuffix=core.windows.net"
        )
        result = self.redactor.redact(conn)
        self.assertNotIn("ABC123==", result)
        self.assertIn("[REDACTED_CONNECTION_STRING]", result)

    # ------------------------------------------------------------------
    # Idempotency — second pass should be stable
    # ------------------------------------------------------------------

    def test_redacted_output_is_stable(self) -> None:
        text = "user@example.com and Bearer secret-token"
        once = self.redactor.redact(text)
        twice = self.redactor.redact(once)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
