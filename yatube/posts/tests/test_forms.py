from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test_name')
        cls.group = Group.objects.create(
            title='Test group',
            description='Test description',
            slug='test_group'
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_form(self):
        """При отправке валидной формы создаётся новая запись в бд"""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.first()
        self.assertEqual(form_data['text'], last_post.text)
        self.assertEqual(last_post.id, self.post.id + 1)
        self.assertEqual(last_post.author, self.post.author)
        self.assertEqual(self.group, last_post.group)

    def test_post_edit_form(self):
        """Происходит изменение поста post_id в базе данных."""
        form_data = {
            'text': 'Изменение прошло успешно',
            'group': self.group.id
        }
        posts_count = Post.objects.count()
        self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        edit = Post.objects.get(id=self.post.id)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(edit.text, form_data['text'])
        self.assertEqual(edit.author, self.post.author)
        self.assertEqual(self.group, edit.group)
