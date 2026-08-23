from nette.findings import PARSE_ERROR_CODE
from nette.rules.annotations import UnderAnnotated
from nette.rules.base import DEFAULT_THRESHOLDS, Context, Rule
from nette.rules.defensiveness import Defensiveness
from nette.rules.duplication import DuplicatedSibling
from nette.rules.naming import NamingDrift, ShortNameLongScope
from nette.rules.shape import SHAPE_RULES
from nette.rules.structure import FileNaming, FileSize, MixedModule
from nette.suppressions import MISSING_REASON_CODE, UNUSED_ALLOW_CODE

ALL_RULES = (
    *SHAPE_RULES,
    Defensiveness,
    ShortNameLongScope,
    NamingDrift,
    FileNaming,
    FileSize,
    DuplicatedSibling,
    MixedModule,
    UnderAnnotated,
)
ENGINE_CODES = (PARSE_ERROR_CODE, MISSING_REASON_CODE, UNUSED_ALLOW_CODE)
KNOWN_RULE_CODES = frozenset({rule.code for rule in ALL_RULES} | set(ENGINE_CODES))

__all__ = [
    "ALL_RULES",
    "ENGINE_CODES",
    "KNOWN_RULE_CODES",
    "Context",
    "Rule",
    "DEFAULT_THRESHOLDS",
    "SHAPE_RULES",
]
