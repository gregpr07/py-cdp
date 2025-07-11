# This file is auto-generated by the CDP protocol generator.
# Do not edit this file manually as your changes will be overwritten.
# Generated from Chrome DevTools Protocol specifications.

"""CDP Performance Domain Commands"""

from typing import List
from typing_extensions import TypedDict

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Metric

class EnableParameters(TypedDict, total=False):
    timeDomain: "str"
    """Time domain to use for collecting and reporting duration metrics."""





class SetTimeDomainParameters(TypedDict):
    timeDomain: "str"
    """Time domain"""





class GetMetricsReturns(TypedDict):
    metrics: "List[Metric]"
    """Current values for run-time metrics."""
