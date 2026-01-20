from __future__ import annotations

from dataclasses import dataclass, field
from abc import abstractmethod, ABC
from typing import Optional, List
from datetime import datetime

from gym.gym import new_id, PaymentStatus, ValidationError

@dataclass(frozen=True, init=False)
class PaymentRecord():
    id: str
    member_id: str
    member_name: str
    amount: float
    status: PaymentStatus
    message: str
    created_at: datetime

    @classmethod
    def create(cls,
                *,
                member_id: str,
                member_name: str,
                amount: float,
                status: PaymentStatus,
                message: str):
        if not member_id or not member_id.strip():
            raise ValidationError ("Member id cannot be empty")
        if not member_name or not member_name.strip():
            raise ValidationError ("Member cannot be empty.")
        if amount < 0:
            raise ValidationError ("Amount cannot be less than 0.")
        if not message or not message.strip():
            raise ValidationError ("Message cannot be empty.")
        
        return cls(
            id = new_id("pay"),
            member_id = member_id.strip(),
            member_name = member_name.strip(),
            amount = amount,
            status = status,
            message= message.strip(),
            created_at = datetime.now()
        )
    
class BasePaymentProcessor(ABC):
    @abstractmethod
    def charge(self, *, member_id: str, member_name: str, amount: float) -> PaymentRecord:
        ...

class FakePaymentProcessor(BasePaymentProcessor):
    fail_threshold: Optional[float] = None

    def charge(self, *, member_id, member_name, amount):
        if self.fail_threshold is not None and amount > self.fail_threshold:
            return PaymentRecord.create(
                member_id= member_id,
                member_name= member_name,
                amount=amount,
                status= PaymentStatus.FAILED,
                message="Simulated Failure, amount exceeds threshold"
            )
        return PaymentRecord.create(
            member_id=member_id,
            member_name=member_name,
            amount=amount,
            status=PaymentStatus.SUCCESS,
            message="Payment sucessfully processed"
        )
    
@dataclass
class InMemoryPaymentLedger():
    records :List[PaymentRecord] = field(default_factory=list)

    def add(self, record: PaymentRecord) -> None:
        if not isinstance(record, PaymentRecord):
            raise ValidationError ("Must be a payment record object.")
        self.records.append(record)

    def list_all(self) -> List[PaymentRecord]:
        return self.records
    
    def list_all_for_member(self, member_id: str) -> List[PaymentRecord]:
        return [r for r in self.records if r.member_id == member_id]
    
    def total_success_for_member(self, member_id: str) -> float:
        return sum(r.amount for r in self.records 
                   if (r.member_id == member_id and r.status == PaymentStatus.SUCCESS))
    
    def total_success_for_all(self) -> float:
        return sum(r.amount for r in self.records if r.status == PaymentStatus.SUCCESS)
    