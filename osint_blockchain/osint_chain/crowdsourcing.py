"""
Crowdsourcing Module for HybridChain-OSINT OS

Enables community-driven OSINT investigations with:
- Public evidence submission
- Community verification and voting
- Reputation system for contributors
- Collaborative investigation workflows
- Consensus mechanisms for information verification
"""

import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum


class CommunityRole(str, Enum):
    """Community member roles"""
    PUBLIC_CONTRIBUTOR = "public_contributor"  # Can submit evidence for review
    VERIFIED_ANALYST = "verified_analyst"      # Can verify evidence
    SENIOR_ANALYST = "senior_analyst"          # Higher voting weight
    MODERATOR = "moderator"                    # Can resolve disputes


class VerificationVote(str, Enum):
    """Verification vote types"""
    AUTHENTIC = "authentic"
    SUSPICIOUS = "suspicious"
    FABRICATED = "fabricated"
    NEEDS_MORE_INFO = "needs_more_info"


class ReputationAction(str, Enum):
    """Actions that affect reputation"""
    SUBMIT_EVIDENCE = "submit_evidence"
    VERIFY_CORRECT = "verify_correct"
    VERIFY_INCORRECT = "verify_incorrect"
    EVIDENCE_VERIFIED = "evidence_verified"
    EVIDENCE_REJECTED = "evidence_rejected"
    HELP_SOLVE_CASE = "help_solve_case"


# Reputation points for various actions
REPUTATION_POINTS = {
    ReputationAction.SUBMIT_EVIDENCE: 5,
    ReputationAction.VERIFY_CORRECT: 10,
    ReputationAction.VERIFY_INCORRECT: -15,
    ReputationAction.EVIDENCE_VERIFIED: 20,
    ReputationAction.EVIDENCE_REJECTED: -10,
    ReputationAction.HELP_SOLVE_CASE: 100,
}


