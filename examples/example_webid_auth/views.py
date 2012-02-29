from django.shortcuts import render, render_to_response  # get_object_or_404
from django.contrib.auth.decorators import login_required

from django.conf import settings


#@login_required
#XXX is this decodator working as expected?
#I think we need a webidlogin_required...
def test_login(request):
    return render_to_response('django_webid/auth/testlogin.html', {
        'user': request.user,
        'webidinfo': getattr(request, 'webidinfo', None),
        'STATIC_URL': settings.STATIC_URL,
        'MEDIA_URL': settings.MEDIA_URL,
        })


def webidlogin_report(request):
    if settings.DEBUG:
        content_type = "text/xml"
    else:
        content_type = "application/rdf+xml"
    return render(request,
        'django_webid/auth/webidloginReport.html',
        {'user': request.user,
        'webidinfo': request.webidinfo},
        content_type=content_type,
        )

def tryme(request):
    return render_to_response('django_webid/auth/tryme.html',
            {'STATIC_URL': settings.STATIC_URL})
