from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional

class PrimitiveType(Enum):
    ACTOR = "actor"
    GOAL = "goal"
    DATA_ENTITY = "data_entity"
    CONSTRAINT = "constraint"
    ASSUMPTION = "assumption"

class GapPriority(Enum):
    P1 = 1  # Blocker (Missing Actor, Missing Core Job/Why)
    P2 = 2  # High (Missing Outcome/SLA, Missing Situation Context)
    P3 = 3  # Medium (Edge case, Unvalidated Assumption)

class GapCategory(Enum):
    STRUCTURAL_ORPHANED_GOAL = "structural_orphaned_goal"
    STRUCTURAL_MISSING_ENTITY = "structural_missing_entity"
    STRUCTURAL_FLOATING_CONSTRAINT = "structural_floating_constraint"
    SEMANTIC_JTBD_WHY = "semantic_jtbd_why"
    SEMANTIC_JTBD_WHEN = "semantic_jtbd_when"
    SEMANTIC_JTBD_OUTCOME = "semantic_jtbd_outcome"
    SEMANTIC_UNMEASURABLE_CONSTRAINT = "semantic_unmeasurable_constraint"
    SEMANTIC_UNHANDLED_FAILURE = "semantic_unhandled_failure"

@dataclass(frozen=True)
class Actor:
    id: str
    name: str
    role: str
    description: str = ""

@dataclass(frozen=True)
class Goal:
    id: str
    description: str
    actor_ids: List[str] = field(default_factory=list)
    entity_ids: List[str] = field(default_factory=list)
    # JTBD Fields
    situation_trigger: Optional[str] = None  # "When [situation]..."
    underlying_motivation: Optional[str] = None  # "I want to [motivation]..."
    desired_outcome: Optional[str] = None  # "So that I can [outcome]..."
    failure_modes: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class DataEntity:
    id: str
    name: str
    fields: List[str] = field(default_factory=list)
    description: str = ""

@dataclass(frozen=True)
class Constraint:
    id: str
    description: str
    target_id: Optional[str] = None  # Goal or DataEntity ID
    is_measurable: bool = False
    sla_metric: Optional[str] = None

@dataclass(frozen=True)
class Assumption:
    id: str
    description: str
    validated: bool = False

@dataclass(frozen=True)
class Edge:
    source_id: str
    target_id: str
    relation: str  # e.g., "PERFORMS", "OPERATES_ON", "CONSTRAINED_BY"

@dataclass
class KnowledgeMap:
    actors: Dict[str, Actor] = field(default_factory=dict)
    goals: Dict[str, Goal] = field(default_factory=dict)
    entities: Dict[str, DataEntity] = field(default_factory=dict)
    constraints: Dict[str, Constraint] = field(default_factory=dict)
    assumptions: Dict[str, Assumption] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)

    def add_actor(self, actor: Actor) -> None:
        self.actors[actor.id] = actor

    def add_goal(self, goal: Goal) -> None:
        self.goals[goal.id] = goal
        for actor_id in goal.actor_ids:
            self.edges.append(Edge(source_id=actor_id, target_id=goal.id, relation="PERFORMS"))
        for entity_id in goal.entity_ids:
            self.edges.append(Edge(source_id=goal.id, target_id=entity_id, relation="OPERATES_ON"))

    def add_entity(self, entity: DataEntity) -> None:
        self.entities[entity.id] = entity

    def add_constraint(self, constraint: Constraint) -> None:
        self.constraints[constraint.id] = constraint
        if constraint.target_id:
            self.edges.append(Edge(source_id=constraint.target_id, target_id=constraint.id, relation="CONSTRAINED_BY"))

    def add_assumption(self, assumption: Assumption) -> None:
        self.assumptions[assumption.id] = assumption

@dataclass(frozen=True)
class Gap:
    id: str
    category: GapCategory
    target_id: str
    description: str
    priority: GapPriority

@dataclass(frozen=True)
class Question:
    id: str
    gap_id: str
    target_id: str
    question_text: str
    priority: GapPriority

@dataclass
class EngineeringOutputs:
    requirements: List[str]
    spec: str
    jtbd_matrix: List[Dict[str, str]]
    acceptance_criteria: List[str]
