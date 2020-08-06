"""A package which allow parsing Reussian receipts."""

__version__ = "0.0.24"
__license__ = "MIT"


from .receipt_parser import RuleBased  # type: ignore
from .finder import Finder  # type: ignore
from .normalizer import Normalizer  # type: ignore
from .cat_model import PredictCategory  # type: ignore
