"""Shared scripted paths and reproducible exploration runs for local clients."""

import random
import secrets
from dataclasses import asdict, dataclass
from typing import Any

from backend.app.scenario_engine.loader import load_scenario


@dataclass(frozen=True)
class DemoDefinition:
    """One scripted path that demonstrates a useful POC review story."""

    demo_id: str
    label: str
    short_label: str
    scenario_id: str
    tone: str
    description: str
    actions: tuple[str, ...]
    mode: str = "scripted"
    seed: int | None = None
    available_actions: tuple[str, ...] = ()

    def as_public_dict(self) -> dict[str, Any]:
        return asdict(self)


SMOKE_HAPPY = DemoDefinition(
    demo_id="smoke-room-happy",
    label="Smoke-room happy path",
    short_label="Smoke room · expected path",
    scenario_id="smoke_inhalation_room_v0",
    tone="expected",
    description="A clean scripted run that notices the room cues before occupant removal.",
    actions=(
        "assess_scene",
        "check_door",
        "confirm_ppe",
        "request_backup",
        "communicate_status",
        "move_obstacle",
        "open_door",
        "scan_room",
        "check_visibility",
        "monitor_environment",
        "enter_room",
        "locate_occupant",
        "remove_occupant",
    ),
)
SMOKE_WARNING = DemoDefinition(
    demo_id="smoke-room-warning",
    label="Smoke-room warning/error path",
    short_label="Smoke room · review path",
    scenario_id="smoke_inhalation_room_v0",
    tone="review",
    description="A deliberately imperfect run that creates useful review discussion points.",
    actions=(
        "confirm_ppe",
        "enter_room",
        "assess_scene",
        "scan_room",
        "confirm_ppe",
        "check_door",
        "request_backup",
        "open_door",
        "move_obstacle",
        "open_door",
        "scan_room",
        "enter_room",
        "communicate_status",
        "check_visibility",
        "enter_room",
        "monitor_environment",
        "enter_room",
        "remove_occupant",
        "stop_scenario",
    ),
)
HALLWAY_HAPPY = DemoDefinition(
    demo_id="blocked-exit-happy",
    label="Blocked-exit hallway happy path",
    short_label="Blocked exit · expected path",
    scenario_id="blocked_exit_hallway_v0",
    tone="expected",
    description="A clean hallway run that clears the route and guides the occupant to the exit.",
    actions=(
        "assess_scene",
        "scan_hallway",
        "confirm_ppe",
        "request_backup",
        "communicate_status",
        "check_visibility",
        "identify_secondary_exit",
        "move_obstacle",
        "check_exit_door",
        "open_exit_door",
        "monitor_environment",
        "guide_occupant_to_exit",
    ),
)
HALLWAY_WARNING = DemoDefinition(
    demo_id="blocked-exit-warning",
    label="Blocked-exit hallway warning path",
    short_label="Blocked exit · review path",
    scenario_id="blocked_exit_hallway_v0",
    tone="review",
    description="A warning-focused hallway run that acts before the monitoring cue is complete.",
    actions=(
        "assess_scene",
        "scan_hallway",
        "confirm_ppe",
        "request_backup",
        "communicate_status",
        "check_visibility",
        "identify_secondary_exit",
        "move_obstacle",
        "check_exit_door",
        "open_exit_door",
        "guide_occupant_to_exit",
        "monitor_environment",
        "guide_occupant_to_exit",
    ),
)

SMOKE_USER_CONTROLLED = DemoDefinition(
    demo_id="smoke-room-user-controlled",
    label="Smoke-room user-controlled path",
    short_label="Smoke room · choose actions",
    scenario_id="smoke_inhalation_room_v0",
    tone="interactive",
    description=(
        "Choose one action at a time and see how the backend-owned scenario responds. "
        "This is a POC interaction, not protocol guidance or trainee scoring."
    ),
    actions=(),
    mode="user_controlled",
    available_actions=load_scenario("smoke_inhalation_room_v0").allowed_actions,
)

DEMO_DEFINITIONS = (SMOKE_HAPPY, SMOKE_WARNING, HALLWAY_HAPPY, HALLWAY_WARNING)


def generate_exploration_definition(
    scenario_id: str,
    *,
    seed: int | None = None,
) -> DemoDefinition:
    """Create a varied but reproducible simulated-trainee action sequence."""

    definition = load_scenario(scenario_id)
    selected_seed = seed if seed is not None else secrets.randbelow(1_000_000_000)
    generator = random.Random(selected_seed)
    available_actions = [
        action for action in definition.allowed_actions if action != "stop_scenario"
    ]
    shuffled_actions = available_actions.copy()
    generator.shuffle(shuffled_actions)
    retry_count = min(6, len(available_actions))
    retries = [generator.choice(available_actions) for _ in range(retry_count)]
    actions = (*shuffled_actions, *retries, "stop_scenario")
    return DemoDefinition(
        demo_id=f"seeded-exploration-{scenario_id}",
        label=f"Seeded exploration: {definition.title}",
        short_label="Seeded exploration run",
        scenario_id=scenario_id,
        tone="explore",
        description=(
            "A backend-generated simulated-trainee sequence. It may create incomplete or "
            "repeated actions, and the seed makes the exact run reproducible."
        ),
        actions=actions,
        mode="seeded_exploration",
        seed=selected_seed,
    )
