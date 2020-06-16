from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import Post, User, Group


class TestProfile(TestCase):
    def setUp(self):
        # Очищаем кэш
        cache.clear()
        # Создаем пользователя
        self.user = User.objects.create_user(
            username='vasya', email='vasya@vasya.com',
            password='12345')
        # Данные для регистрации
        self.signup_data = {
            'first_name': 'Петр',
            'last_name': 'Петров',
            'username': 'petr',
            'email': 'petr@petr.com',
            'password1': 'pwd_petr',
            'password2': 'pwd_petr'}

    def test_add_profile_page(self):
        """Проверяет, появилась ли страница пользователя после регистрации"""
        # Регистрируемся
        self.client.post(reverse('signup'), self.signup_data)
        # Логимся
        self.client.login(username='petr', password='pwd_petr')
        # Проверяем, появился ли новый пользователь
        response = self.client.get(
            reverse('profile', kwargs={'username': 'petr'}))
        self.assertEqual(response.status_code, 200)


class TestPostCreated(TestCase):
    def setUp(self):
        # Очищаем кэш
        cache.clear()
        # Создаем пользователя
        self.user = User.objects.create_user(
            username='vasya', password='12345')
        # Создаем пост
        self.post = Post.objects.create(text='Тестовый пост', author=self.user)

    def test_authorized_user_new_post(self):
        """Проверяет, что авторизованный пользователь
        может опубликовать пост"""
        # Логимся
        self.client.login(username='vasya', password='12345')
        # Создаем новый пост
        self.client.post(reverse('new_post'), kwargs={'text': 'Новый пост'})
        # Проверяем, появился ли пост после отправки формы
        post1 = Post.objects.first()
        self.assertEqual(post1.text, self.post.text)

    def test_unauthorized_user_new_post(self):
        """Проверяет, что неавторизованный пользователь не
        может опубликовать пост, и его редиректит
        на страницу авторизации"""
        # Попытка создать пост неавторизованным пользователем
        response = self.client.post(
            reverse('new_post'), {'text': 'Новый пост'})
        self.assertRedirects(
            response, '/auth/login/?next=/new/', status_code=302)

    def test_authorized_user_post_edit(self):
        """Проверяет, что авторизованный пользователь может
        отредактировать свой пост, и его содержимое изменится
        на всех связанных страницах
        """
        # Логимся
        self.client.login(username='vasya', password='12345')
        # Редактируем пост
        self.client.post(
            reverse('post_edit', kwargs={'username': 'vasya',
                                         'post_id': self.post.id}),
            {'text': 'Изменили тестовый пост'})
        # Проверка изменения поста на главной странице
        response = self.client.get(reverse('index'))
        self.assertContains(
            response, 'Изменили тестовый пост', count=1,
            status_code=200, msg_prefix='Пост не изменен на главной странице',
            html=False)
        # Проверка изменения на странице пользователя
        response = self.client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        self.assertContains(
            response, 'Изменили тестовый пост', count=1,
            status_code=200,
            msg_prefix='Пост не изменен на странице пользователя', html=False)
        # Проверка изменения на странице поста
        response = self.client.get(
            reverse('post_view', kwargs={
                'username': self.user.username, 'post_id': self.post.id}))
        self.assertContains(
            response, 'Изменили тестовый пост', count=1,
            status_code=200, msg_prefix='Пост не изменен на странице поста',
            html=False)


class TestPostRender(TestCase):
    def setUp(self):
        # Очищаем кэш
        cache.clear()
        # Создаем пользователя
        self.user = User.objects.create_user(
            username='vasya', password='12345')
        # Создаем пост
        self.post = Post.objects.create(text='Тестовый пост', author=self.user)

    def test_post_add_everywhere(self):
        """Проверяет, что опубликовынный пост появляется
        на всех связанных страницах"""
        # Пост на главной странице
        response = self.client.get(reverse('index'))
        self.assertContains(
            response, 'Тестовый пост', count=1,
            status_code=200, msg_prefix='Пост не найден на главной странице',
            html=False)
        # Пост на странице автора
        self.client.login(username='vasya', password='12345')
        response = self.client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        self.assertContains(
            response, 'Тестовый пост', count=1,
            status_code=200,
            msg_prefix='Пост не найден на странице пользователя', html=False)
        # Пост на стронице поста
        response = self.client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        self.assertContains(
            response, 'Тестовый пост', count=1,
            status_code=200, msg_prefix='Пост не найден на странице поста',
            html=False)


