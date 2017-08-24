import json

from mock import call, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from ...delivery.models import MatchReport
from ...utils.api import MatchingApi
from .base import MatchSetup

User = get_user_model()


class MatchPropertyTest(MatchSetup):

    def test_running_matching_sets_report_seen(self):
        self.create_match(self.user1, 'test1', alert=False)
        self.create_match(self.user2, 'test2', alert=False)
        for report in MatchReport.objects.all():
            self.assertFalse(report.seen)
        MatchingApi.run_matching()
        for report in MatchReport.objects.all():
            self.assertTrue(report.seen)

    def test_running_matching_erases_identifier(self):
        self.create_match(self.user1, 'test1', alert=False)
        self.create_match(self.user2, 'test2', alert=False)
        for report in MatchReport.objects.all():
            self.assertIsNotNone(report.identifier)
        MatchingApi.run_matching()
        for report in MatchReport.objects.all():
            self.assertIsNone(report.identifier)


class MatchDiscoveryTest(MatchSetup):

    def test_two_matching_reports_match(self):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        self.assert_matches_found_true()

    def test_non_matching_reports_dont_match(self):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test2')
        self.assert_matches_found_false()

    def test_matches_only_triggered_by_different_people(self):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user1, 'test1')
        self.assert_matches_found_false()

    def test_multiple_matches(self):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        self.create_match(self.user3, 'test1')
        self.create_match(self.user4, 'test1')
        self.assert_matches_found_true()


@patch('callisto_core.tests.utils.api.CustomMatchingApi.process_new_matches')
class MatchAlertingTest(MatchSetup):

    def test_existing_match_not_retriggered_by_same_reporter(
            self, mock_process):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        self.assertTrue(mock_process.called)

        mock_process.reset_mock()
        self.create_match(self.user2, 'test1')
        self.assertFalse(mock_process.called)

    def test_error_during_processing_means_match_not_seen(self, mock_process):
        mock_process.side_effect = [Exception('Boom!'), ()]
        try:
            self.create_match(self.user1, 'test1')
            self.create_match(self.user2, 'test1')
        except BaseException:
            pass
        self.assert_matches_found_false()

        mock_process.reset_mock()
        MatchingApi.run_matching()
        self.assert_matches_found_true()

    def test_triggers_new_matches_only(self, mock_process):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        self.assertTrue(mock_process.called)

        mock_process.reset_mock()
        self.create_match(self.user3, 'test2')
        self.assertFalse(mock_process.called)


@override_settings(CALLISTO_MATCHING_API=MatchingApi.DEFAULT_CLASS_PATH)
@patch('callisto_core.notification.api.CallistoCoreNotificationApi.send_match_notification')
class MatchNotificationTest(MatchSetup):

    def test_basic_email_case(self, mock_send_email):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        self.assertEqual(mock_send_email.call_count, 2)

    def test_multiple_email_case(self, mock_send_email):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user2, 'test1')
        self.create_match(self.user3, 'test1')
        self.create_match(self.user4, 'test1')
        self.assertEqual(mock_send_email.call_count, 4)

    def test_users_are_deduplicated(self, mock_send_email):
        self.create_match(self.user1, 'test1')
        self.create_match(self.user1, 'test1')
        self.assertFalse(mock_send_email.called)
        self.create_match(self.user2, 'test1')
        self.assertEqual(mock_send_email.call_count, 2)

    def test_doesnt_notify_on_reported_reports(self, mock_send_email):
        self.create_match(self.user1, 'test1')
        match_report = self.create_match(self.user2, 'test1', alert=False)
        match_report.report.submitted_to_school = timezone.now()
        match_report.report.save()
        MatchingApi.run_matching()
        self.assertEqual(mock_send_email.call_count, 1)