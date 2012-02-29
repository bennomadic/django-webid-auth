#from django.contrib.auth import authenticate, login, get_user
#from backends import authenticate, get_user
import logging

from backends import WEBIDAuthBackend
from django.contrib.auth import login
from django.contrib.auth import get_user
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from util import SSLInfo, settings_get

logger = logging.getLogger(name=__name__)


class WEBIDAuthMiddleware(object):
    """
    attempts to find a valid user based on the client certificate info
    """
    def process_request(self, request):
        USE_COOKIE = settings_get('WEBIDAUTH_USE_COOKIE')
        #@TODO implement cookies
        if USE_COOKIE:
            #WTF??
            request.user = get_user(request)
            if request.user.is_authenticated():
                logging.error('>>>>>>>>>>>> YOUR COOKIE SAYS: \
                        YOU ARE ALRDY AUTHD!')
                return

        #logging.error("WEBIDAuthMiddleware: about to construct sslinfo")
        request.ssl_info = SSLInfo(request)
        logging.debug("calling to authenticate user (on middleware)")
        user = WEBIDAuthBackend().authenticate(
                request=request) or AnonymousUser()
        logger.debug('first auth: now user is %s' % user)
        logger.warning('NO USER. Attempting to create one')
        logger.debug('validated? %s' % request.webidvalidated)
        logger.debug('create user? %s' % settings.WEBIDAUTH_CREATE_USER)
        #XXX check ssl_info.verify ??
        logger.debug(settings.WEBIDAUTH_CREATE_USER)
        if request.webidvalidated and not user.is_authenticated() and \
                settings_get('WEBIDAUTH_CREATE_USER'):
            logger.info('Validated. Trying to create user.')
        #if not user.is_authenticated() and \
        #   settings_get('WEBIDAUTH_CREATE_USER'):
            created = WEBIDAuthBackend().create_user(request=request)
            if created:
                user = WEBIDAuthBackend().authenticate(
                        request=request) or AnonymousUser()

        logger.debug('final check. now user is %s' % user)
        if user.is_authenticated() and USE_COOKIE:
            login(request, user)
        else:
            request.user = user
