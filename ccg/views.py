def status_view(request):
    """Default project status page. Checks each status function and returns 200 OK if they all pass, else 500. The idea is not to leak any information about how things passed or failed, except for the name of the check function in case of failure or uncaught exception"""
    from django.conf import settings
    from django.http import HttpResponse, HttpResponseServerError
    if hasattr(settings,"STATUS_CHECKS"):
        # perform checks
        result = True
        for check in settings.STATUS_CHECKS:
            if callable(check):
                try:
                    result &= check(request)
                except:
                    # catch accidental uncaught exceptions
                    return HttpResponseServerError("Exception in status check: %s\n" % (str(check.__name__) ) )


            if not result:
                # failure
                return HttpResponseServerError("Status check failed: %s\n" % (check.__name__) )

    # no checks or all checks pass. we succeed!
    return HttpResponse("Project is running OK\n",status=200)
