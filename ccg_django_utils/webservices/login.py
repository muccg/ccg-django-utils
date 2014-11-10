from django.contrib import admin, auth
from django.conf.urls.defaults import patterns, url
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotAllowed
from json import dumps, loads


def autodiscover():
    """
    Auto-discover INSTALLED_APPS admin.py modules and fail silently when
    not present. This forces an import on them to register any admin bits they
    may want.
    """

    import copy
    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    # Monkey patch admin.site to be our own site instance, which makes
    # autodiscovered modules using admin.site.register magically work.
    admin.site = site

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        # Attempt to import the app's admin module.
        try:
            before_import_registry = copy.copy(site._registry)
            import_module('%s.admin' % app)
            print app, "imported"
        except:
            # Reset the model registry to the state before the last import as
            # this import will have to reoccur on the next request and this
            # could raise NotRegistered and AlreadyRegistered exceptions
            # (see #8245).
            site._registry = before_import_registry
            print app, "failed"

            # Decide whether to bubble up this error. If the app just
            # doesn't have an admin module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, 'admin'):
                raise


class AdminSite(admin.AdminSite):
    """
    Extension of the Django AdminSite class to implement a simple Web service
    to allow logging in and out without needing to fake form submissions.

    Generally speaking, you can use this in one of two ways:

    1. If you're using admin.autodiscover() in urls.py, just change the import
       and function call to use the autodiscover() function above, and include
       site.urls in the patterns from this module instead of
       django.contrib.admin.  This module's autodiscover will take care of
       ensuring ModelAdmins are registered to the right site instance.

    2. If you're manually registering models on an AdminSite instance already
       (even if it's just django.contrib.admin.site), simply instantiate this
       AdminSite class and register them on that instead, or use the site
       instance this module provides.
    """

    CONTENT_TYPE = "application/json; charset=UTF-8"

    def get_urls(self):
        """
        Function to add the login, logout and user calls to the AdminSite.
        """

        urls = super(AdminSite, self).get_urls()

        local_urls = patterns("",
            url(r"^ws/login", self.ws_login),
            url(r"^ws/logout", self.admin_view(self.ws_logout)),
            url(r"^ws/user", self.ws_user),
        )

        return local_urls + urls


    def ws_login(self, request):
        """
        Handler for login requests. Given a user name and password (either JSON
        or URL encoded), this will authenticate the user and create a session
        using the normal Django methods.
        """

        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        def login(username, password):
            user = auth.authenticate(username=username, password=password)
            
            if user is not None:
                if user.is_staff or user.is_superuser:
                    auth.login(request, user)
                    response = {
                        "success": True,
                        "user": unicode(user),
                    }
                    return HttpResponse(content_type=self.CONTENT_TYPE, content=dumps(response))
                else:
                    response = {
                        "success": False,
                        "message": "This user does not have access to MASTR MS.",
                    }
            else:
                response = {
                    "success": False,
                    "message": "The user name and password are incorrect.",
                }

            return HttpResponseForbidden(content_type=self.CONTENT_TYPE, content=dumps(response))

        if "username" in request.POST and "password" in request.POST:
            # Check for a HTTP POST upload first.
            return login(request.POST["username"], request.POST["password"])
        else:
            # Must be a JSON upload. Hopefully.
            try:
                data = loads(request.raw_post_data)
                return login(data["username"], data["password"])
            except ValueError:
                # No idea what we've been passed.
                response = {
                    "success": False,
                    "message": "Unable to interpret input data.",
                }
                return HttpResponseBadRequest(content_type=self.CONTENT_TYPE, content=dumps(response))


    def ws_logout(self, request):
        """
        Handler for logout requests. This only requires a valid session cookie.
        """

        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        auth.logout(request)
        
        response = {
            "success": True,
        }

        return HttpResponse(content_type=self.CONTENT_TYPE, content=dumps(response))


    def ws_user(self, request):
        """
        Handler for user information requests. If the user is logged in, this will return
        """

        if request.method != "GET":
            return HttpResponseNotAllowed(["GET"])

        if request.user.is_authenticated():
            response = {
                "logged_in": True,
                "user": unicode(request.user),
            }
        else:
            response = {
                "logged_in": False,
            }

        return HttpResponse(content_type=self.CONTENT_TYPE, content=dumps(response))


site = AdminSite()