class TestImage(TestCase):
    def setUp(self):
        # Очищаем кэш
        cache.clear()
        # Создаем пользователя
        self.user = User.objects.create_user(
            username='vasya', email='vasya@vasya.com', password='12345')
        # Создаем группу
        self.group = Group.objects.create(
            title='Group', slug='grp_test', description='desc')
        # Логинемся
        self.client.login(username='vasya', password='12345')
        # Создаем пост с картинкой
        with open('media/posts/test.jpg', 'rb') as f_obj:
            self.client.post(
                reverse('new_post'),
                {'text': 'Text', 'image': f_obj,
                 'group': self.group.id})

    def test_image_everywhere(self):
        """Проверяет, что картинка есть на всех
        связанных страницах"""
        # Ищем картинку на главной странице
        response = self.client.get(reverse('index'))
        self.assertContains(
            response, '<img', status_code=200, count=1,
            msg_prefix='Тэг не найден на главной странице',
            html=False)
        # На странице поста
        response = self.client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        self.assertContains(
            response, '<img', status_code=200, count=1,
            msg_prefix='Тэг не найден на странице профиля',
            html=False)
        # На странице группы
        response = self.client.get(
            reverse('group_post', kwargs={'slug': 'grp_test'}))
        self.assertContains(
            response, '<img', status_code=200, count=1,
            msg_prefix='Тэг не найден на странице группы',
            html=False)

    def test_wrong_format_file(self):
        """Проверяет защиту от загрузки файлов
        неправильных форматов"""
        with open('requirements.txt', 'rb') as f_obj:
            self.client.post(
                reverse('new_post'),
                {'text': 'Тест картинки с неправильным форматом',
                 'image': f_obj})
        response = self.client.get(reverse('index'))
        self.assertNotContains(
            response, 'Тест картинки с неправильным форматом',
            status_code=200, msg_prefix='Тэг найден, а не должен', html=False)


class TestCache(TestCase):
    def setUp(self):
        self.client.get(reverse('index'))
        user = User.objects.create_user(
            username="vasya", email="vasya@vasya.com", password="12345")
        self.client.login(username='vasya', password='12345')
        self.client.post(reverse('new_post'), {'text': 'Тест кэша'})

    def test_cache(self):
        response = self.client.get(reverse('index'))
        self.assertNotContains(
            response, 'Тест кэша',
            status_code=200, msg_prefix='Пост найден, а не должен', html=False)
        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(
            response, 'Тест кэша',
            status_code=200, count=1, msg_prefix='Пост не найден', html=False)


class TestFollow(TestCase):
    def setUp(self):
        # Очищаем кэш
        cache.clear()
        # Создаем пользователей
        self.user1 = User.objects.create_user(
            username='vasya', email='vasya@vasya.com',
            password='12345')
        self.user2 = User.objects.create_user(
            username='ivan', email='ivan@ivan.com',
            password='12345')
        self.user3 = User.objects.create_user(
            username='petr', email='petr@petr.com',
            password='12345')
        # Логимся
        self.client.login(username='vasya', password='12345')
        # Создаем пост
        self.post = Post.objects.create(
            text='Тест подписок', author=self.user3)

    def test_authorized_follow_unfollow(self):
        """Проверяет, что авторизованный пользователь может
        подписываться на других пользователей и
        удалять их из подписок"""
        # Подписываемся
        self.client.get(
            reverse('profile_follow', kwargs={'username': self.user2}))
        response = self.client.get(
            reverse('profile', kwargs={'username': self.user1}))
        self.assertEqual(response.context["following"], False)
        # Отписываемся
        self.client.get(reverse('profile_unfollow',
                                kwargs={'username': self.user2}))
        response = self.client.get(
            reverse('profile', kwargs={'username': self.user1}))
        self.assertEqual(response.context["following"], 0)

    def test_follow_posts_feed(self):
        """Проверяет, что новая запись пользователя появляется
        в ленте тех, кто на него подписан и не появляется
        в ленте тех, кто не подписан на него"""
        # Подписываемся и проверяем наличие поста в ленте
        self.client.get(
            reverse('profile_follow', kwargs={'username': self.user3}))
        response = self.client.get(reverse('follow_index'))
        self.assertContains(
            response, 'Тест подписок', status_code=200,
            count=1, msg_prefix='Пост не найден',
            html=False)
        # Выходим из аккаунта и проверяем ленту
        self.client.logout()
        # Очищаем кэш
        cache.clear()
        self.client.login(username='ivan', password='12345')
        response = self.client.get(reverse('follow_index'))
        self.assertNotContains(
            response, 'Тест подписок', status_code=200,
            msg_prefix='Пост найден, а не должен',
            html=False)


class TestComment(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='vasya',
                                             password=12345)
        self.text = 'Тестовый пост'
        self.post = Post.objects.create(
            text=self.text, author=self.user)

        self.commenting_user = User.objects.create_user(
            username='ivan',
            password=12345)
        self.comment_text = 'Тестовый коммент'

    def test_auth_user_commenting(self):
        """Залогиненный юзер не может оставить комментарий"""
        self.client.force_login(self.commenting_user)
        response = self.client.post(
            reverse('add_comment', kwargs={'username': self.user.username,
                                           'post_id': self.post.pk}),
            {'text': self.comment_text}, follow=True)
        self.assertContains(response, self.comment_text)

    def test_anon_user_commenting(self):
        """Незалогиненный юзер не может оставить комментарий"""
        response = self.client.post(
            reverse('add_comment', kwargs={'username': self.user.username,
                                           'post_id': self.post.pk}),
            {'text': self.comment_text}, follow=True)
        self.assertNotContains(response, self.comment_text)
