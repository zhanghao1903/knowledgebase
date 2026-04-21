from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, resource: str, resource_id):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id '{resource_id}' not found",
        )


class BadRequestError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class UnsupportedFileTypeError(BadRequestError):
    def __init__(self, file_type: str):
        super().__init__(
            detail=f"Unsupported file type: '{file_type}'. Supported: pdf, txt, docx",
        )


class InvalidURLError(BadRequestError):
    def __init__(self, detail: str):
        super().__init__(detail=f"Invalid URL: {detail}")


class URLFetchError(BadRequestError):
    def __init__(self, detail: str):
        super().__init__(detail=f"Failed to fetch URL: {detail}")


class UnsupportedSourceOperationError(BadRequestError):
    def __init__(self, detail: str):
        super().__init__(detail=detail)
