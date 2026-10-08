from typing import Protocol
from threading import Lock

from .repair_contracts import DraftPlan


class PlanRepository(Protocol):
    def save(self, plan: DraftPlan) -> None: ...
    def get(self, plan_id: str) -> DraftPlan | None: ...


class MemoryPlanRepository:
    """Temporary process-local storage, lost on restart; bounded to 100 drafts."""

    def __init__(self):
        self._plans: dict[str, DraftPlan] = {}
        self._lock = Lock()

    def save(self, plan: DraftPlan) -> None:
        with self._lock:
            if len(self._plans) >= 100 and plan.id not in self._plans:
                del self._plans[next(iter(self._plans))]
            self._plans[plan.id] = plan.model_copy(deep=True)

    def get(self, plan_id: str) -> DraftPlan | None:
        with self._lock:
            plan = self._plans.get(plan_id)
            return plan.model_copy(deep=True) if plan else None
