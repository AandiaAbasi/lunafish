"""Regression coverage for international mobile payment eligibility."""
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from api.region_policy import is_international_request


class InternationalRegionPolicyTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def international(self, region='', timezone=''):
        request = self.factory.get(
            '/api/home/',
            HTTP_X_CLIENT_REGION=region,
            HTTP_X_CLIENT_TIMEZONE=timezone,
        )
        return is_international_request(request)

    def test_foreign_region_and_timezone_are_international(self):
        self.assertTrue(self.international('DE', 'Europe/Berlin'))
        self.assertTrue(self.international('US', 'America/New_York'))

    def test_iran_region_or_tehran_timezone_keep_paid_mode(self):
        self.assertFalse(self.international('IR', 'Europe/Berlin'))
        self.assertFalse(self.international('DE', 'Asia/Tehran'))
        self.assertFalse(self.international('IR', 'Asia/Tehran'))

    def test_incomplete_or_invalid_region_fails_closed(self):
        self.assertFalse(self.international('', 'Europe/Berlin'))
        self.assertFalse(self.international('DE', ''))
        self.assertFalse(self.international('DE', 'Not/A_Timezone'))
        self.assertFalse(self.international('??', 'Europe/Berlin'))
