import enum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

E = TypeVar("E", bound=enum.Enum)

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"
    CASHIER = "CASHIER"
    TRAINER = "TRAINER"
    MEMBER = "MEMBER"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    INACTIVE = "INACTIVE"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class MemberStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class PlanStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISCONTINUED = "DISCONTINUED"


class SubscriptionType(str, enum.Enum):
    NEW = "NEW"
    RENEW = "RENEW"
    UPGRADE = "UPGRADE"


class SubscriptionStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class InvoiceStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class ScheduleStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


class AssignmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AttendanceStatus(str, enum.Enum):
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"


class FeedbackType(str, enum.Enum):
    RATING = "RATING"
    COMPLAINT = "COMPLAINT"


class FeedbackStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class NotificationType(str, enum.Enum):
    SUBSCRIPTION_EXPIRY = "SUBSCRIPTION_EXPIRY"
    TRAINING_SCHEDULE = "TRAINING_SCHEDULE"
    PAYMENT = "PAYMENT"
    FEEDBACK = "FEEDBACK"
    SYSTEM = "SYSTEM"


class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOCK = "LOCK"
    UNLOCK = "UNLOCK"
    PRICE_CHANGE = "PRICE_CHANGE"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"


class RevenuePeriod(str, enum.Enum):
    DAY = "DAY"
    MONTH = "MONTH"


EMPLOYEE_ROLES: frozenset[UserRole] = frozenset(
    {UserRole.ADMIN, UserRole.STAFF, UserRole.CASHIER, UserRole.TRAINER}
)


BOOKING_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
    BookingStatus.CONFIRMED: {BookingStatus.COMPLETED, BookingStatus.CANCELLED},
    BookingStatus.COMPLETED: set(),
    BookingStatus.CANCELLED: set(),
}

FEEDBACK_TRANSITIONS: dict[FeedbackStatus, set[FeedbackStatus]] = {
    FeedbackStatus.PENDING: {FeedbackStatus.PROCESSING, FeedbackStatus.REJECTED},
    FeedbackStatus.PROCESSING: {FeedbackStatus.RESOLVED, FeedbackStatus.REJECTED},
    FeedbackStatus.RESOLVED: {FeedbackStatus.CLOSED},
    FeedbackStatus.REJECTED: {FeedbackStatus.CLOSED},
    FeedbackStatus.CLOSED: set(),
}

INVOICE_TRANSITIONS: dict[InvoiceStatus, set[InvoiceStatus]] = {
    InvoiceStatus.UNPAID: {InvoiceStatus.PAID, InvoiceStatus.CANCELLED},
    InvoiceStatus.PAID: {InvoiceStatus.REFUNDED},
    InvoiceStatus.CANCELLED: set(),
    InvoiceStatus.REFUNDED: set(),
}

SUBSCRIPTION_TRANSITIONS: dict[SubscriptionStatus, set[SubscriptionStatus]] = {
    SubscriptionStatus.PENDING: {
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.CANCELLED,
    },
    SubscriptionStatus.ACTIVE: {
        SubscriptionStatus.SUSPENDED,
        SubscriptionStatus.EXPIRED,
        SubscriptionStatus.CANCELLED,
    },
    SubscriptionStatus.SUSPENDED: {
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.CANCELLED,
    },
    SubscriptionStatus.EXPIRED: set(),
    SubscriptionStatus.CANCELLED: set(),
}


def can_transition(table: dict[E, set[E]], current: E, target: E) -> bool:
    return target in table.get(current, set())


def enum_column(enum_cls: type[enum.Enum], length: int) -> SAEnum:
    def values_callable(cls: type[enum.Enum]) -> list[str]:
        return [str(member.value) for member in cls]

    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        validate_strings=True,
        values_callable=values_callable,
    )
