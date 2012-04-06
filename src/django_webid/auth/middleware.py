#from django.contrib.auth import authenticate, login, get_user
#from backends import authenticate, get_user
import logging

from backends import WEBIDAuthBackend
from django.contrib.auth import login
from django.contrib.auth import get_user
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from util import SSLInfo

logger = logging.getLogger(name=__name__)


class WEBIDAuthMiddleware(object):
    """
    attempts to find a valid user based on the client certificate info
    """
    def process_request(self, request):
        CREATE_USER = getattr(settings, "WEBIDAUTH_CREATE_USER", True)
        USE_COOKIE = getattr(settings, 'WEBIDAUTH_USE_COOKIE', False)

        EXCLUDE_ADMIN = getattr(settings, "WEBIDAUTH_EXCLUDE_ADMIN", True)
        EXCLUDE_STATIC = getattr(settings, "WEBIDAUTH_EXCLUDE_STATIC", True)
        EXCLUDE_MEDIA = getattr(settings, "WEBIDAUTH_EXCLUDE_MEDIA", True)
        EXCLUDE_PATH = getattr(settings, "WEBIDAUTH_EXCLUDE_PATH", None)

        toexclude = set([])

        if EXCLUDE_ADMIN:
            #XXX get proper admin URL setting
            adminurl = getattr(settings, "ADMIN_URL", "/admin/")
            toexclude.add(adminurl)

        if EXCLUDE_STATIC:
            staticurl = getattr(settings, "STATIC_URL", None)
            if staticurl:
                toexclude.add(staticurl)

        if EXCLUDE_MEDIA:
            mediaurl = getattr(settings, "MEDIA_URL", None)
            if mediaurl:
                toexclude.add(mediaurl)

        if EXCLUDE_PATH:
            if isinstance(EXCLUDE_PATH, list):
                for path in EXCLUDE_PATH:
                    toexclude.add(path)
            if isinstance(EXCLUDE_PATH, str):
                toexclude.add(EXCLUDE_PATH)

        #NON_WEBID_PATHS = ('/admin/', '/static/', '/media/')
        for path in toexclude:
            if request.path.startswith(path):
                return

        logger.debug('not skipping:%s' % request.path)
        logger.debug('use cookie? %s' % USE_COOKIE)
        logger.debug('')
        logger.debug('checking url path: %s' % request.path)

        if USE_COOKIE:
            #XXX we could get a parameter for ignoring (expiring)
            #the current user.
            #We could use that, for instance, for forcing the WebIDvalidation
            #report on a testlogin page.
            request.user = get_user(request)
            if request.user.is_authenticated():
                logger.debug('ALREADY AUTHENTICATED (by cookie)!')
                return

        #logging.debug("WEBIDAuthMiddleware: about to construct sslinfo")
        request.ssl_info = SSLInfo(request)
        logging.debug("calling to authenticate user (on middleware)")
        user = WEBIDAuthBackend().authenticate(
                request=request) or AnonymousUser()

        logger.debug('first auth attempt: now user is %s' % user)
        logger.debug('validated? %s' % request.webidvalidated)

        if request.webidvalidated and not user.is_authenticated():
            logger.debug('create user? %s' % CREATE_USER)
            if not isinstance(CREATE_USER, bool):
                logger.debug('WEBID_CREATE_USER was not bool')
                if callable(CREATE_USER):
                    logger.debug('calling CREATE_USER function with \
webidvalidated arg')
                    CREATE_USER = CREATE_USER(request.webidvalidated)

            if CREATE_USER is True:
                logger.info('Trying to create user per setting.')
                created = WEBIDAuthBackend().create_user(request=request)
                if created:
                    user = WEBIDAuthBackend().authenticate(
                            request=request) or AnonymousUser()
                else:
                    logger.warning('User creation failed.')

            if CREATE_USER is False:
                logger.debug('not creating user, per setting.')

        logger.debug('final check. now user is %s' % user)

        if user.is_authenticated() and USE_COOKIE:
            logger.debug('authenticated and USE_COOKIE')
            login(request, user)
        else:
            logger.debug('not authenticated or not cookie')
            request.user = user
