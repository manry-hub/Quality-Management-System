import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("qms.core.audit")


class AuditTrailMiddleware(MiddlewareMixin):
    """
    Captures client request metadata (IP address, user agent) and stores on current thread/request
    for 21 CFR Part 11 audit logging traceability.
    """
    def process_request(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        request.client_ip = ip
        return None
