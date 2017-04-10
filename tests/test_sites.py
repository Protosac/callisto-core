from django.test import TestCase

from wizard_builder.models import QuestionPage


class SitePageTest(TestCase):

    def test_basic_created_question_page_comes_with_a_site(self):
        page = QuestionPage.objects.create()
        self.assertTrue(page.site.domain)
