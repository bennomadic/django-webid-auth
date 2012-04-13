WebIDAuth Django App
=====================

Authors:
  Ben Carrillo <bennomadic@gmail.com>
  Julia Anaya <julia.anaya@gmail.com>

Based on code from sslauth, by Marcus Weseloh <mawe42@gmail.com>

Introduction
------------
This django app provides the middleware and the authentication backend needed for enabling `WebID based authentication <http://webid.info/spec>`_ in any django project.

Setup
-----
1. Add django_webid.auth and django_webid.provider apps to your project INSTALLED_APPS.

2. Set the WebIDAuthBackend in your AUTHENTICATION_BACKENDS tuple. 
   If you want to be able to use the username/password, leave the ModelBackend in place::

   AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'django_webid.auth.backends.WebIDAuthBackend',
   )

3. Add the WebIDAuthMiddleware to your MIDDLEWARE_CLASSES. 
   You can leave out AuthenticationMiddleware:: 

   MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_webid.auth.middleware.WebIDAuthMiddleware',
   )
   
4. Run a ./manage syncdb to populate models.

5. Configure your web server to ask client for a certificate on your chosen location (see Apache configuration section).

And you're set! Any valid WebID certificate should allow your happy users to log into your site.

Refer to the docs section for a complete Settings list.
