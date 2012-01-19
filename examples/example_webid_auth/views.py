from django.shortcuts import render, render_to_response  # get_object_or_404
from django.contrib.auth.decorators import login_required


@login_required
def test_login(request):
    return render_to_response('django_webid/auth/testlogin.html', {
        'user': request.user,
        'webidinfo': request.webidinfo
        })


def webidlogin_report(request):
    return render(request,
        'django_webid/auth/webidloginReport.html',
        {'user': request.user,
        'webidinfo': request.webidinfo},
        #XXX need a switch here.
        #If settings.DEBUG, set mimetype to xml
        #(it's easier for me to debug on browser)
        content_type="text/xml")
        #content_type="application/rdf+xml")
