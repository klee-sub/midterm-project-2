from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Post


class PostApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='api-user', password='test-password'
        )

    def test_list_and_detail(self):
        post = Post.objects.create(
            author=self.user, title='First post', text='First text'
        )

        response = self.client.get(reverse('post-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], post.title)

        response = self.client.get(reverse('post-detail', args=[post.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], post.text)

    def test_create_update_delete(self):
        response = self.client.post(
            reverse('post-list'),
            {'author': self.user.pk, 'title': 'New post', 'text': 'New text'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_id = Post.objects.get(title='New post').pk
        post_url = reverse('post-detail', args=[post_id])

        response = self.client.put(
            post_url,
            {'author': self.user.pk, 'title': 'Updated post', 'text': 'Updated text'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated post')

        response = self.client.delete(post_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=post_id).exists())


class BlogViewTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='view-user', password='test-password'
        )
        self.client.force_login(self.user)

    def test_list_detail_and_js(self):
        post = Post.objects.create(
            author=self.user,
            title='Published post',
            text='Published text',
            published_date=timezone.now(),
        )

        response = self.client.get(reverse('post_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, post.title)

        response = self.client.get(reverse('post_detail', args=[post.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, post.text)

        response = self.client.get(reverse('js_test'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_new_post(self):
        response = self.client.get(reverse('post_new'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse('post_new'), {'title': '', 'text': ''}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse('post_new'), {'title': 'New post', 'text': 'New text'}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(Post.objects.filter(title='New post').exists())

    def test_edit_post(self):
        post = Post.objects.create(
            author=self.user, title='Old title', text='Old text'
        )

        response = self.client.get(reverse('post_edit', args=[post.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse('post_edit', args=[post.pk]), {'title': '', 'text': ''}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse('post_edit', args=[post.pk]),
            {'title': 'Updated title', 'text': 'Updated text'},
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Updated title')

    def test_publish_and_string(self):
        post = Post.objects.create(
            author=self.user, title='Draft title', text='Draft text'
        )
        self.assertEqual(str(post), 'Draft title')
        self.assertIsNone(post.published_date)
        post.publish()
        post.refresh_from_db()
        self.assertIsNotNone(post.published_date)
