from django.db import models
from django.utils import timezone

class Tag(models.Model):
    name = models.CharField(max_length=40, unique=True)
    def __str__(self):
        return self.name

class Post(models.Model):
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)
    image = models.ImageField(upload_to='images/%Y/%m/%d/', default='images/default_error.png')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    def publish(self):
        self.published_date = timezone.now()
        self.save()
    def __str__(self):
        return self.title

class EnrollmentRequest(models.Model):
    STATUS_CHOICES = [('pending', '대기'), ('done', '완료'), ('failed', '실패')]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='enrollments')
    name = models.CharField(max_length=30)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.CharField(max_length=200, blank=True)
    requested_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f'{self.name} ({self.status})'

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    text = models.TextField(max_length=1000)
    created_date = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f'{self.author}: {self.text[:30]}'
