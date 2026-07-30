from fastapi import HTTPException, status

class BusinessError(Exception):
    """Exception métier personnalisée."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class DatasetNotFoundError(BusinessError):
    def __init__(self, dataset_id: int):
        super().__init__(f"Dataset {dataset_id} non trouvé", status.HTTP_404_NOT_FOUND)

class PermissionDeniedError(BusinessError):
    def __init__(self, message: str = "Permission refusée"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)

class DuplicateResourceError(BusinessError):
    def __init__(self, resource: str, value: str):
        super().__init__(f"{resource} '{value}' existe déjà", status.HTTP_409_CONFLICT)

def raise_http_exception(exc: BusinessError):
    """Convertit une BusinessError en HTTPException."""
    raise HTTPException(status_code=exc.status_code, detail=exc.message)
