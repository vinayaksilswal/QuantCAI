from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models import Base

class ApiKey(Base):
    __tablename__ = "developer_api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    hashed_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', NOW())"),
        nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="developer_api_keys", lazy="selectin")
    rollups: Mapped[list["DailyUsageRollup"]] = relationship("DailyUsageRollup", back_populates="api_key", cascade="all, delete-orphan")


class WalletBalance(Base):
    __tablename__ = "wallet_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )
    balance_credits: Mapped[float] = mapped_column(Numeric(12, 6), default=0.0, nullable=False)
    auto_topup_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="wallet_balance", lazy="selectin")


class DailyUsageRollup(Base):
    __tablename__ = "daily_usage_rollups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_key_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("developer_api_keys.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    usage_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True) # YYYY-MM-DD
    requests_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_shots: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spend: Mapped[float] = mapped_column(Numeric(12, 6), default=0.0, nullable=False)

    api_key: Mapped["ApiKey"] = relationship("ApiKey", back_populates="rollups", lazy="selectin")
