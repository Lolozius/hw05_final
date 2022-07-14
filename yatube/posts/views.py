from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post
from .utils import func_paginator

User = get_user_model()


def index(request):
    """
     В переменную posts будет сохранена выборка из 10 объектов модели Post,
     отсортированных по полю pub_date по убыванию
     (от больших значений к меньшим)
     В словаре context отправляем информацию в шаблон.
    """
    posts = Post.objects.all()
    page_obj = func_paginator(request, posts)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = (
        Post.objects.filter(group=group)
        .all()
    )
    page_obj = func_paginator(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    users = get_object_or_404(User, username=username)
    posts = users.posts.all()
    page_obj = func_paginator(request, posts)

    context = {
        'users': users,
        'page_obj': page_obj

    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    context = {

        'posted': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id):
    """
    В переменную post подтягиваем посты,
    далее проверяем пользователя, является
    ли он автором поста, если нет то
    редирект на страницу детализации
    """
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {
        'form': form,
        'post': post,
        'post_edit_flag': True})


def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk)
    post.delete()
    return redirect('posts:profile', post.author)
