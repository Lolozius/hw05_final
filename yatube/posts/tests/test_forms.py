import datetime
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            text='test comet',
            author=cls.user,
            post=cls.post,
            created=datetime.datetime.now()
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_posts_form(self):
        pass


    def test_create_post_form(self):
        """При отправке валидной формы создаётся новая запись в бд"""

        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
            'image': self.post.image
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
        self.assertEqual(form_data['image'], self.post.image)


    def test_post_edit_form(self):
        """Происходит изменение поста post_id в базе данных."""
        form_data = {
            'text': 'Изменение прошло успешно',
            'group': self.group.id,
            'image': self.post.image
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
        self.assertEqual(edit.text, self.post.text)
        self.assertEqual(edit.author, self.post.author)
        self.assertEqual(self.group, edit.group)
        self.assertEqual(form_data['image'], self.post.image)
