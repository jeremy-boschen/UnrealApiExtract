class UnrealApiExtractorError(Exception):
    """Base exception for the extractor."""


class ModuleNotFoundError(UnrealApiExtractorError):
    pass


class PluginEnableError(UnrealApiExtractorError):
    pass


class BuildFailureError(UnrealApiExtractorError):
    pass


class CompileDbError(UnrealApiExtractorError):
    pass


class UhtOutputMissingError(UnrealApiExtractorError):
    pass
