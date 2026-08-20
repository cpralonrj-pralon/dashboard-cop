import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import auth
from src.config import COORD_IDS, SUB_ADMIN_NAMES, can_view_fechamento_toa_sir


def _password_entry(password: str, *, must_change: bool = False) -> dict:
    hashed, salt = auth._hash_password(password)
    return {"hash": hashed, "salt": salt, "must_change": must_change}


class PasswordResetTest(unittest.TestCase):
    def test_batch_reset_changes_only_requested_subadmins(self):
        original = {
            "ADMIN": _password_entry("admin-secret"),
            "LUIZ": _password_entry("luiz-secret"),
            "VINICIUS": _password_entry("vinicius-secret"),
            "N5972428": _password_entry("analyst-secret"),
        }
        saved = {}

        def _capture(payload):
            saved.update(copy.deepcopy(payload))
            return True

        with (
            patch.object(auth, "_load_passwords", return_value=copy.deepcopy(original)),
            patch.object(auth, "_save_passwords", side_effect=_capture),
        ):
            count = auth.reset_user_passwords({"luiz", "VINICIUS", "INEXISTENTE"})

        self.assertEqual(2, count)
        self.assertEqual(original["ADMIN"], saved["ADMIN"])
        self.assertEqual(original["N5972428"], saved["N5972428"])
        for user_id in {"LUIZ", "VINICIUS"}:
            self.assertTrue(saved[user_id]["must_change"])
            expected_hash, _ = auth._hash_password(
                auth.DEFAULT_PASSWORD,
                saved[user_id]["salt"],
            )
            self.assertEqual(expected_hash, saved[user_id]["hash"])

    def test_batch_reset_reports_persistence_failure(self):
        passwords = {"LUIZ": _password_entry("old-password")}
        with (
            patch.object(auth, "_load_passwords", return_value=passwords),
            patch.object(auth, "_save_passwords", return_value=False),
        ):
            with self.assertRaises(RuntimeError):
                auth.reset_user_passwords({"LUIZ"})

    def test_all_configured_subadmins_are_valid_reset_targets(self):
        self.assertEqual(
            {"LUIZ", "VINICIUS", "N0150817", "N5768308", "TPAROLI"},
            COORD_IDS,
        )
        self.assertEqual(COORD_IDS, set(SUB_ADMIN_NAMES))
        self.assertTrue(all(SUB_ADMIN_NAMES.values()))


class FechamentoAccessTest(unittest.TestCase):
    def test_luiz_and_vinicius_cannot_view_fechamento(self):
        self.assertFalse(can_view_fechamento_toa_sir("LUIZ"))
        self.assertFalse(can_view_fechamento_toa_sir(" vinicius "))

    def test_other_profiles_keep_existing_fechamento_access(self):
        for user_id in {"ADMIN", "PRALON", "EVANDRO", "N0150817", "N5972428"}:
            self.assertTrue(can_view_fechamento_toa_sir(user_id))

    def test_excluded_source_is_removed_and_not_loaded_from_disk(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            uploads_dir = Path(temp_dir) / "uploads"
            uploads_dir.mkdir()
            (uploads_dir / "produtividade.xlsx").write_bytes(b"produtividade")
            (uploads_dir / "fechamento_toa_sir.xlsx").write_bytes(b"restrito")
            session = {"uploaded_fech_sir_bytes": b"sessao-anterior"}

            with (
                patch.object(auth.storage, "r2_available", return_value=False),
                patch.object(auth, "DATA_DIR", Path(temp_dir)),
                patch.object(auth, "UPLOADS_DIR", uploads_dir),
                patch.object(auth.st, "session_state", session),
            ):
                auth.load_saved_files_to_session(
                    excluded_keys={"uploaded_fech_sir_bytes"}
                )

            self.assertNotIn("uploaded_fech_sir_bytes", session)
            self.assertEqual(b"produtividade", session["uploaded_bytes"])


if __name__ == "__main__":
    unittest.main()
