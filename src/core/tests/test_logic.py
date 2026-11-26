__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import uuid
from mock import patch

from django.shortcuts import reverse
from django.test import TestCase, override_settings

from core import logic
from utils import shared
from utils.testing import helpers


class TestLogic(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.request = helpers.get_request(
            press=cls.press,
            journal=cls.journal_one,
        )
        cls.inactive_user = helpers.create_user("zlwdi6frbtlh4gditdir@example.org")
        cls.inactive_user.is_active = False
        cls.inactive_user.confirmation_code = "8bd3cdc9-1c3c-4ec9-99bc-9ea0b86a3c55"
        cls.inactive_user.clean()
        cls.inactive_user.save()

        # A decoded next URL
        cls.next_url_raw = "/target/page/?q=a"

        # An encoded next URL
        cls.next_url_encoded = "/target/page/%3Fq%3Da"

    def test_render_nested_settings(self):
        expected_rendered_setting = '<p>For help with Janeway, contact <a href="mailto:--No support email set--">--No support email set--</a>.</p>'
        rendered_setting = logic.render_nested_setting(
            "support_contact_message_for_staff",
            "general",
            self.request,
            nested_settings=[("support_email", "general")],
        )
        self.assertEqual(expected_rendered_setting, rendered_setting)

    @patch("core.logic.reverse")
    def test_reverse_with_next_in_kwarg(self, mock_reverse):
        mock_reverse.return_value = "/my/path/?my=params"
        reversed_url = logic.reverse_with_next(
            "/test/",
            next_url=self.next_url_raw,
        )
        self.assertIn(self.next_url_encoded, reversed_url)

    @patch("core.logic.reverse")
    def test_reverse_with_next_no_next(self, mock_reverse):
        mock_reverse.return_value = "/my/url/?my=params"
        reversed_url = logic.reverse_with_next("/test/", "")
        self.assertEqual(mock_reverse.return_value, reversed_url)

    @patch("core.logic.reverse")
    def test_reverse_with_query(self, mock_reverse):
        mock_reverse.return_value = "/my/url/?my=params"
        reversed_url = logic.reverse_with_query(
            "/test/",
            query_params={
                "important": "stuff",
            },
        )
        self.assertIn("important=stuff", reversed_url)

    def test_get_confirm_account_url(self):
        url = logic.get_confirm_account_url(
            self.request,
            self.inactive_user,
            next_url=self.next_url_raw,
        )
        self.assertIn(
            f"/register/step/2/8bd3cdc9-1c3c-4ec9-99bc-9ea0b86a3c55/?next={self.next_url_encoded}",
            url,
        )


class TestLoginAttemptLockout(TestCase):
    def _request(self, user_agent):
        from django.test import RequestFactory

        return RequestFactory().post(
            "/login/",
            REMOTE_ADDR="203.0.113.7",
            HTTP_USER_AGENT=user_agent,
        )

    def test_user_agent_change_does_not_reset_counter(self):
        logic.add_failed_login_attempt(self._request("UA-one"), "User@Example.org")
        logic.add_failed_login_attempt(self._request("UA-one"), "user@example.org")
        logic.add_failed_login_attempt(self._request("UA-two"), "user@example.org")

        self.assertEqual(
            logic.check_for_bad_login_attempts(
                self._request("UA-three"), "user@example.org"
            ),
            3,
        )

    def test_counter_is_per_login(self):
        logic.add_failed_login_attempt(self._request("UA-one"), "a@example.org")

        self.assertEqual(
            logic.check_for_bad_login_attempts(self._request("UA-one"), "b@example.org"),
            0,
        )

    def test_successful_login_clears_only_its_login(self):
        logic.add_failed_login_attempt(self._request("UA-one"), "a@example.org")
        logic.add_failed_login_attempt(self._request("UA-one"), "b@example.org")

        logic.clear_bad_login_attempts(self._request("UA-two"), "a@example.org")

        self.assertEqual(
            logic.check_for_bad_login_attempts(self._request("UA-one"), "a@example.org"),
            0,
        )
        self.assertEqual(
            logic.check_for_bad_login_attempts(self._request("UA-one"), "b@example.org"),
            1,
        )


class TestClientIpTrust(TestCase):
    def _post(self, remote_addr, **headers):
        from django.test import RequestFactory

        return RequestFactory().post("/login/", REMOTE_ADDR=remote_addr, **headers)

    def test_proxy_peer_uses_x_real_ip(self):
        request = self._post("192.168.64.1", HTTP_X_REAL_IP="193.41.131.20")
        self.assertEqual(shared.get_ip_address(request), "193.41.131.20")

    def test_proxy_peer_ignores_spoofed_x_forwarded_for(self):
        request = self._post(
            "192.168.64.1",
            HTTP_X_FORWARDED_FOR="8.8.8.8",
            HTTP_X_REAL_IP="193.41.131.20",
        )
        self.assertEqual(shared.get_ip_address(request), "193.41.131.20")

    def test_public_peer_ignores_all_forwarded_headers(self):
        request = self._post(
            "93.184.216.34",
            HTTP_X_FORWARDED_FOR="8.8.8.8",
            HTTP_X_REAL_IP="8.8.4.4",
        )
        self.assertEqual(shared.get_ip_address(request), "93.184.216.34")

    def test_private_peer_without_x_real_ip_falls_back_to_peer(self):
        request = self._post("192.168.64.1", HTTP_X_FORWARDED_FOR="8.8.8.8")
        self.assertEqual(shared.get_ip_address(request), "192.168.64.1")

class TestLoginFailureLog(TestCase):
    def test_login_form_does_not_log_field_repr(self):
        from core.forms import LoginForm

        with patch("core.forms.forms.logger") as logger_mock:
            LoginForm(bad_logins=2)

        logger_mock.warning.assert_not_called()

    def test_failed_login_logs_ip_and_user(self):
        from django.test import RequestFactory

        request = RequestFactory().post(
            "/login/",
            REMOTE_ADDR="203.0.113.7",
            HTTP_USER_AGENT="UA-log",
        )
        with patch("core.logic.logger") as logger_mock:
            logic.add_failed_login_attempt(request, "user@example.org")

        logger_mock.warning.assert_called_once_with(
            "[FAILED_LOGIN][IP:203.0.113.7][USER:user@example.org]"
        )