class CommunityMember:
    """Represents a community member in the crowdsourcing system"""

    def __init__(
        self,
        member_id: str,
        username: str,
        role: CommunityRole,
        reputation: int = 0,
        public_key: Optional[str] = None,
        join_date: Optional[float] = None,
    ):
        self.member_id = member_id
        self.username = username
        self.role = role
        self.reputation = reputation
        self.public_key = public_key
        self.join_date = join_date or time.time()
        self.verifications_count = 0
        self.submissions_count = 0
        self.verification_accuracy = 0.0

    def can_verify(self) -> bool:
        """Check if member can participate in verification"""
        return self.role in [
            CommunityRole.VERIFIED_ANALYST,
            CommunityRole.SENIOR_ANALYST,
            CommunityRole.MODERATOR,
        ]

    def get_vote_weight(self) -> float:
        """Calculate voting weight based on role and reputation"""
        base_weights = {
            CommunityRole.PUBLIC_CONTRIBUTOR: 0.0,
            CommunityRole.VERIFIED_ANALYST: 1.0,
            CommunityRole.SENIOR_ANALYST: 2.0,
            CommunityRole.MODERATOR: 3.0,
        }
        weight = base_weights.get(self.role, 1.0)

        # Reputation multiplier (capped at 2x)
        reputation_multiplier = min(1.0 + (self.reputation / 1000), 2.0)

        # Accuracy multiplier
        accuracy_multiplier = 0.5 + (self.verification_accuracy * 0.5)

        return weight * reputation_multiplier * accuracy_multiplier

    def update_reputation(self, action: ReputationAction):
        """Update reputation based on action"""
        points = REPUTATION_POINTS.get(action, 0)
        self.reputation += points

        # Ensure reputation doesn't go below 0
        if self.reputation < 0:
            self.reputation = 0

    def to_dict(self) -> Dict:
        return {
            "member_id": self.member_id,
            "username": self.username,
            "role": self.role,
            "reputation": self.reputation,
            "public_key": self.public_key,
            "join_date": self.join_date,
            "verifications_count": self.verifications_count,
            "submissions_count": self.submissions_count,
            "verification_accuracy": self.verification_accuracy
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CommunityMember':
        member = cls(
            member_id=data["member_id"],
            username=data["username"],
            role=CommunityRole(data["role"]),
            reputation=data.get("reputation", 0),
            public_key=data.get("public_key"),
            join_date=data.get("join_date")
        )
        member.verifications_count = data.get("verifications_count", 0)
        member.submissions_count = data.get("submissions_count", 0)
        member.verification_accuracy = data.get("verification_accuracy", 0.0)
        return member


class EvidenceSubmission:
    """Community-submitted evidence pending verification

    Submissions can be linked to collection tasks posted by investigators,
    fulfilling specific evidence gathering requirements.
    """

    def __init__(
        self,
        submission_id: str,
        submitter_id: str,
        evidence_data: Dict[str, Any],
        timestamp: float,
        case_id: Optional[str] = None,
        task_id: Optional[str] = None  # Links to a collection task
    ):
        self.submission_id = submission_id
        self.submitter_id = submitter_id
        self.evidence_data = evidence_data
        self.timestamp = timestamp
        self.case_id = case_id
        self.task_id = task_id  # Which collection task this fulfills
        self.votes: List[Dict] = []
        self.status = "pending"  # pending, accepted, rejected
        self.consensus_reached_at: Optional[float] = None

    def add_vote(
        self,
        voter_id: str,
        vote: VerificationVote,
        vote_weight: float,
        comment: str = ""
    ):
        """Add a verification vote"""
        self.votes.append({
            "voter_id": voter_id,
            "vote": vote,
            "weight": vote_weight,
            "comment": comment,
            "timestamp": time.time()
        })

    def calculate_consensus(self, threshold: float = 0.6) -> Optional[str]:
        """
        Calculate consensus based on weighted votes.
        Returns 'accepted' or 'rejected' if consensus reached, None otherwise.
        """
        if not self.votes:
            return None

        total_weight = sum(v["weight"] for v in self.votes)
        authentic_weight = sum(
            v["weight"] for v in self.votes
            if v["vote"] == VerificationVote.AUTHENTIC
        )
        fabricated_weight = sum(
            v["weight"] for v in self.votes
            if v["vote"] == VerificationVote.FABRICATED
        )

        authentic_ratio = authentic_weight / total_weight if total_weight > 0 else 0
        fabricated_ratio = fabricated_weight / total_weight if total_weight > 0 else 0

        if authentic_ratio >= threshold:
            return "accepted"
        elif fabricated_ratio >= threshold:
            return "rejected"

        return None

    def to_dict(self) -> Dict:
        return {
            "submission_id": self.submission_id,
            "submitter_id": self.submitter_id,
            "evidence_data": self.evidence_data,
            "timestamp": self.timestamp,
            "case_id": self.case_id,
            "task_id": self.task_id,
            "votes": self.votes,
            "status": self.status,
            "consensus_reached_at": self.consensus_reached_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'EvidenceSubmission':
        submission = cls(
            submission_id=data["submission_id"],
            submitter_id=data["submitter_id"],
            evidence_data=data["evidence_data"],
            timestamp=data["timestamp"],
            case_id=data.get("case_id"),
            task_id=data.get("task_id")
        )
        submission.votes = data.get("votes", [])
        submission.status = data.get("status", "pending")
        submission.consensus_reached_at = data.get("consensus_reached_at")
        return submission


class CrowdsourcingManager:
    """Manages community members, submissions, and verification workflows"""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.members_file = self.data_dir / "community_members.json"
        self.submissions_file = self.data_dir / "community_submissions.jsonl"

        self.members: Dict[str, CommunityMember] = {}
        self.submissions: Dict[str, EvidenceSubmission] = {}

        self._load_data()

    def _load_data(self):
        """Load community data from disk"""
        # Load members
        if self.members_file.exists():
            with open(self.members_file, 'r') as f:
                data = json.load(f)
                for member_data in data.values():
                    member = CommunityMember.from_dict(member_data)
                    self.members[member.member_id] = member

        # Load submissions
        if self.submissions_file.exists():
            with open(self.submissions_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        submission = EvidenceSubmission.from_dict(data)
                        self.submissions[submission.submission_id] = submission

    def _save_members(self):
        """Save members to disk"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.members_file, 'w') as f:
            data = {mid: m.to_dict() for mid, m in self.members.items()}
            json.dump(data, f, indent=2)

    def _append_submission(self, submission: EvidenceSubmission):
        """Append submission to file"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.submissions_file, 'a') as f:
            f.write(json.dumps(submission.to_dict()) + '\n')

    def register_member(
        self,
        username: str,
        public_key: str,
        initial_role: CommunityRole = CommunityRole.PUBLIC_CONTRIBUTOR
    ) -> CommunityMember:
        """Register a new community member"""
        import uuid
        member_id = str(uuid.uuid4())

        member = CommunityMember(
            member_id=member_id,
            username=username,
            role=initial_role,
            public_key=public_key
        )

        self.members[member_id] = member
        self._save_members()

        return member

    def submit_evidence(
        self,
        submitter_id: str,
        evidence_data: Dict[str, Any],
        case_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> EvidenceSubmission:
        """Submit evidence for community verification

        Can be linked to a collection task posted by an investigator.
        """
        import uuid

        if submitter_id not in self.members:
            raise ValueError(f"Unknown submitter: {submitter_id}")

        submission_id = str(uuid.uuid4())
        submission = EvidenceSubmission(
            submission_id=submission_id,
            submitter_id=submitter_id,
            evidence_data=evidence_data,
            timestamp=time.time(),
            case_id=case_id,
            task_id=task_id
        )

        self.submissions[submission_id] = submission
        self._append_submission(submission)

        # Update submitter stats
        self.members[submitter_id].submissions_count += 1
        self.members[submitter_id].update_reputation(ReputationAction.SUBMIT_EVIDENCE)
        self._save_members()

        return submission

    def vote_on_submission(
        self,
        submission_id: str,
        voter_id: str,
        vote: VerificationVote,
        comment: str = ""
    ) -> Optional[str]:
        """
        Vote on an evidence submission.
        Returns the new status if consensus is reached, None otherwise.
        """
        if submission_id not in self.submissions:
            raise ValueError(f"Unknown submission: {submission_id}")

        if voter_id not in self.members:
            raise ValueError(f"Unknown voter: {voter_id}")

        member = self.members[voter_id]
        if not member.can_verify():
            raise ValueError(f"Member {voter_id} cannot verify evidence")

        submission = self.submissions[submission_id]

        # Add vote
        vote_weight = member.get_vote_weight()
        submission.add_vote(voter_id, vote, vote_weight, comment)

        # Check for consensus
        consensus = submission.calculate_consensus()
        if consensus:
            submission.status = consensus
            submission.consensus_reached_at = time.time()

            # Update reputations
            submitter = self.members[submission.submitter_id]
            if consensus == "accepted":
                submitter.update_reputation(ReputationAction.EVIDENCE_VERIFIED)
            else:
                submitter.update_reputation(ReputationAction.EVIDENCE_REJECTED)

            # Update voter stats (simplified)
            member.verifications_count += 1

            self._save_members()

        # Rewrite submissions file
        self._rewrite_submissions()

        return consensus

    def _rewrite_submissions(self):
        """Rewrite submissions file"""
        with open(self.submissions_file, 'w') as f:
            for submission in self.submissions.values():
                f.write(json.dumps(submission.to_dict()) + '\n')

    def get_pending_submissions(self, case_id: Optional[str] = None) -> List[EvidenceSubmission]:
        """Get all pending submissions, optionally filtered by case"""
        pending = [s for s in self.submissions.values() if s.status == "pending"]
        if case_id:
            pending = [s for s in pending if s.case_id == case_id]
        return pending

    def get_member_reputation(self, member_id: str) -> Optional[int]:
        """Get member's reputation score"""
        if member_id in self.members:
            return self.members[member_id].reputation
        return None

    def promote_member(self, member_id: str, new_role: CommunityRole):
        """Promote a member to a higher role"""
        if member_id not in self.members:
            raise ValueError(f"Unknown member: {member_id}")

        self.members[member_id].role = new_role
        self._save_members()

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top contributors by reputation"""
        sorted_members = sorted(
            self.members.values(),
            key=lambda m: m.reputation,
            reverse=True
        )
        return [m.to_dict() for m in sorted_members[:limit]]
