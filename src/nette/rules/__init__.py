from nette.findings import PARSE_ERROR_CODE
from nette.rules.base import DEFAULT_THRESHOLDS, Context, Rule
from nette.rules.defensiveness import Defensiveness
from nette.rules.naming import NamingDrift, ShortNameLongScope
from nette.rules.shape import SHAPE_RULES
from nette.rules.structure import FileNaming, FileSize
from nette.suppressions import MISSING_REASON_CODE

ALL_RULES = (
    *SHAPE_RULES,
    Defensiveness,
    ShortNameLongScope,
    NamingDrift,
    FileNaming,
    FileSize,
)
KNOWN_RULE_CODES = frozenset(
    {rule.code for rule in ALL_RULES} | {PARSE_ERROR_CODE, MISSING_REASON_CODE}
)

__all__ = [
    "ALL_RULES",
    "KNOWN_RULE_CODES",
    "Context",
    "Rule",
    "DEFAULT_THRESHOLDS",
    "SHAPE_RULES",
]
