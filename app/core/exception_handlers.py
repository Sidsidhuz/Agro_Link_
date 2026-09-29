import logging

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


def error_response(message, status_code, details=None, headers=None):
    return JSONResponse({'status': 'error', 'message': message, 'details': details or []},
                        status_code=status_code, headers=headers)


def register_exception_handlers(app):
    @app.exception_handler(AppError)
    async def application_error(request, exc):
        return error_response(exc.message, exc.status_code)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        message = exc.detail if isinstance(exc.detail, str) else 'Request failed'
        return error_response(message, exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Never echo input values, passwords, or validator context.
        details = [{'field': '.'.join(map(str, error['loc'])), 'type': error['type']}
                   for error in exc.errors()]
        return error_response('Request validation failed', 422, details)

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logger.exception('Unhandled API error on %s', request.url.path)
        return error_response('An unexpected error occurred', 500)
