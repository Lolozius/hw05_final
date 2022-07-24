from django.shortcuts import redirect, render
from http import HTTPStatus


def core(request):
    return redirect('https://youtu.be/dQw4w9WgXcQ')


def Not_found_404(request, exception):
    return render(
        request,
        'error_page/404.html',
        {'path': request.path}, status=HTTPStatus.NOT_FOUND
    )


def crfs_403(request):
    return render(request, 'error_page/403.html', status=HTTPStatus.FORBIDDEN)


def server_error_500(request):
    return render(
        request,
        'error_page/500.html',
        status=HTTPStatus.INTERNAL_SERVER_ERROR
    )


def csrf_failure(request, reason=''):
    return render(
        request,
        'error_page/403csrf.html',
        status=HTTPStatus.FORBIDDEN
    )
