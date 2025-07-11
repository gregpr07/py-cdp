# This file is auto-generated by the CDP protocol generator.
# Do not edit this file manually as your changes will be overwritten.
# Generated from Chrome DevTools Protocol specifications.

"""CDP ServiceWorker Domain Events"""

from typing import List
from typing_extensions import TypedDict

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import ServiceWorkerErrorMessage
    from .types import ServiceWorkerRegistration
    from .types import ServiceWorkerVersion

class WorkerErrorReportedEvent(TypedDict):
    errorMessage: "ServiceWorkerErrorMessage"



class WorkerRegistrationUpdatedEvent(TypedDict):
    registrations: "List[ServiceWorkerRegistration]"



class WorkerVersionUpdatedEvent(TypedDict):
    versions: "List[ServiceWorkerVersion]"
