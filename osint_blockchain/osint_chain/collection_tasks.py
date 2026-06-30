"""
Collection Tasks Module for HybridChain-OSINT OS

Enables investigators to publicly post evidence collection requirements that
the crowdsourced community can help fulfill. This creates a collaborative
intelligence gathering workflow where:

1. Investigators post what evidence they need
2. Community members submit evidence to fulfill tasks
3. Community validates submitted evidence
4. Validated evidence is added to private chain
5. Contributors earn reputation for successful submissions
"""

import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum


class TaskPriority(str, Enum):
    """Priority levels for collection tasks"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Status of a collection task"""
    OPEN = "open"                    # Accepting submissions
    IN_PROGRESS = "in_progress"      # Has submissions under review
    PARTIALLY_FULFILLED = "partially_fulfilled"  # Some evidence accepted
    FULFILLED = "fulfilled"          # Task complete
    CLOSED = "closed"                # No longer accepting submissions


class EvidenceType(str, Enum):
    """Types of evidence that can be requested"""
    SCREENSHOT = "screenshot"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    SOCIAL_MEDIA_POST = "social_media_post"
    URL = "url"
    NETWORK_DATA = "network_data"
    GEOLOCATION = "geolocation"
    METADATA = "metadata"
    ANY = "any"


class CollectionTask:
    """Represents a public collection requirement posted by an investigator."""

    def __init__(
        self,
        task_id: str,
        investigator_id: str,
        title: str,
        description: str,
        evidence_types: List[EvidenceType],
        case_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        quantity_needed: int = 1,
        deadline: Optional[float] = None,
        metadata_requirements: Optional[Dict[str, Any]] = None,
        created_at: Optional[float] = None,
    ):
        self.task_id = task_id
        self.investigator_id = investigator_id
        self.title = title
        self.description = description
        self.evidence_types = evidence_types
        self.case_id = case_id
        self.priority = priority
        self.quantity_needed = quantity_needed
        self.quantity_fulfilled = 0
        self.deadline = deadline
        self.metadata_requirements = metadata_requirements or {}
        self.created_at = created_at or time.time()
        self.status = TaskStatus.OPEN
        self.submissions: List[str] = []  # submission_ids
        self.accepted_submissions: List[str] = []
        self.updated_at = self.created_at

    def add_submission(self, submission_id: str):
        """Record a new evidence submission for this task"""
        if submission_id not in self.submissions:
            self.submissions.append(submission_id)
            self.updated_at = time.time()
            if self.status == TaskStatus.OPEN:
                self.status = TaskStatus.IN_PROGRESS

    def accept_submission(self, submission_id: str):
        """Mark a submission as accepted/validated"""
        if submission_id not in self.accepted_submissions:
            self.accepted_submissions.append(submission_id)
            self.quantity_fulfilled += 1
            self.updated_at = time.time()

            # Update status based on fulfillment
            if self.quantity_fulfilled >= self.quantity_needed:
                self.status = TaskStatus.FULFILLED
            elif self.quantity_fulfilled > 0:
                self.status = TaskStatus.PARTIALLY_FULFILLED

    def close_task(self):
        """Close the task (no longer accepting submissions)"""
        self.status = TaskStatus.CLOSED
        self.updated_at = time.time()

    def is_expired(self) -> bool:
        """Check if the task deadline has passed"""
        if self.deadline is None:
            return False
        return time.time() > self.deadline

    def get_progress_percentage(self) -> float:
        """Calculate task completion percentage"""
        if self.quantity_needed == 0:
            return 100.0
        return min(100.0, (self.quantity_fulfilled / self.quantity_needed) * 100)

    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            "task_id": self.task_id,
            "investigator_id": self.investigator_id,
            "title": self.title,
            "description": self.description,
            "evidence_types": self.evidence_types,
            "case_id": self.case_id,
            "priority": self.priority,
            "quantity_needed": self.quantity_needed,
            "quantity_fulfilled": self.quantity_fulfilled,
            "deadline": self.deadline,
            "metadata_requirements": self.metadata_requirements,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "submissions": self.submissions,
            "accepted_submissions": self.accepted_submissions,
            "progress_percentage": self.get_progress_percentage(),
            "is_expired": self.is_expired()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CollectionTask':
        """Deserialize from dictionary"""
        task = cls(
            task_id=data["task_id"],
            investigator_id=data["investigator_id"],
            title=data["title"],
            description=data["description"],
            evidence_types=[EvidenceType(t) for t in data["evidence_types"]],
            case_id=data.get("case_id"),
            priority=TaskPriority(data.get("priority", "medium")),
            quantity_needed=data.get("quantity_needed", 1),
            deadline=data.get("deadline"),
            metadata_requirements=data.get("metadata_requirements"),
            created_at=data.get("created_at")
        )
        task.quantity_fulfilled = data.get("quantity_fulfilled", 0)
        task.updated_at = data.get("updated_at", task.created_at)
        task.status = TaskStatus(data.get("status", "open"))
        task.submissions = data.get("submissions", [])
        task.accepted_submissions = data.get("accepted_submissions", [])
        return task


