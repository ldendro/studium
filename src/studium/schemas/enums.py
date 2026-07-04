"""StrEnum types for Studium concept note metadata."""

from enum import StrEnum


class ConceptType(StrEnum):
    GENERAL_CONCEPT = "general_concept"
    MATHEMATICAL_CONCEPT = "mathematical_concept"
    ALGORITHM = "algorithm"
    PROGRAMMING_CONCEPT = "programming_concept"
    SYSTEM_DESIGN_CONCEPT = "system_design_concept"
    THEORY_CONCEPT = "theory_concept"
    PROCESS_CONCEPT = "process_concept"
    TOOLING_CONCEPT = "tooling_concept"


class SourceType(StrEnum):
    STUDIUM = "studium"
    BOOK = "book"
    VIDEO = "video"
    PAPER = "paper"
    ARTICLE = "article"
    CLASS = "class"
    WORK = "work"
    PROJECT = "project"
    DOCUMENTATION = "documentation"
    CHATBOT = "chatbot"
    PODCAST = "podcast"
    IMPORTED_NOTE = "imported_note"
    OTHER = "other"


class EncounterRole(StrEnum):
    PRIMARY = "primary"
    ADDITIONAL = "additional"


class ContributionStatus(StrEnum):
    PENDING = "pending"
    USER_DESCRIBED = "user_described"
    SOURCE_ATTACHED = "source_attached"
    SOURCE_ANALYZED = "source_analyzed"
    INTEGRATED = "integrated"
    NO_NEW_CONTRIBUTION_DETECTED = "no_new_contribution_detected"


class NoteStatus(StrEnum):
    SCAFFOLDED = "scaffolded"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class ReviewStatus(StrEnum):
    NOT_SUBMITTED = "not_submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"


class NoteVaultStatus(StrEnum):
    DRAFT = "draft"
    ACCEPTED = "accepted"


class ScaffoldModuleType(StrEnum):
    CONCEPTUAL_EXPLANATION = "conceptual_explanation"
    WORKED_EXAMPLE = "worked_example"
    CODE_IMPLEMENTATION = "code_implementation"
    IMPLEMENTATION_NOTES = "implementation_notes"
    COMPARISON = "comparison"
    DERIVATION = "derivation"
    APPLICATION = "application"
    MISCONCEPTION_DEBUGGING = "misconception_debugging"
    CUSTOM = "custom"


class ScaffoldModuleStatus(StrEnum):
    SCAFFOLDED = "scaffolded"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"


class ScaffoldModuleOrigin(StrEnum):
    AGENT_RECOMMENDED = "agent_recommended"
    USER_REQUESTED = "user_requested"
    SOURCE_SUGGESTED = "source_suggested"
    REVIEW_SUGGESTED = "review_suggested"
    MANUAL = "manual"


class RelationshipType(StrEnum):
    DEPENDS_ON = "depends_on"
    PREREQUISITE_FOR = "prerequisite_for"
    RELATED_TO = "related_to"
    VARIANT_OF = "variant_of"
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    CONTRASTS_WITH = "contrasts_with"


class RelationshipVaultStatus(StrEnum):
    FOUND = "found"
    MISSING = "missing"
    UNRESOLVED = "unresolved"


class ValidationOperation(StrEnum):
    PARSE = "parse"
    CREATE = "create"
    UPDATE = "update"
    WRITE = "write"


class ValidationSeverity(StrEnum):
    CRITICAL = "critical"
    WARNING = "warning"


class WriteOperation(StrEnum):
    CREATE_NOTE = "create_note"
    UPDATE_NOTE = "update_note"
