from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    tags = forms.CharField(required=False, help_text='쉼표로 구분')
    class Meta:
        model = Post
        fields = ('title', 'text', 'image', 'tags')
    def save(self, commit=True):
        post = super().save(commit=commit)
        if commit:
            self.save_m2m()
        return post
    def save_m2m(self):
        names = [name.strip() for name in self.cleaned_data.get('tags', '').split(',') if name.strip()]
        from .models import Tag
        self.instance.tags.set([Tag.objects.get_or_create(name=name)[0] for name in names])
