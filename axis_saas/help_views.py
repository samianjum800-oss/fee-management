from mimetypes import guess_type
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_safe


def _serve_help_file(request, relative_path):
    site_root = (Path(settings.BASE_DIR) / 'help_site').resolve()
    if not site_root.is_dir():
        raise Http404('AXIS Help Center has not been built.')

    requested = Path(relative_path)
    if requested.is_absolute() or '..' in requested.parts:
        raise Http404
    if not requested.suffix:
        if not relative_path.endswith('/'):
            return redirect(request.path + '/')
        requested = requested / 'index.html'

    file_path = (site_root / requested).resolve()
    if site_root not in file_path.parents or not file_path.is_file():
        raise Http404

    response = FileResponse(
        file_path.open('rb'),
        content_type=guess_type(file_path.name)[0] or 'application/octet-stream',
    )
    response['Cache-Control'] = 'public, max-age=300'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@require_safe
def help_home(request):
    return _serve_help_file(request, 'index.html')


@require_safe
def help_asset(request, resource):
    return _serve_help_file(request, resource)
