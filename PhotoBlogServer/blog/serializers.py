from blog.models import Post, Comment, Tag
from rest_framework import serializers

class TagListField(serializers.ListField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            data = [item.strip() for item in data.split(',') if item.strip()]
        return super().to_internal_value(data)
    def to_representation(self, data):
        if hasattr(data, 'all'):
            data = data.all()
        return [str(item.name if hasattr(item, 'name') else item) for item in data]

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    class Meta:
        model = Comment
        fields = ('id', 'post', 'author', 'author_name', 'text', 'created_date')
        read_only_fields = ('author',)

class PostSerializer(serializers.ModelSerializer):
    tags = TagListField(child=serializers.CharField(max_length=40), required=False)
    comments = serializers.SerializerMethodField()
    class Meta:
        model = Post
        fields = ('id', 'author', 'title', 'text', 'created_date', 'published_date', 'image', 'tags', 'comments')
        read_only_fields = ('author',)
    def get_comments(self, obj):
        return CommentSerializer(obj.comments.select_related('author').all(), many=True).data
    def create(self, validated_data):
        names = validated_data.pop('tags', [])
        post = super().create(validated_data)
        post.tags.set([Tag.objects.get_or_create(name=name.strip())[0] for name in names if name.strip()])
        return post
    def update(self, instance, validated_data):
        names = validated_data.pop('tags', None)
        post = super().update(instance, validated_data)
        if names is not None:
            post.tags.set([Tag.objects.get_or_create(name=name.strip())[0] for name in names if name.strip()])
        return post
