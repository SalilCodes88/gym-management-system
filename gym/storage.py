from __future__ import annotations

import json
from datetime import datetime, date
from typing import Any, Dict
from pathlib import Path

from gym.memberships import BaseMembership, PremiumMembership, BasicMembership
from gym.pricing import NoDiscount, PercentOff, FixedPrice, PricePolicy
from gym.gym import MembershipStatus, PaymentStatus, ValidationError, Gym
from gym.people import Member, Trainer
from gym.workouts import Exercise, WorkoutPlan, WorkoutCatalog
from gym.payments import PaymentRecord, InMemoryPaymentLedger, FakePaymentProcessor


def price_policy_to_dict(policy: PricePolicy) -> Dict[str, Any]:
    if isinstance(policy, NoDiscount):
        return {"type": "no_discount"}
    if isinstance(policy, PercentOff):
        return {"type": "percent_off", "discount": policy.discount}
    if isinstance(policy, FixedPrice):
        return {"type": "fixed_price", "price": policy.price}
    
    raise ValidationError (f"Unknown policy type: {type(policy).__name__}")

def price_policy_from_dict(data: Dict[str, Any]) -> PricePolicy:
    policy_type = data.get("type")

    if policy_type == "no_discount":
        return NoDiscount()
    if policy_type == "percent_off":
        return PercentOff(discount=float(data["discount"]))
    if policy_type == "fixed_price":
        return FixedPrice(price=float(data["price"]))
    
    raise ValidationError (f"Unknown policy type: {policy_type}")

def membership_to_dict(membership: BaseMembership) -> Dict[str, Any]:
    if isinstance(membership, BaseMembership):
        membership_type = "basic"
    elif isinstance(membership, PremiumMembership):
        membership_type = "premium"
    else:
        raise ValidationError (f"Unknown membership type: {type(membership).__name__}")
    
    return {
        "type": membership_type,
        "status": membership.status.value,
        "price_policy": price_policy_to_dict(membership.price_policy),
    }

def membership_from_dict(data: Dict[str, Any]) -> BaseMembership:
    membership_type = data.get("type")
    status_str = data.get("status")
    policy_data = data.get("price_policy")

    policy = price_policy_from_dict(policy_data)
    
    if membership_type == "basic":
        membership = BasicMembership(price_policy=policy)
    elif membership_type == "premium":
        membership = PremiumMembership(price_policy=policy)
    else:
        raise ValidationError (f"Unknown membership type: {membership_type}")
    
    membership.status = MembershipStatus(status_str)
    return membership

def member_to_dict(member: Member) -> Dict[str, Any]:
    if not isinstance(member, Member):
        raise ValidationError ("Expected member instance.")
    
    return{
        "id": member.id,
        "full_name": member.full_name,
        "email": member.email,
        "join_date": member.join_date.isoformat(),
        "membership": membership_to_dict(member.membership)
    }

def member_from_dict(data: Dict[str, Any]) -> Member:
    if not isinstance(data, Dict):
        raise ValidationError ("Member data must be a dictionary.")
    full_name = data.get("full_name")
    email = data.get("email")
    
    if not full_name or not str(full_name).strip():
        raise ValidationError ("Member missing full name.")
    if not email and not str(email).strip():
        raise ValidationError ("Trainer missing email.")
    
    member = Member(
        full_name=full_name,
        email=email,
        membership= membership_from_dict(data["membership"])
    )

    stored_id = data.get("id")
    if stored_id:
        member.id = str(stored_id)
    return member

def trainer_to_dict(trainer: Trainer) -> Dict[str, Any]:
    if not isinstance(trainer, Trainer):
        raise ValidationError ("Expected Trainer instance")
    
    return {
        "id": trainer.id,
        "full_name": trainer.full_name,
        "email": trainer.email,
        "specialty": trainer.specialty,
    }

def trainer_from_dict(data: Dict[str, Any]) -> Trainer:
    if not isinstance(data, Dict):
        raise ValidationError ("Trainer data must be a dictionary.")
    
    full_name = data.get("full_name")
    email = data.get("email")

    if not full_name or not str(full_name).strip():
        raise ValidationError ("Trainer full name missing.")
    if not email or not str(email).strip():
        raise ValidationError ("Trainer email missing.")
    
    trainer = Trainer(full_name=full_name,
                      email=email,
                      specialty=data.get("specialty"),
                      )
    stored_id = data.get("id")
    if stored_id:
        trainer.id = stored_id
    
    return trainer

def exercise_to_dict(exercise: Exercise) -> Dict[str, Any]:
    if not isinstance(exercise, Exercise):
        raise ValidationError ("exercise instance expected.")
    
    return {
        "name": exercise.name,
        "sets": exercise.sets,
        "reps": exercise.reps,
        "load": exercise.load,
        "notes": exercise.notes,
    }

