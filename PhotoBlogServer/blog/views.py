from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Post, Comment
from .forms import PostForm
from rest_framework import viewsets
try:
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
except ImportError:
    async_to_sync = None
    get_channel_layer = lambda: None
from .serializers import PostSerializer, CommentSerializer

def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).prefetch_related('tags').order_by('-published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post.objects.prefetch_related('tags', 'comments__author'), pk=pk)
    if request.method == 'POST' and request.user.is_authenticated:
        text = request.POST.get('comment', '').strip()
        if text:
            Comment.objects.create(post=post, author=request.user, text=text)
            return redirect('post_detail', pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})

def post_new(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid() and request.user.is_authenticated:
            post = form.save(commit=False); post.author = request.user; post.published_date = timezone.now(); post.save()
            form.save_m2m(); return redirect('post_detail', pk=post.pk)
    else: form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})

def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid() and request.user.is_authenticated:
            post = form.save(commit=False); post.author = request.user; post.published_date = timezone.now(); post.save()
            form.save_m2m(); return redirect('post_detail', pk=post.pk)
    else: form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})

def js_test(request): return render(request, 'blog/js_test.html', {})

class BlogImages(viewsets.ModelViewSet):
    queryset = Post.objects.all().prefetch_related('tags', 'comments__author')
    serializer_class = PostSerializer
    def _broadcast(self, change, post_id):
        if async_to_sync is not None:
            layer = get_channel_layer()
            if layer is not None:
                async_to_sync(layer.group_send)('posts', {'type': 'post_changed', 'change': change, 'post_id': post_id})
    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else get_user_model().objects.get(username='klee')
        post = serializer.save(author=user)
        self._broadcast('created', post.pk)

    def perform_update(self, serializer):
        post = serializer.save()
        self._broadcast('updated', post.pk)

class Comments(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('author').all()
    serializer_class = CommentSerializer
    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else get_user_model().objects.get(username='klee')
        serializer.save(author=user)
