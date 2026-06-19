"""Unit tests for the normal-text to Band message transformation."""
import unittest

from proofgate.chat_entry import ChatEntryError, prepare_intake_message


class TestPrepareIntakeMessage(unittest.TestCase):

    def test_normal_text_gets_single_intake_prefix(self):
        result = prepare_intake_message(
            "Review this proposed change.",
            intake_participant_id="uuid-123",
        )
        self.assertEqual(result.band_content, "@itz1508/intake Review this proposed change.")
        self.assertEqual(result.display_text, "Review this proposed change.")

    def test_existing_prefix_is_not_duplicated(self):
        result = prepare_intake_message(
            "@itz1508/intake Review this request.",
            intake_participant_id="uuid-123",
        )
        self.assertEqual(result.band_content, "@itz1508/intake Review this request.")
        self.assertNotIn("@itz1508/intake @itz1508/intake", result.band_content)

    def test_prefix_without_at_sign_is_normalized(self):
        result = prepare_intake_message(
            "itz1508/intake Do something.",
            intake_participant_id="uuid-123",
        )
        self.assertEqual(result.band_content, "@itz1508/intake Do something.")

    def test_empty_input_rejected(self):
        with self.assertRaises(ChatEntryError):
            prepare_intake_message("", intake_participant_id="uuid-123")

    def test_whitespace_only_rejected(self):
        with self.assertRaises(ChatEntryError):
            prepare_intake_message("   \t\n  ", intake_participant_id="uuid-123")

    def test_input_trimmed(self):
        result = prepare_intake_message(
            "  Hello agent  ",
            intake_participant_id="uuid-123",
        )
        self.assertEqual(result.display_text, "Hello agent")

    def test_exceeds_max_length_rejected(self):
        long_text = "x" * 2001
        with self.assertRaises(ChatEntryError):
            prepare_intake_message(long_text, intake_participant_id="uuid-123")

    def test_missing_participant_id_rejected(self):
        with self.assertRaises(ChatEntryError):
            prepare_intake_message("Hello", intake_participant_id="")

    def test_mention_metadata_included(self):
        result = prepare_intake_message(
            "Test message",
            intake_handle="itz1508/intake",
            intake_participant_id="abc-def-ghi",
            intake_name="Intake Agent",
        )
        self.assertEqual(len(result.mentions), 1)
        self.assertEqual(result.mentions[0]["id"], "abc-def-ghi")
        self.assertEqual(result.mentions[0]["handle"], "itz1508/intake")
        self.assertEqual(result.mentions[0]["name"], "Intake Agent")

    def test_non_string_input_rejected(self):
        with self.assertRaises(ChatEntryError):
            prepare_intake_message(123, intake_participant_id="uuid")  # type: ignore

    def test_target_handle_set(self):
        result = prepare_intake_message(
            "Hello",
            intake_handle="itz1508/intake",
            intake_participant_id="uuid-123",
        )
        self.assertEqual(result.target_handle, "itz1508/intake")

    def test_credentials_never_in_output(self):
        result = prepare_intake_message(
            "Hello",
            intake_participant_id="uuid-123",
        )
        self.assertNotIn("API_KEY", result.band_content)
        self.assertNotIn("API_KEY", result.display_text)
        for m in result.mentions:
            self.assertNotIn("API_KEY", str(m))


if __name__ == "__main__":
    unittest.main()
