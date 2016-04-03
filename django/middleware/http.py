from django.utils.cache import (
    cc_delim_re, get_conditional_response, set_response_etag,
)
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import http_date, parse_http_date_safe


class ConditionalGetMiddleware(MiddlewareMixin):
    """
    Handles conditional GET operations. If the response has an ETag or
    Last-Modified header, and the request has If-None-Match or
    If-Modified-Since, the response is replaced by an HttpNotModified. An ETag
    header is added if needed.

    Also sets the Date and Content-Length response-headers.
    """
    def process_response(self, request, response):
        response['Date'] = http_date()
        if not response.streaming and not response.has_header('Content-Length'):
            response['Content-Length'] = str(len(response.content))

        if self.needs_etag(response) and not response.has_header('ETag'):
            set_response_etag(response)

        etag = response.get('ETag')
        last_modified = response.get('Last-Modified')
        if last_modified:
            last_modified = parse_http_date_safe(last_modified)

        if etag or last_modified:
            return get_conditional_response(
                request,
                etag=etag,
                last_modified=last_modified,
                response=response,
            )

        return response

    def needs_etag(self, response):
        """
        Return True if an ETag header should be added to response.
        """
        cache_control_headers = cc_delim_re.split(response.get('Cache-Control', ''))
        return all(header.lower() != 'no-store' for header in cache_control_headers)
