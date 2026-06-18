import enum
from datetime import datetime, timezone, date
from typing import Optional, Any
from sqlalchemy import (
    String, Integer, Boolean, DateTime, Date, ForeignKey, Index, func, text, Text, UniqueConstraint, Float
)
from sqlalchemy.dialects.postgresql import JSONB, ENUM as PG_ENUM
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# -----------------------------------------------------------------------------
# Base Class
# -----------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""
    pass

# -----------------------------------------------------------------------------
# Python Enums representing the schema states
# -----------------------------------------------------------------------------
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    LEARNER = "learner"
    ENTERPRISE_USER = "enterprise_user"
    ROOT = "root"
    SECURITY_ANALYST = "security_analyst"
    COMPLIANCE_OFFICER = "compliance_officer"
    ORG_ADMIN = "org_admin"


class OrgPlan(str, enum.Enum):
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class ContractType(str, enum.Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"

class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    TRIALING = "trialing"

class APIKeyTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class UsageEventType(str, enum.Enum):
    TUTOR_QUERY = "tutor_query"
    SIMULATION_RUN = "simulation_run"
    PQC_SCAN = "pqc_scan"
    API_CALL = "api_call"
    QPU_RUN = "qpu_run"


# -----------------------------------------------------------------------------
# Database Models
# -----------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    role: Mapped[UserRole] = mapped_column(
        PG_ENUM(UserRole, name="user_role_enum", create_type=True),
        nullable=False,
        default=UserRole.LEARNER
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )
    
    last_active_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True
    )
    
    org_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    usage_events: Mapped[list["UsageEvent"]] = relationship(
        "UsageEvent", back_populates="user", cascade="all, delete-orphan"
    )
    consent_records: Mapped[list["ConsentRecord"]] = relationship(
        "ConsentRecord", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )
    posts: Mapped[list["Post"]] = relationship(
        "Post", back_populates="author", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="author", cascade="all, delete-orphan"
    )
    circuits: Mapped[list["Circuit"]] = relationship(
        "Circuit", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    developer_api_keys: Mapped[list["ApiKey"]] = relationship(
        "ApiKey", back_populates="user", cascade="all, delete-orphan"
    )
    wallet_balance: Mapped[Optional["WalletBalance"]] = relationship(
        "WalletBalance", back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    user_plan: Mapped[Optional["UserPlan"]] = relationship(
        "UserPlan", back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    feature_usage: Mapped[Optional["FeatureUsage"]] = relationship(
        "FeatureUsage", back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, email={self.email!r}, role={self.role.value!r}, "
            f"org_id={self.org_id}, stripe_customer_id={self.stripe_customer_id!r})>"
        )


class Tier(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    API_METERED = "API_METERED"
    INSTITUTIONAL = "INSTITUTIONAL"
    ENTERPRISE = "ENTERPRISE"


class UserPlan(Base):
    __tablename__ = "user_plans"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )
    tier: Mapped[Tier] = mapped_column(
        PG_ENUM(Tier, name="user_tier_enum", create_type=True),
        nullable=False,
        default=Tier.FREE
    )
    cycle_reset_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today
    )

    user: Mapped["User"] = relationship("User", back_populates="user_plan")


class FeatureUsage(Base):
    __tablename__ = "feature_usages"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )
    daily_ai_chats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_pqc_scans: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_compute_overhead: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="feature_usage")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    
    plan: Mapped[OrgPlan] = mapped_column(
        PG_ENUM(OrgPlan, name="org_plan_enum", create_type=True),
        nullable=False,
        default=OrgPlan.STARTER
    )
    
    contract_type: Mapped[ContractType] = mapped_column(
        PG_ENUM(ContractType, name="contract_type_enum", create_type=True),
        nullable=False,
        default=ContractType.MONTHLY
    )
    
    pqc_scan_quota: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Organization(id={self.id}, name={self.name!r}, domain={self.domain!r}, "
            f"plan={self.plan.value!r}, pqc_scan_quota={self.pqc_scan_quota})>"
        )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    org_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    plan: Mapped[SubscriptionPlan] = mapped_column(
        PG_ENUM(SubscriptionPlan, name="sub_plan_enum", create_type=True),
        nullable=False,
        default=SubscriptionPlan.FREE
    )
    
    status: Mapped[SubscriptionStatus] = mapped_column(
        PG_ENUM(SubscriptionStatus, name="sub_status_enum", create_type=True),
        nullable=False,
        default=SubscriptionStatus.TRIALING
    )
    
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True
    )
    
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="subscriptions")
    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="subscriptions")

    def __repr__(self) -> str:
        return (
            f"<Subscription(id={self.id}, user_id={self.user_id}, org_id={self.org_id}, "
            f"plan={self.plan.value!r}, status={self.status.value!r})>"
        )


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    
    tier: Mapped[APIKeyTier] = mapped_column(
        PG_ENUM(APIKeyTier, name="api_key_tier_enum", create_type=True),
        nullable=False,
        default=APIKeyTier.FREE
    )
    
    requests_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_reset_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    daily_limit: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
    usage_events: Mapped[list["UsageEvent"]] = relationship(
        "UsageEvent", back_populates="api_key", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<APIKey(id={self.id}, user_id={self.user_id}, label={self.label!r}, "
            f"tier={self.tier.value!r}, is_active={self.is_active})>"
        )


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    api_key_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("api_keys.id", ondelete="SET NULL"),
        nullable=True
    )
    
    event_type: Mapped[UsageEventType] = mapped_column(
        PG_ENUM(UsageEventType, name="usage_event_type_enum", create_type=True),
        nullable=False
    )
    
    credits_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Python-side attribute name mapping to avoid conflicts with DeclarativeBase.metadata
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="usage_events")
    api_key: Mapped[Optional["APIKey"]] = relationship("APIKey", back_populates="usage_events")

    # Table arguments for required indexes
    __table_args__ = (
        Index("idx_usage_events_user_id_created_at", "user_id", text("created_at DESC")),
        Index("idx_usage_events_api_key_id", "api_key_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<UsageEvent(id={self.id}, user_id={self.user_id}, api_key_id={self.api_key_id}, "
            f"event_type={self.event_type.value!r}, credits_used={self.credits_used})>"
        )


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )
    
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="consent_records")

    def __repr__(self) -> str:
        return (
            f"<ConsentRecord(id={self.id}, user_id={self.user_id}, purpose={self.purpose!r}, "
            f"granted={self.granted})>"
        )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    old_value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # Fits IPv6 and IPv4
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action!r}, "
            f"table_name={self.table_name!r}, record_id={self.record_id})>"
        )


