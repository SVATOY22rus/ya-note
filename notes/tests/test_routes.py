from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты маршрутов для приложения Notes."""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='slug-1',
            author=cls.author
        )

    def test_pages_availability_for_anonymous_user(self):
        """
        Главная страница, страницы входа и регистрации доступны анониму.
        """
        names = (
            ('notes:home', None),
            ('users:login', None),
            ('users:signup', None),
        )
        for name, args in names:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """
        Страницы списка заметок, добавления и успеха доступны
        авторизованному пользователю.
        """
        names = (
            'notes:list',
            'notes:add',
            'notes:success',
        )
        self.client.force_login(self.author)
        for name in names:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_author_and_reader(self):
        """
        Страницы заметки (просмотра, редактирования, удаления)
        доступны только автору. Для других - 404.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        names = (
            'notes:detail',
            'notes:edit',
            'notes:delete',
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in names:
                with self.subTest(user=user.username, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        Приватные страницы перенаправляют анонимного пользователя
        на страницу входа.
        """
        login_url = reverse('users:login')
        names = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
        )
        for name, args in names:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
