import logging
import re

from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import UserManager

from util import settings_get

from webid.validator import WebIDValidator
#XXX problems with this import???!

logger = logging.getLogger(name=__name__)

if settings.DEBUG:
    logger.setLevel(logging.DEBUG)

logger.error('trying to import WebID model')
from django_webid.provider import models


class WEBIDAuthBackend:
    """
    Authenticate a client certificate checking cert and webid credentials
    and lookup the corresponding django user

    In all methods, the ssl_info parameter is supposed to be an SSLInfo
    instance
    """
    def authenticate(self, request=None):
        logger.error('AUTHENTICATING:  ')
        ssl_info = request.ssl_info
        logger.debug('ssl_info.cert %s' % ssl_info.cert)
        certstr = ssl_info.__dict__.get('cert', None)
        logger.error('certstr= %s' % certstr)
        validator = WebIDValidator(certstr=certstr)
        validated, data = validator.validate()
        #passing data in request
        request.webidinfo = data
        if validated is True:
            data._extract_webid_name(data.validatedURI)
            logger.error(
            'OK! ALMOST DONE! SUCCESSFULLY CHECKED WEBID!\
            NOW SHOULD BE AUTHD!')
            user = self.get_user_from_uri(request.webidinfo.validatedURI)
            if user:
                logger.debug('>>>>>>>> yeah! we got an user')
                return user
            else:
                logger.debug('>>>>>>> no user :( ')
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
            logger.debug('>>>>>>>>>> getting user by uri = %s' % user_uri)
            user = models.WebIDUser.get_for_uri(user_uri)
            logger.debug('user is %s' % user)
            return user
        except models.WebIDUser.DoesNotExist:
            logger.debug('>>>>>>>>>> that user doesnot exists :(')
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
        #XXX make sure that uri does not exists
        user = self.get_user_from_uri(data.validatedURI)
        if not user:
            if settings_get('WEBDIAUTH_CREATE_USER_CALLBACK'):
                build_user = settings_get('WEBIDAUTH_CREATE_USER_CALLBACK')
            else:
                logger.error('create user: no callback')
                build_user = self.build_user
            logger.error('calling to build_user')
            user = build_user(request)
        return user

    def build_user(self, request=None):
        """
        create a valid (and stored) django user to be associated with
        the authenticated WebID URI. This method can be "overwritten"
        by using the
        WEBIDAUTH_CREATE_USER_CALLBACK setting.
        """
        logger.debug('>>>>>>>>>>>>>>building user!')
        user = models.WebIDUser()
        data = request.webidinfo
        names = data.webid_name

        field_name = "name"
        target_name = names.get(field_name, None)

        def augment_name(name):
            ends_number = re.findall('\S+_(\d+)', name)
            if ends_number:
                number = int(ends_number[0]) + 1
                print 'number', number
                _name = name.replace('_%s' % ends_number[0], '_%s' %
                        str(number))
                return _name
            else:
                return u"%s_1" % (name)

        #[warning] This is "a bit" hackish:
        max_tries = 10
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
                #print ('oops... name taken')
                target_name = augment_name(target_name)
                tries -= 1
            else:
                break
        else:
            logger.error('Sorry... Your name is already taken...')
            #XXX here we should signal some way of getting
            #user input (a form, or something)

        # what the fuckt is this get('key', None) ??
        # I think I was too sleepy when I wrote this
        #if names.has_key('name') and names.get('key', None):

        # XXX this assumption is very very weak
        # i.e, make sure to find a proper username if we do not
        # have the nick information.

        # Also, handle collisions
        # (better to have, for instance, user@site usernames in the db
        # and have a display-name?)
        user.username = target_name
        logger.error('username set to %s' % names['name'])

        user.uri = data.validatedURI
        user.password = UserManager().make_random_password()
        user.is_active = True
        logger.error('saving??')
        #print 'name ', user.username
        user.save()
        return user
