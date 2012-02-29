from django.conf import settings


def settings_get(key):
    """
    helper function to ease access to settings module
    """
    #XXX deprecate. shouuld use getattr(settings, 'foo', default)
    if hasattr(settings, key):
        return settings.__getattr__(key)
    else:
        return None

X509_KEYS = {
            'cert': 'SSL_CLIENT_CERT',
            'verify': 'SSL_CLIENT_VERIFY',
        }


class SSLInfo(object):
    """
    Encapsulates the SSL environment variables in a read-only object.
    It attempts to find
    the ssl vars based on the type of request passed to the constructor.
    Currently only WSGIRequest and ModPythonRequest are supported.
    """
    def __init__(self, request):
        """
        initializator method. accepts only a request.
        """
        name = request.__class__.__name__
        if settings_get('WEBIDAUTH_FORCE_ENV'):
            env = settings_get('WEBIDAUTH_FORCE_ENV')
        #XXX better to make isinstance checks???

        elif name == 'WSGIRequest':
            env = request.environ
        elif name == 'ModPythonRequest':
            env = request._req.subprocess_env
        else:
            raise EnvironmentError('WEBIDAuth currently only works \
with mod_python or wsgi requests')
        self.read_env(env)

        #print 'verification:'
        #print self.__dict__['verify']

    def read_env(self, env):
        """
        reads cert variables from environment
        """
        for attr, key in X509_KEYS.iteritems():
            if key in env and env[key]:
                self.__dict__[attr] = env[key]
            else:
                self.__dict__[attr] = None

        if self.__dict__['verify'] == 'SUCCESS':
            self.__dict__['verify'] = True
        else:
            self.__dict__['verify'] = False

    def get(self, attr):
        """
        attribute getter
        """
        return self.__getattr__(attr)

    def get_dict(self, prefix):
        """
        returns dict.
        """
        _dict = {}
        for key in X509_KEYS.keys():
            if key.startswith(prefix):
                _dict[key] = self.__dict__[key]
        return _dict

    def __getattr__(self, attr):
        """
        attr getter.
        """
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            raise AttributeError('SSLInfo does \
not contain key %s' % attr)

    #XXX probably it's not a good idea to disable this check
    def __setattr__(self, attr, value):
        raise AttributeError('SSL vars are read only!')
