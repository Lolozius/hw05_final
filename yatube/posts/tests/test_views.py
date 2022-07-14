import shutil
import tempfile
from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
OBJ_PAGE = 0
TEMP_DUMB_FIRST_PAGE = settings.POSTS_LIMIT
OPTIONAL_PAGE_RANGE = TEMP_DUMB_FIRST_PAGE + 3
TEMP_DUMB_SECOND_PAGE = OPTIONAL_PAGE_RANGE - TEMP_DUMB_FIRST_PAGE


class PostTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_name1',
                                            email='test1@gmail.ru',
                                            password='test_pass'),
            text='Тестовая запись для создания 1 поста',
            image=uploaded,
            group=Group.objects.create(
                title='Заголовок для 1 тестовой группы',
                slug='test_slug1')
        )

        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_name2',
                                            email='test2@gmail.ru',
                                            password='test_pass', ),
            text='Тестовая запись для создания 2 поста',
            image=uploaded,
            group=Group.objects.create(
                title='Заголовок для 2 тестовой группы',
                slug='test_slug2')
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='test_name2')
        self.authorized_client_2 = Client()
        self.user_2 = User.objects.get(username='test_name1')

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2.force_login(self.user_2)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}): 'posts/post_detail.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug1'}): 'posts/group_list.html',
            reverse('posts:new_post'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'test_name1'}): 'posts/profile.html'
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_template_delete(self):
        templates_page_names = {
            reverse(
                'posts:post_delete',
                kwargs={
                    'post_id': self.post.id}): 'posts/create_post.html',
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][OBJ_PAGE]
        post = PostTests.post
        post_text = first_object.text
        post_author = first_object.author
        post_group = first_object.group
        post_image = Post.objects.first().image
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_author, post.author)
        self.assertEqual(post_group, post.group)
        self.assertEqual(post_image, post.image)

    def test_group_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug2'}
                    )
        )
        first_object = response.context['group']
        second_object = response.context['page_obj'][OBJ_PAGE]
        post = PostTests.post
        obj_title = second_object.text
        group_title = first_object
        group_slug = first_object.slug
        post_image = Post.objects.first().image
        self.assertEqual(group_title, post.group)
        self.assertEqual(group_slug, post.group.slug)
        self.assertEqual(obj_title, post.text)
        self.assertEqual(post_image, post.image)

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    )
        )
        first_object = response.context['posted']
        post = PostTests.post
        post_text = first_object.text
        post_author = first_object.author
        post_group = first_object.group
        post_image = Post.objects.first().image
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_author, post.author)
        self.assertEqual(post_group, post.group)
        self.assertEqual(post_image, post.image)


    def assert_post_response(self, response):
        """Шаблон сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))
        self.assert_post_response(response)

    def test_post_edit_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={
                'post_id': self.post.id}))
        self.assert_post_response(response)

    def test_post_delete_correct_context(self):
        """Шаблон post_delete сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_delete',
            kwargs={
                'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        user = PostTests.post.author
        post = PostTests.post
        first_object = response.context['page_obj'][OBJ_PAGE]
        second_object = response.context['users']
        users_username = second_object
        post_text = first_object.text
        post_group = first_object.group
        post_image = Post.objects.first().image
        self.assertEqual(users_username, user)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_group, post.group)
        self.assertEqual(post_image, post.image)

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        post = Post.objects.create(
            author=self.user,
            text='Test_post22',
            group=Group.objects.get(slug='test_slug1')
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug2'})
        )
        first_object = response.context['page_obj'][OBJ_PAGE]
        self.assertNotIn(post.text, first_object.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='test_name',
            email='test@gmail.ru',
            password='test_pass', )
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug2',
            description='Тестовое описание')
        cls.posts = []
        for i in range(OPTIONAL_PAGE_RANGE):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_posts(self):
        list_urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test_slug2'}),
            reverse('posts:profile', kwargs={'username': 'test_name'}),
        )
        for tested_url in list_urls:
            response = self.guest_client.get(tested_url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list),
                TEMP_DUMB_FIRST_PAGE
            )

    def test_second_page_contains_three_posts(self):
        list_urls = {
            reverse('posts:index') + '?page=2': 'index',
            reverse(''
                    'posts:group_list',
                    kwargs={'slug': 'test_slug2'}) + '?page=2': 'group',
            reverse(
                'posts:profile',
                kwargs={'username': 'test_name'}) + '?page=2': 'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list),
                TEMP_DUMB_SECOND_PAGE
            )