# -----------------------------------------------------------------------------
# Recreated Missing Models
# -----------------------------------------------------------------------------

class Circuit(Base):
    __tablename__ = "circuits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    circuit_data: Mapped[str] = mapped_column(Text, nullable=False)
    is_interactive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    share_slug: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="circuits")

    def __repr__(self) -> str:
        return f"<Circuit(id={self.id}, user_id={self.user_id}, name={self.name!r})>"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    author: Mapped["User"] = relationship("User", back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )
    likes: Mapped[list["Like"]] = relationship(
        "Like", back_populates="post", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_posts_created_at", text("created_at DESC")),
        Index("ix_posts_author_created", "author_id", text("created_at DESC")),
    )

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title={self.title!r}, author_id={self.author_id})>"


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")

    __table_args__ = (
        Index("ix_comments_created_at", text("created_at DESC")),
    )

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, post_id={self.post_id}, author_id={self.author_id})>"


class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )

    post: Mapped["Post"] = relationship("Post", back_populates="likes")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_like_post_user"),
    )

    def __repr__(self) -> str:
        return f"<Like(id={self.id}, post_id={self.post_id}, user_id={self.user_id})>"


class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Subscriber(id={self.id}, email={self.email!r}, is_active={self.is_active})>"


class NotificationRequest(Base):
    __tablename__ = "notification_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<NotificationRequest(id={self.id}, email={self.email!r})>"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    enrollment_status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    zoom_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, title={self.title!r}, is_active={self.is_active})>"


class LearnBlock(Base):
    __tablename__ = "learn_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )

    author: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<LearnBlock(id={self.id}, title={self.title!r}, author_id={self.author_id})>"


class PageProgress(Base):
    __tablename__ = "page_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    page_key: Mapped[str] = mapped_column(String(255), nullable=False)
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "page_key", name="uq_user_page_progress"),
    )

    def __repr__(self) -> str:
        return f"<PageProgress(id={self.id}, user_id={self.user_id}, page_key={self.page_key!r})>"


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    jti: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, jti={self.jti!r}, revoked={self.revoked})>"


class CohortEnrollment(Base):
    __tablename__ = "cohort_enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    payment_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )

    user: Mapped["User"] = relationship("User")
    course: Mapped["Course"] = relationship("Course")

    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_cohort_enrollment"),
    )

    def __repr__(self) -> str:
        return f"<CohortEnrollment(id={self.id}, user_id={self.user_id}, course_id={self.course_id})>"


class Log(Base):
    __tablename__ = "logtable"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False,
        index=True
    )
    level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    logger_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    module: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    function: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    request_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    request_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exception: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Log(id={self.id}, level={self.level!r}, message={self.message[:30]!r})>"


class MonitoredTarget(Base):
    __tablename__ = "monitored_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "domain" or "repository"
    target_value: Mapped[str] = mapped_column(String(500), nullable=False) # domain host or path/name
    schedule_interval: Mapped[str] = mapped_column(String(50), default="daily", nullable=False) # "daily" or "weekly"
    last_scan_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_scanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User")


class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    target_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("monitored_targets.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )

    user: Mapped["User"] = relationship("User")
    target: Mapped[Optional["MonitoredTarget"]] = relationship("MonitoredTarget")


# Import billing models to register them on Base metadata
from models_billing import ApiKey, WalletBalance, DailyUsageRollup




