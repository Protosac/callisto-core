from django.test import TestCase

from callisto_core.wizard_builder import managers


class FormSerializationTest(TestCase):
    manager = managers.FormManager
    fixtures = [
        'wizard_builder_data',
    ]
    expected_data = [{
        'descriptive_text': 'answer wisely',
        'field_id': 'question_2',
        'id': 2,
        'page': 2,
        'position': 0,
        'question_text': 'do androids dream of electric sheep?',
        'text': 'do androids dream of electric sheep?',
        'type': 'singlelinetext',
        'choices': [],
        'skip_eval': True,
    }]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        form = cls.manager.get_form_models()[1]
        cls.actual_data = form.serialized

    def test_same_size(self):
        actual_data = self.actual_data
        expected_data = self.expected_data
        self.assertEqual(
            len(actual_data),
            len(expected_data),
        )

    def test_same_questions(self):
        actual_data = self.actual_data
        expected_data = self.expected_data
        for index, expected_question in enumerate(expected_data):
            actual_question = actual_data[index]
            self.assertEqual(
                actual_question,
                expected_question,
            )

    def test_eval_set_true(self):
        question = self.manager.get_form_models()[1].serialized[0]
        self.assertEqual(
            question['text'],
            'do androids dream of electric sheep?')
        self.assertTrue(question['skip_eval'])

    def test_eval_set_false(self):
        question = self.manager.get_form_models()[0].serialized[1]
        self.assertEqual(
            question['text'],
            'eat it now???')
        self.assertFalse(question['skip_eval'])

    def test_eval_set_null(self):
        question = self.manager.get_form_models()[2].serialized[0]
        self.assertEqual(
            question['text'],
            'whats on the radios?')
        self.assertTrue(question['skip_eval'])
