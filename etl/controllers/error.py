# -*- coding: utf-8 -*-
"""Error controller"""
from tg import request, expose, decorators
from etl.lib.base import BaseController

__all__ = ['ErrorController']


class ErrorController(BaseController):
    """
    Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """

    @expose('etl.templates.error', custom_format='not_xhr')
    @expose('etl.templates.error_xhr', custom_format='xhr')
    def document(self, *args, **kwargs):
        """Render the error document"""
        resp = request.environ.get('tg.original_response')
        try:
            # tg.abort exposes the message as .detail in response
            message = resp.detail
        except:
            message = None

        if not message:
            message = ("<p>We're sorry but we weren't able to process "
                       " this request.</p>")

        if request.is_xhr:
            decorators.use_custom_format(self.document, 'xhr')
            try:
                message = kwargs['detail'][:kwargs['detail'].index(kwargs['detail'].split()[30])] + '...'\
                        if len(kwargs['detail'].split()) > 30 else kwargs['detail']
            except KeyError as ex:
                pass
        else:
            decorators.use_custom_format(self.document, 'not_xhr')

        values = dict(prefix=request.environ.get('SCRIPT_NAME', ''),
                      code=request.params.get('code', resp.status_int),
                      message=request.params.get('message', message))
        return values
