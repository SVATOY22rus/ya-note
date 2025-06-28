from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    """Тесты контента для приложения Notes."""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='note-1',
            author=cls.author,
        )

    def test_notes_list_for_different_users(self):
        """
        В список заметок одного пользователя попадают только его заметки,
        а чужие - нет.
        """
        users_and_expected_results = (
            (self.author, True),
            (self.reader, False),
        )
        for user, note_in_list in users_and_expected_results:
            self.client.force_login(user)
            with self.subTest(user=user.username, note_in_list=note_in_list):
                response = self.client.get(reverse('notes:list'))
                object_list = response.context.get('object_list')
                self.assertEqual((self.note in object_list), note_in_list)

    def test_pages_contain_form(self):
        """
        На страницы создания и редактирования заметки передаётся форма.
        """
        self.client.force_login(self.author)
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
