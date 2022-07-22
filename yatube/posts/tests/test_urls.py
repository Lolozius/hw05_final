from http import HTTPStatus
from urllib.parse import urljoin

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_name1',
                                            email='test@gmail.ru',
                                            password='test_pass'),
            text='Тестовая запись для создания нового поста',
        )
        cls.not_author = User.objects.create_user(
            username="not_author_post", password="321"
        )
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug'
        )


    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент c автором
        user_author = self.post.author
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(user_author)
        user_no_author = self.not_author
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(user_no_author)

    def test_home_and_group(self):
        """Страницы доступны всем пользователям"""
        url_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}),
            reverse('posts:profile', kwargs={'username': 'test_name1'}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        )
        for adress in url_names:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_for_authorized_non_author(self):
        """Страница post_edit, post_delete, не доступна не автору поста."""
        urls_names = (
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            reverse('posts:post_delete', kwargs={'post_id': self.post.id}),
        )
        for adress in urls_names:
            with self.subTest(adress=adress):
                response = self.authorized_client_not_author.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_for_comments_authorized_user(self):
        """
        Коментарии доступны только авторизированному
        пользователю
        """
        urls_names = (reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id})
        )
        response = self.authorized_client_not_author.get(urls_names)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_for_authorized_user(self):
        """
        Страница new_post, post_edit, доступна авторизированному.
        пользователлю
        """
        urls_name = (
            reverse('posts:new_post'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        )
        for adress in urls_name:
            with self.subTest(adress=adress):
                response = self.authorized_client_author.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_url(self):
        """без авторизации приватные URL недоступны"""
        url_names = (
            reverse('posts:new_post'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            reverse('posts:post_delete', kwargs={'post_id': self.post.pk})
        )
        for adress in url_names:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_redirect_anonymous_on_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get(reverse('posts:new_post'))
        url = urljoin(reverse('login'), '?next=/create/')
        self.assertRedirects(response, url)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug'}): 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}): 'posts/post_detail.html',
            reverse('posts:new_post'): 'posts/create_post.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'test_name1'}): 'posts/profile.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
        }

        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client_author.get(template)
                self.assertTemplateUsed(response, url)

    def test_urls_edit_page_authorized_user_but_not_author(self):
        """Проверяем, редирект если пользователь не является
         автором поста
         """
        response = self.authorized_client_not_author.get(
            f"/posts/{TaskURLTests.post.id}/edit/"
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f"/posts/{TaskURLTests.post.id}/"
        )

    def test_page_404(self):
        response = self.guest_client.get('/qwerty12345/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
