import re
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Post, Comment, EnrollmentRequest
from .forms import PostForm
from rest_framework import mixins, permissions, viewsets
try:
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
except ImportError:
    async_to_sync = None
    get_channel_layer = lambda: None
from .serializers import PostSerializer, CommentSerializer, EnrollmentSerializer

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
    can_enroll = request.user.is_staff and post.tags.filter(name='auth:unknown').exists()
    return render(request, 'blog/post_detail.html', {'post': post, 'can_enroll': can_enroll})

@staff_member_required
@require_POST
def post_enroll(request, pk):
    post = get_object_or_404(Post, pk=pk)
    name = request.POST.get('name', '').strip()
    if not re.fullmatch(r'[\w-]{1,30}', name) or name in ('unknown', 'no-face'):
        messages.error(request, '이름은 30자 이내의 문자, 숫자, _, - 만 사용할 수 있습니다.')
    elif request.POST.get('consent') != 'on':
        messages.error(request, '얼굴 등록에는 본인 동의 확인이 필요합니다.')
    else:
        EnrollmentRequest.objects.create(post=post, name=name, requested_by=request.user)
        messages.success(request, '등록을 요청했습니다.')
    return redirect('post_detail', pk=pk)

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
    queryset = Post.objects.order_by('-published_date', '-id').prefetch_related('tags', 'comments__author')
    serializer_class = PostSerializer
    def _broadcast(self, change, post_id):
        if async_to_sync is not None:
            layer = get_channel_layer()
            if layer is not None:
                async_to_sync(layer.group_send)('posts', {'type': 'post_changed', 'change': change, 'post_id': post_id})
    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)
        self._broadcast('created', post.pk)

    def perform_update(self, serializer):
        post = serializer.save()
        self._broadcast('updated', post.pk)

class Comments(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('author').all()
    serializer_class = CommentSerializer
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class Enrollments(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = EnrollmentRequest.objects.select_related('post').order_by('id')
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['get', 'patch', 'head', 'options']
    def get_queryset(self):
        status = self.request.query_params.get('status')
        return self.queryset.filter(status=status) if status else self.queryset