def exercise_from_dict(data: Dict[str, Any]) -> Exercise:
    if not isinstance(data, dict):
        raise ValidationError ("Exercise data must be a dictionary.")
    
    name = data.get("name")
    if not name or not str(name).strip():
        raise ValidationError ("Exercise name missing.")
    
    return Exercise(
        name=str(name),
        sets= int(data.get("sets", 0)),
        reps= int(data.get("reps", 0)),
        load= (None if data.get("load") is None else float(data["load"])),
        notes= (None if data.get("notes") is None else str(data["notes"]))
    )

def workout_plan_to_dict(plan: WorkoutPlan) -> Dict[str, Any]:
    if not isinstance(plan, WorkoutPlan):
        raise ValidationError ("Expected a workout plan instance.")
    
    return {
        "id": plan.id,
        "member_id": plan.member_id,
        "title": plan.title,
        "created_at": plan.created_at.isoformat(),
        "exercises": [exercise_to_dict(e) for e in plan.exercises],
    }

def workout_plan_from_dict(data: Dict) -> WorkoutPlan:
    if not isinstance(data, dict):
        raise ValidationError ("Workout plan data must be a dictionary.")
    member_id = data.get("member_id")
    title = data.get("title")

    if not member_id or not str(member_id).strip():
        raise ValidationError ("WorkoutPlan missing member_id.")
    if not title or not str(title).strip():
        raise ValidationError ("WorkoutPlan missing title.")
    
    plan = WorkoutPlan(member_id=member_id, title=title)

    stored_id = str(data.get("id"))
    if stored_id:
        plan.id = stored_id

    created_at = data.get("created_at")
    if created_at:
        plan.created_at = datetime.fromisoformat(str(created_at))

    exercise_data = data.get("exercises", [])
    if not isinstance(exercise_data, list):
        raise ValidationError ("WorkoutPlan.exercises must be a list.")
    for ex in exercise_data:
        plan.add_exercise(exercise_from_dict(ex))

    return plan

def workout_catalog_to_dict(cat: WorkoutCatalog) -> Dict[str, Any]:
    if not isinstance(cat, WorkoutCatalog):
        raise ValidationError ("WorkoutCatalog instance expected.")
    
    return {
        "plans": {pid: workout_plan_to_dict(plan) for pid , plan in cat.plans.items()}
    }

def workout_catalog_from_dict(data: Dict[str, Any]) -> WorkoutCatalog:
    if not isinstance(data, dict):
        raise ValidationError ("WorkoutCatalog data must be a Dictionary.")
    
    cat = WorkoutCatalog()

    plans_data = data.get("plans", {})

    if not isinstance (plans_data, dict):
        raise ValidationError ("WorkoutCatalog.plans must be a dictionary.")
    
    for _, plan_data in plans_data.items():
        plan = workout_plan_from_dict(plan_data)
        cat.plans[plan.id] = plan
        cat.plans_by_member.setdefault(plan.member_id, []).append(plan.id)

    return cat

def payment_record_to_dict(record: PaymentRecord) -> Dict[str, Any]:
    if not isinstance(record, PaymentRecord):
        raise ValidationError ("PaymentRecord Instance expected.")
    
    return {
        "id": record.id,
        "member_id": record.member_id,
        "member_name": record.member_name,
        "amount": record.amount,
        "status": record.status.value,
        "message": record.message,
        "created_at": record.created_at.isoformat(),
    }

def payment_record_from_dict(data: Dict[str, Any]) -> PaymentRecord:
    if not isinstance(data, dict):
        raise ValidationError ("PaymentRecord must be a Dictionary.")
    
    member_id = data.get("member_id")
    if not member_id or not str(member_id).strip():
        raise ValidationError ("PaymentRecord missing member id.")

    member_name = data.get("member_name")
    if not member_name or not str(member_name).strip():
        raise ValidationError ("PaymentRecord missing member_name.")
    
    amount_raw= data.get("amount")
    try:
        amount = float(amount_raw)
    except (TypeError, ValueError):
        raise ValidationError ("PaymentRecord amount must be a positive number.")
    if amount < 0:
        raise ValidationError ("PaymentRecord amount must be greater than 0.")
    
    status_str = data.get("status")
    if not status_str or not str(status_str).strip():
        raise ValidationError ("PaymentRecord missing payment status")
    status = PaymentStatus(str(status_str))
    
    message = data.get("message")
    if not message or not str(message).strip():
        raise ValidationError ("PaymentRecord missing message.")
    
    record = PaymentRecord.create(
        member_id= str(member_id).strip(),
        member_name=str(member_name).strip(),
        amount=amount,
        status= status,
        message= str(message).strip()
    )

    stored_id = data.get("id")
    if stored_id:
        object.__setattr__(record, "id", str(stored_id))

    created_at = data.get("created_at")
    if created_at:
        object.__setattr__(record, "created_at", datetime.fromisoformat(str(created_at)))

    return record

