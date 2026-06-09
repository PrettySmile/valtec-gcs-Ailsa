from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from app.exceptions.drone import DroneNotFoundError
from app.constants.error_codes import ErrorCode
from app.models.error import ErrorResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    @app.exception_handler(DroneNotFoundError)
    async def drone_not_found_handler(request: Request, exc: DroneNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                code=ErrorCode.DRONE_NOT_FOUND.value,
                message=str(exc),
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                code=ErrorCode.VALIDATION_ERROR.value,
                message=str(exc.errors()),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            f"Unexpected error. "
            f"path={request.url.path}, "
            f"method={request.method}"
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR.value,
                message="Unexpected error occurred",
            ).model_dump(),
        )
