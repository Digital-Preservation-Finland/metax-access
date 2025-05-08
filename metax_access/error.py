class MetaxError(Exception):
    """Generic invalid usage Exception."""

    def __init__(self, message="Metax error", response=None):
        """Init MetaxError."""
        super().__init__(message)
        self.message = message
        self.response = response


class ResourceNotAvailableError(MetaxError):
    """Exception raised when resource is not found from metax."""

    def __init__(self, message="Resource not found"):
        """Init ResourceNotAvailableError."""
        super().__init__(message)


class ResourceAlreadyExistsError(MetaxError):
    """Exception raised when resource to be created already exists."""

    def __init__(self, message="Resource already exists.", response=None):
        """Init ResourceAlreadyExistsError.

        :param message: error message
        :param dict errors: Key-value pairs that caused the exception
        """
        super().__init__(message, response=response)


class FileNotAvailableError(ResourceNotAvailableError):
    """Exception raised when file is not found from metax."""

    def __init__(self):
        """Init FileNotAvailableError."""
        super().__init__("File not found")


class DatasetNotAvailableError(ResourceNotAvailableError):
    """Exception raised when dataset is not found from metax."""

    def __init__(self):
        """Init DatasetNotAvailableError."""
        super().__init__("Dataset not found")


class ContractNotAvailableError(ResourceNotAvailableError):
    """Exception raised when contract is not found from metax."""

    def __init__(self):
        """Init ContractNotAvailableError."""
        super().__init__("Contract not found")


class DataciteGenerationError(MetaxError):
    """Exception raised when Metax returned 400 for datacite."""

    def __init__(self, message="Datacite generation failed in Metax"):
        """Init DataciteGenerationError."""
        super().__init__(message)
