WebIDAuth Django App
=====================

Authors:
  Ben Carrillo <bennomadic@gmail.com>
  Julia Anaya <julia.anaya@gmail.com>

Based on code from sslauth, by Marcus Weseloh <mawe42@gmail.com>

Introduction
------------
This django app provides the middleware and the authentication backend needed for enabling `WebID based authentication <http://webid.info/spec>`_ in any django project.

Installation
------------
1. Add django_webid.auth and django_webid.provider apps to your project INSTALLED_APPS.

2. Set the WebIDAuthBackend as your AUTHENTICATION_BACKENDS. 
   If you want to be able to use the  username/password
   Example:
   AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'mythirdpartyapps.sslauth.backends.SSLAuthBackend',
   )

3. Add the WebIDAuthMiddleware to your MIDDLEWARE_CLASSES. 
   You can leave out AuthenticationMiddleware 
   Example:
   MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_webid.auth.middleware.WebIDAuthMiddleware',
   )
   
4. Run a ./manage syncdb to populate models.

And you're set! Any valid WebID certificate should allow your happy users to log into your site.
