from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    """Тесты создания заметок."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Тестовый юзер')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.url = reverse('notes:add')
        cls.form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Тестовый текст',
            'slug': 'test-slug'
        }

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        notes_count_before = Note.objects.count()
        self.client.post(self.url, data=self.form_data)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)

    def test_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        notes_count_before = Note.objects.count()
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before + 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.user)

    def test_not_unique_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        self.auth_client.post(self.url, data=self.form_data)
        notes_count_before = Note.objects.count()
        response = self.auth_client.post(self.url, data=self.form_data)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)
        form_from_context = response.context['form']
        self.assertIn('slug', form_from_context.errors)
        expected_error_text = self.form_data['slug'] + WARNING
        self.assertEqual(
            form_from_context.errors['slug'], [expected_error_text]
        )

    def test_empty_slug(self):
        """Если slug не заполнен, он формируется автоматически из заголовка."""
        form_data = self.form_data.copy()
        form_data.pop('slug')
        notes_count_before = Note.objects.count()
        response = self.auth_client.post(self.url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before + 1)
        new_note = Note.objects.get()
        expected_slug = slugify(form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    """Тесты редактирования и удаления заметок."""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок', text='Текст', slug='note-slug', author=cls.author
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {
            'title': 'Новый заголовок', 'text': 'Новый текст', 'slug': 'new-slug'
        }

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_reader_cant_edit_note(self):
        """Другой пользователь не может редактировать чужую заметку."""
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        notes_count_before = Note.objects.count()
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before - 1)

    def test_reader_cant_delete_note(self):
        """Другой пользователь не может удалить чужую заметку."""
        notes_count_before = Note.objects.count()
        response = self.reader_client.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)
