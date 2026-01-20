from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from gym.gym import new_id, ValidationError, NotFoundError

@dataclass(frozen=True)
class Exercise:
    name: str
    sets: int
    reps: int
    load: Optional[float]= None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        n = self.name.strip().lower()
        if not n:
            raise ValidationError ("Exercise name cannot be empty.")
        object.__setattr__(self, "name", n)

        if self.sets <= 0:
            raise ValidationError ("Sets must be >= 1")
        if self.reps <= 0:
            raise ValidationError ("Reps must be >= 1")
        if self.load is not None and self.load < 0:
            raise ValidationError ("Load cannot be negative.")
        if self.notes is not None:
            object.__setattr__(self, "notes", self.notes.strip() or None)

@dataclass
class WorkoutPlan:
    member_id: str
    title: str

    id: str = field(init=False)
    created_at: datetime = field(init=False)

    _exercises: List[Exercise] = field(init=False,repr=False)


    def __post_init__(self) -> None:
        if not self.member_id or not self.member_id.strip():
            raise ValidationError ("member_id cannot be empty.")
        self.member_id = self.member_id.strip()

        if not self.title or not self.title.strip():
            raise ValidationError ("title cannot be left empty.")
        self.title = self.title.strip()

        self.id = new_id("wkp")
        self.created_at = datetime.now()

        self._exercises = []

    @property
    def exercises(self) -> Tuple[Exercise,...]:
        return tuple(self._exercises)
    
    def list_exercises_numbered(self) -> List[Tuple[int, Exercise]]:
        return list(enumerate(self.exercises, start=1))
    
    def add_exercise(self, exercise: Exercise):
        if not isinstance(exercise, Exercise):
            raise ValidationError ("add_exercise expects an exercise object.")
        self._exercises.append(exercise)

    def remove_exercise_by_number(self, num: int) -> None:
        if not isinstance(num, int):
            raise ValidationError ("Exercise number must be an integer.")
        if num < 1 or num > len(self._exercises):
            raise ValidationError ("Exercise number out of range.")
        self._exercises.pop(num - 1)

    def remove_exercise_by_name(self, name: str) -> None:
        name_key = name.strip().lower()
        if not name_key:
            raise ValidationError ("Exercise name cannot be empty.")
        
        for ex in self._exercises:
            if ex.name.lower().strip() == name_key:
                self._exercises.remove(ex)
                return
        
        raise ValidationError ("This exercise does not exist in the plan.")
    
    def total_sets(self) -> int:
        return sum(s.sets for s in self._exercises)


@dataclass
class WorkoutCatalog:
    plans: Dict[str, WorkoutPlan] = field(default_factory=dict)
    plans_by_member: Dict[str, List[str]] = field(default_factory=dict)

    def add_plan(self, plan: WorkoutPlan) -> None:
        if not isinstance(plan, WorkoutPlan):
            raise ValidationError ("WorkoutPlan instance expected.")
        if plan.id in self.plans:
            raise ValidationError ("This plan already exists in the system.")
        
        self.plans[plan.id] = plan
        self.plans_by_member.setdefault(plan.member_id, []).append(plan.id)

    def get_plan(self, plan_id: str) -> WorkoutPlan:
        plan = self.plans.get(plan_id)
        if plan is None:
            raise ValidationError (f"Plan with '{plan_id}' does not exist in the system.")
        
        return plan
    
    def list_all_plans_for_member(self, member_id: str) -> List[WorkoutPlan]:
        plans_ids = self.plans_by_member.get(member_id, [])
        return [self.plans[pid] for pid in plans_ids if pid in self.plans]
    
    def remove_plan(self, plan_id: str) -> None:
        plan = self.plans.get(plan_id)
        if plan is None:
            raise ValidationError ("This plan does not exist in the system.")
        
        member_id_key = plan.member_id

        self.plans.pop(plan_id)

        plan_ids = self.plans.get(member_id_key)
        if plan_ids is None:
            raise ValidationError ("Workout index in consistent: member key missing.")
        
        if plan_id not in plan_ids:
            raise ValidationError ("Workout index inconsistent: plan id missing for member.")
        