class CollectionTaskManager:
    """Manages public collection tasks posted by investigators"""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.tasks_file = self.data_dir / "collection_tasks.jsonl"
        self.tasks: Dict[str, CollectionTask] = {}
        self._load_tasks()

    def _load_tasks(self):
        """Load tasks from disk"""
        if self.tasks_file.exists():
            with open(self.tasks_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        task = CollectionTask.from_dict(data)
                        self.tasks[task.task_id] = task

    def _append_task(self, task: CollectionTask):
        """Append task to file"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.tasks_file, 'a') as f:
            f.write(json.dumps(task.to_dict()) + '\n')

    def _rewrite_tasks(self):
        """Rewrite entire tasks file (for updates)"""
        with open(self.tasks_file, 'w') as f:
            for task in self.tasks.values():
                f.write(json.dumps(task.to_dict()) + '\n')

    def create_task(
        self,
        investigator_id: str,
        title: str,
        description: str,
        evidence_types: List[EvidenceType],
        case_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        quantity_needed: int = 1,
        deadline: Optional[float] = None,
        metadata_requirements: Optional[Dict[str, Any]] = None
    ) -> CollectionTask:
        """Create a new collection task"""
        import uuid

        task_id = str(uuid.uuid4())
        task = CollectionTask(
            task_id=task_id,
            investigator_id=investigator_id,
            title=title,
            description=description,
            evidence_types=evidence_types,
            case_id=case_id,
            priority=priority,
            quantity_needed=quantity_needed,
            deadline=deadline,
            metadata_requirements=metadata_requirements
        )

        self.tasks[task_id] = task
        self._append_task(task)

        return task

    def get_task(self, task_id: str) -> Optional[CollectionTask]:
        """Get a specific task by ID"""
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        case_id: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        investigator_id: Optional[str] = None,
        include_expired: bool = False
    ) -> List[CollectionTask]:
        """List tasks with optional filters"""
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        if case_id:
            tasks = [t for t in tasks if t.case_id == case_id]

        if priority:
            tasks = [t for t in tasks if t.priority == priority]

        if investigator_id:
            tasks = [t for t in tasks if t.investigator_id == investigator_id]

        if not include_expired:
            tasks = [t for t in tasks if not t.is_expired()]

        # Sort by priority (urgent first) then by creation date
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        tasks.sort(key=lambda t: (priority_order.get(t.priority, 2), -t.created_at))

        return tasks

    def get_open_tasks(self) -> List[CollectionTask]:
        """Get all open tasks (accepting submissions)"""
        return self.list_tasks(status=TaskStatus.OPEN, include_expired=False)

    def link_submission(self, task_id: str, submission_id: str):
        """Link an evidence submission to a task"""
        if task_id not in self.tasks:
            raise ValueError(f"Unknown task: {task_id}")

        task = self.tasks[task_id]
        task.add_submission(submission_id)
        self._rewrite_tasks()

    def accept_submission(self, task_id: str, submission_id: str):
        """Mark a submission as accepted for a task"""
        if task_id not in self.tasks:
            raise ValueError(f"Unknown task: {task_id}")

        task = self.tasks[task_id]
        task.accept_submission(submission_id)
        self._rewrite_tasks()

    def close_task(self, task_id: str):
        """Close a task"""
        if task_id not in self.tasks:
            raise ValueError(f"Unknown task: {task_id}")

        task = self.tasks[task_id]
        task.close_task()
        self._rewrite_tasks()

    def get_statistics(self) -> Dict:
        """Get overall collection task statistics"""
        total_tasks = len(self.tasks)
        open_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.OPEN])
        fulfilled_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.FULFILLED])
        total_submissions = sum(len(t.submissions) for t in self.tasks.values())
        total_accepted = sum(len(t.accepted_submissions) for t in self.tasks.values())

        return {
            "total_tasks": total_tasks,
            "open_tasks": open_tasks,
            "fulfilled_tasks": fulfilled_tasks,
            "in_progress_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
            "closed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.CLOSED]),
            "total_submissions": total_submissions,
            "total_accepted_submissions": total_accepted,
            "acceptance_rate": (total_accepted / total_submissions * 100) if total_submissions > 0 else 0
        }