def ledger_to_dict(ledger: InMemoryPaymentLedger) -> Dict[str, Any]:
    if not isinstance(ledger, InMemoryPaymentLedger):
        raise ValidationError ("InMemoryPaymentLedger instance expected.")
    
    return {
        "records": [payment_record_to_dict(r) for r in ledger.records]
    }

def ledger_from_dict(data: Dict[str, Any]) -> InMemoryPaymentLedger:
    if not isinstance(data, dict):
        raise ValidationError ("InMemoryPaymentLedger data must be a Dictionary.")
    
    records_data = data.get("records", [])
    if not isinstance(records_data, list):
        raise ValidationError ("Ledger.records must be a list.")
    
    ledger = InMemoryPaymentLedger()

    for rdata in records_data:
        ledger.add(payment_record_from_dict(rdata))

    return ledger

def gym_to_dict(gym: Gym) -> Dict[str, Any]:
    if not isinstance(gym, Gym):
        raise ValidationError ("Gym instance expected.")
    
    return {
        "name": gym.name,
        "members": {mid: member_to_dict(member) for mid, member in gym.members.items()},
        "trainers": {tid: trainer_to_dict(trainer) for tid, trainer in gym.trainers.items()},
        "payment_processor": {
            "type": "fake",
            "fail_threshold": getattr(gym.payment_processor, "fail_threshold", None)
        },
        "workouts": workout_catalog_to_dict(gym.workouts),
        "payment_ledger": ledger_to_dict(gym.payment_ledger),
    }
def gym_from_dict(data: Dict[str, Any]) -> Gym:
    if not isinstance(data, dict):
        raise ValidationError ("Gym data must be a dictionary.")
    
    name = data.get("name")
    if not name or not str(name).strip():
        raise ValidationError ("Gym missing name.")
    
    gym = Gym(name=name)
    
    members_data = data.get("members")
    if not isinstance(members_data, dict):
        raise ValidationError ("Members data must be a dictionary.")
    for _, member_data in members_data.items():
        member = member_from_dict(member_data)
        gym.members[member.id] = member
        gym.members_by_email[member.email.lower().strip()] = member.id

    trainers_data = data.get("trainers")
    if not isinstance(trainers_data, dict):
        raise ValidationError ("Trainers data must be a dictionary.")
    for _, trainer_data in trainers_data.items():
        trainer = trainer_from_dict(trainer_data)
        gym.trainers[trainer.id] = trainer
        gym.trainers_by_email[trainer.email.lower().strip()] = trainer.id

    gym.workouts = workout_catalog_from_dict(data.get("workouts", {}))
    gym.payment_ledger = ledger_from_dict(data.get("payment_ledger", {}))

    pp_data = data.get("payment_processor", {})
    pp_type = pp_data.get("type", "fake")

    if pp_type == "fake":
        gym.payment_processor = FakePaymentProcessor(fail_threshold = pp_data.get("fail_threshold"))

    else:
        raise ValidationError (f"Unknown payment processor {pp_type}")
    
    return gym

CURRENT_SCHEMA_VERSION = 1

def save_gym(gym: Gym, filepath: str | Path) -> None:
    if not isinstance(gym, Gym):
        raise ValidationError ("save_gym expects a gym instance.")
    
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload: Dict[str, Any] = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "gym": gym_to_dict(gym)
    }

    tmp_path = path.with_suffix(path.suffix + ".tmp")

    with tmp_path.open("w", encoding= "utf-8") as f:
        json.dump(payload, f, ensure_ascii= False, indent= 2)

    tmp_path.replace(path)

def load_gym(filepath : str | Path) -> Gym:
    path = Path(filepath)
    if not path.exists():
        raise ValidationError (f"No save file found at {path}")
    
    with path.open("r", encoding= "utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, dict):
        raise ValidationError ("Unexpected save file format: expected json instance at root.")
    
    version = payload.get("schema_version")
    if version != CURRENT_SCHEMA_VERSION:
        raise ValidationError (f"Unsupported schema version: expected {CURRENT_SCHEMA_VERSION}.")
    
    gym_data = payload.get("gym")
    if not isinstance(gym_data, dict):
        raise ValidationError ("Invalid save file format: missing 'gym' object.")
    
    return gym_from_dict(gym_data)