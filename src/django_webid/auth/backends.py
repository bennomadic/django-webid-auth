import logging
import re

from django.conf import settings
from django.contrib.auth.models import UserManager
from django.db import transaction

from util import settings_get
from webid.validator import WebIDValidator
#XXX problems with this import???!
from django_webid.provider import models

logger = logging.getLogger(name=__name__)


class WEBIDAuthBackend:
    """
    Authenticate a client certificate checking cert and webid credentials
    and lookup the corresponding django user

    In all methods, the ssl_info parameter is supposed to be an SSLInfo
    instance
    """
    def authenticate(self, request=None):
        ssl_info = request.ssl_info
        certstr = ssl_info.__dict__.get('cert', None)

        #logger.debug('ssl_info.cert %s' % ssl_info.cert)
        logger.debug('certstr= %s' % certstr)

        if not getattr(request, 'webidvalidated', None):
            logger.debug('about to validate client cert')
            validator = WebIDValidator(certstr=certstr)
            validated, data = validator.validate()
            request.webidvalidated = validated
            validatedURI = data.validatedURI

            custom_query = getattr(settings,
                    "WEBIDAUTH_USERNAME_SPARQL",
                    None)
            #XXX FIXME document this.
            #Or better, make both settings together
            #as a dict...
            custom_vars = getattr(settings,
                    "WEBIDAUTH_USERNAME_VARS",
                    None)

            #FIXME !!!
            #If no results with custom query, we could
            #try some fallbacks... we need something for
            #building the username...
            #or we can ask user to choose a visible name
            #if we could not retrieve anything useful.

            data._extract_webid_name(validatedURI,
                    sparql_query=custom_query,
                    sparql_vars=custom_vars)

            #passing data in request
            request.webidinfo = data
        else:
            logger.debug('we had already validated this cert!')
            validated = True

        if validated is True:
            logger.debug(
            '[OK] PASSED WEBID! NOW SHOULD BE AUTHD!')
            user = self.get_user_from_uri(request.webidinfo.validatedURI)
            if user:
                logger.debug('yeah! we got an user')
                user.backend = 'django_webid.auth.backends.WebIDAuthBackend'
                # Annotate the user object with the path of the
                # backend.
                user.backend = "%s.%s" % (self.__module__,
                               self.__class__.__name__)
                return user
            else:
                logger.debug('>>> no user :( ')
                return None
        else:
            #XXX this logic is wrong.
            #We have to signal somehow that either
            #1) WebID validation process went wrong (and then redirect user
            #   to debug page.
            #2) WebID validation process went OK,
            #   but still we do not have an user (it's made on the middleware).

            # And yet we have to respect the authenticate api...
            return None

    def get_user_from_uri(self, uri):
        user_uri = uri
        #make sure that uri does not exists
        try:
            logger.debug('>>> getting user by uri = %s' % user_uri)
            if not uri:
                return None
            user = models.WebIDUser.get_for_uri(user_uri)
            logger.debug('user is %s' % user)
            return user
        except models.WebIDUser.DoesNotExist:
            logger.debug('>>> that user does not exists :(')
            return None

    def get_user(self, user_id):
        """
        simply return the user object. That way, we only need top look-up the
        certificate once, when loggin in
        """
        try:
            return models.WebIDUser.objects.get(id=user_id)
        except models.WebIDUser.DoesNotExist:
            return None

    @transaction.commit_on_success
    def create_user(self, request=None):
        """
        This method creates a new django WebIDUser record
        for the webid associated to the client certificate.
        """
        data = request.webidinfo
        #data "now" is ssl_info.
        #TODO make sure that this WebIDURI indeed does not exists
        logger.debug('creating user')
        user = self.get_user_from_uri(data.validatedURI)
        if not user:
            #XXX enclose in a try block
            build_user_cb = getattr(settings,
                    'WEBIDAUTH_CREATE_USER_CALLBACK', None)
            if build_user_cb:
                #XXX we should check also that it accepts an argument.
                if not callable(build_user_cb):
                    logger.warning('The provided build_user callback is not a\
callable function. Using default build function.')
                    build_user_cb = None
            else:
                logger.debug('create user: no callback. Using default build \
function. Sup.')
            if not build_user_cb:
                build_user_cb = self.build_user
            logger.debug('calling to build_user callback')
            user = build_user_cb(request)
        return user

    def build_user(self, request=None):
        """
        create a valid (and stored) django user to be associated with
        the authenticated WebID URI. This method will be used if no alternative
        is provided in the settings.WEBIDAUTH_CREATE_USER_CALLBACK value, or if
        the value there is not a valid function.
        """
        logger.debug('building user!')
        data = request.webidinfo
        validatedURI = data.validatedURI
        logger.debug('validatedURI = %s' % validatedURI)
        if not validatedURI:
            #XXX this check should be moved to "create_user" function
            logger.error('attempt to build an user with no validatedURI! \
skipping...')
            return None

        names = data.webid_name

        field_name = "name"
        target_name = names.get(field_name, None)

        def augment_name(name):
            ends_number = re.findall('\S+_(\d+)', name)
            if ends_number:
                number = int(ends_number[0]) + 1
                logger.debug('number %s' % number)
                _name = name.replace('_%s' % ends_number[0], '_%s' %
                        str(number))
                return _name
            else:
                return u"%s_1" % (name)

        #[warning] This is "a bit" hackish:
        max_tries = 20
        tries = max_tries

        while tries > 0:
            print 'looping'
            print 'target_name', target_name
            print 'try', max_tries - tries
            #XXX build kwargs dict, instead of hardcoding name
            colliding_users = models.WebIDUser.objects.all().\
                    filter(username=target_name)
            #print 'colliding ', colliding_users
            #print colliding_users.count()
            #print 'all ', WebIDUser.objects.all()

            if colliding_users.count() > 0:
                target_name = augment_name(target_name)
                tries -= 1
            else:
                break
        else:
            logger.warning('Sorry... *that* name is already taken...')
            #XXX here we should signal some way of getting
            #user input (a form, or something)

        # XXX this assumption is very very weak
        # i.e, make sure to find a proper username if we do not
        # have the nick information.
        # Also, handle collisions
        # (better to have, for instance, user@site usernames in the db
        # and have a display-name?)
        user = models.WebIDUser.objects.create(username=target_name)
        useruri = models.WebIDURI.objects.create(uri=validatedURI, user=user)
        useruri.save()
        logger.info('username set to %s' % names['name'])
        user.password = UserManager().make_random_password()
        user.is_active = True
        logger.debug('saving WebIDUser with name %s' % target_name)
        user.save()
        return user
