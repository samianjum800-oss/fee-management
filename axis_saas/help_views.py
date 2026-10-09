from mimetypes import guess_type
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_safe

HELP_CACHEABLE_SUFFIXES = {
    '.css', '.gif', '.html', '.ico', '.jpeg', '.jpg', '.js', '.json',
    '.png', '.svg', '.webmanifest', '.webp', '.woff', '.woff2', '.xml',
}


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

    content_type = (
        'application/manifest+json'
        if file_path.suffix == '.webmanifest'
        else guess_type(file_path.name)[0] or 'application/octet-stream'
    )
    response = FileResponse(
        file_path.open('rb'),
        content_type=content_type,
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


@require_safe
def help_service_worker(request):
    worker_path = (
        Path(settings.BASE_DIR) / 'docs' / 'assets' / 'axis-help-sw.js'
    ).resolve()
    if not worker_path.is_file():
        raise Http404('AXIS Help offline support is unavailable.')

    response = FileResponse(
        worker_path.open('rb'),
        content_type='application/javascript; charset=utf-8',
    )
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Service-Worker-Allowed'] = '/help/'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@require_safe
def help_cache_manifest(request):
    site_root = (Path(settings.BASE_DIR) / 'help_site').resolve()
    if not site_root.is_dir():
        raise Http404('AXIS Help Center has not been built.')

    urls = {'/help/'}
    for file_path in site_root.rglob('*'):
        if not file_path.is_file() or file_path.suffix.lower() not in HELP_CACHEABLE_SUFFIXES:
            continue

        relative = file_path.relative_to(site_root).as_posix()
        if relative == 'index.html':
            url = '/help/'
        elif relative.endswith('/index.html'):
            url = '/help/' + relative[:-len('index.html')]
        else:
            url = '/help/' + relative
        urls.add(url)

    response = JsonResponse({'urls': sorted(urls)})
    response['Cache-Control'] = 'no-store'
    return response
