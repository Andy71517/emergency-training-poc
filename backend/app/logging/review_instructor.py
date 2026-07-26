"""Instructor-facing review narrative, headline, observations, and takeaways."""

from typing import Any

from backend.app.logging.review_timeline import friendly_state


def build_instructor_review(
    *,
    action_count: int,
    validation_counts: dict[str, int],
    end_reached: bool,
    final_state: dict[str, Any],
    environment: dict[str, Any],
    progress_stories: list[str],
) -> dict[str, Any]:
    """Create a final discussion aid from recorded POC evidence."""

    room_cues = environment.get("room_cues") or {}
    completed_cues = [
        label
        for field, label in (
            ("room_scanned", "area check"),
            ("door_checked", "door check"),
            ("status_communicated", "status communication"),
            ("environment_monitored", "environment monitoring"),
            ("exit_path_clear", "clear exit path"),
        )
        if room_cues.get(field)
    ]
    missing_cues = [
        label
        for field, label in (
            ("room_scanned", "area check"),
            ("door_checked", "door check"),
            ("status_communicated", "status communication"),
            ("environment_monitored", "environment monitoring"),
            ("exit_path_clear", "clear exit path"),
        )
        if not room_cues.get(field)
    ]
    finding_count = validation_counts.get("warning", 0) + validation_counts.get("error", 0)
    if finding_count:
        opening = (
            f"This session recorded {action_count} actions and {finding_count} POC review "
            f"finding{'s' if finding_count != 1 else ''}."
        )
    else:
        opening = f"This session recorded {action_count} actions with no POC review findings."

    evidence = [
        f"The scenario end condition was {'reached' if end_reached else 'not reached'}.",
        f"The final recorded outcome was {friendly_state(final_state.get('scenario_outcome'))}.",
        "Completed cues: " + (", ".join(completed_cues) if completed_cues else "none recorded") + ".",
        "Still missing: " + (", ".join(missing_cues) if missing_cues else "none") + ".",
    ]
    if progress_stories:
        evidence.append(
            f"The review identified {len(progress_stories)} blocked-or-flagged action "
            f"retr{'y' if len(progress_stories) == 1 else 'ies'} that can be discussed."
        )

    if progress_stories:
        discussion_prompt = (
            "Ask the trainee to explain what they noticed, what changed before the retry, "
            "and what they would want to review with an instructor."
        )
    elif missing_cues:
        discussion_prompt = (
            "Ask the trainee what they noticed, which recorded cues remained unresolved, "
            "and what they would want to review with an instructor."
        )
    else:
        discussion_prompt = (
            "Ask the trainee what they noticed, how the recorded sequence moved the scenario "
            "forward, and what they would want to review with an instructor."
        )

    return {
        "title": "Instructor review message",
        "summary": opening,
        "evidence": evidence,
        "discussion_prompt": discussion_prompt,
        "boundary": (
            "This is a deterministic POC discussion aid, not a grade, validated rubric, "
            "or operational judgment."
        ),
    }


def review_headline(
    *,
    validation_counts: dict[str, int],
    end_reached: bool,
    final_phase: str | None,
) -> str:
    if validation_counts.get("error"):
        return "The run included an error that stopped at least one attempted action."
    if validation_counts.get("warning"):
        return "The run completed with POC warnings worth discussing in review."
    if end_reached:
        return "The run reached an end condition without recorded POC findings."
    return f"The run ended in phase '{final_phase or 'unknown'}' without reaching an end condition."


def key_observations(
    *,
    action_count: int,
    validation_counts: dict[str, int],
    end_reached: bool,
    environment: dict[str, Any],
) -> list[str]:
    observations = [
        f"The log captured {action_count} trainee action(s) in order.",
        f"The scenario end condition was {'reached' if end_reached else 'not reached'}.",
    ]
    if validation_counts.get("warning") or validation_counts.get("error"):
        observations.append(
            "The run included POC rule findings that are useful for review, not real-world scoring."
        )
    else:
        observations.append("No POC warnings or errors were recorded.")

    chair = environment.get("wooden_chair_poc")
    if chair:
        observations.append(
            "The wooden chair cue was "
            + ("cleared during the run." if chair.get("moved") else "still unresolved at the end.")
        )
    door = environment.get("entry_door_poc")
    if door:
        observations.append(
            "The entry door ended "
            + ("open." if door.get("open") else "closed or blocking the path.")
        )
    visibility = environment.get("smoke_visibility_cue_poc")
    if visibility:
        observations.append(
            "The smoke/visibility cue was "
            + ("checked before the final state." if visibility.get("observed") else "still unchecked at the end.")
        )
    room_cues = environment.get("room_cues")
    if room_cues:
        observations.append(
            "The room-level cues show "
            f"scan={_yes_no(bool(room_cues.get('room_scanned')))}, "
            f"communication={_yes_no(bool(room_cues.get('status_communicated')))}, "
            f"monitoring={_yes_no(bool(room_cues.get('environment_monitored')))}, "
            f"occupant located={_yes_no(bool(room_cues.get('occupant_located')))}."
        )
    return observations


def reviewer_takeaways(
    *,
    warnings: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> list[str]:
    takeaways = [
        "This review explains deterministic POC behavior, not clinical or operational authority."
    ]
    if warnings:
        takeaways.append("Warnings show cues or sequence issues the scenario can discuss afterward.")
    if errors:
        takeaways.append("Errors show actions that did not conform to the toy scenario rules.")
    if not warnings and not errors:
        takeaways.append("The run followed the expected POC path without recorded findings.")
    return takeaways


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
