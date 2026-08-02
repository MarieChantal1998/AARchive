from datetime import date, datetime, timezone

from .models import Brief, ProcessingStatus, Project, Scene

DEMO_VIDEO = "https://d34w7g4gy10iej.cloudfront.net/video/2606/DOD_111741836/DOD_111741836-1920x1080-9000k.mp4"
DEMO_THUMBNAIL = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/USAG-Italy_DES_Integrated_Emergency_Exercise_%281008879%29.webm/960px--USAG-Italy_DES_Integrated_Emergency_Exercise_%281008879%29.webm.jpg"


def demo_project(video_url: str = "") -> Project:
    return Project(
        project_id="demo-coordinated-response",
        title="Integrated Emergency Response Exercise",
        exercise_type="Emergency response / triage",
        exercise_date=date(2026, 4, 29),
        description="Public-domain emergency-response exercise footage used as a demonstration dataset.",
        duration_seconds=57,
        status=ProcessingStatus.ready,
        status_message="Preprocessed demonstration",
        thumbnail_url=DEMO_THUMBNAIL,
        video_url=video_url or DEMO_VIDEO,
        indexed_scene_count=5,
        brief_count=1,
        storage="public_demo",
        seeded_demo=True,
        source_attribution="Public-domain U.S. Army video via Wikimedia Commons / DVIDS.",
        created_at=datetime(2026, 6, 2, 12, 11, tzinfo=timezone.utc),
    )


DEMO_SCENES = [
    Scene(
        scene_id="scene-001", start_seconds=0, end_seconds=9.5,
        start_timestamp="00:00", end_timestamp="00:09",
        summary="Emergency vehicles and responders arrive at the simulated incident area and begin staging.",
        transcript_excerpt="Responders move into the exercise area as the simulated incident begins.",
        people_or_roles=["first responders", "exercise controllers"],
        activities=["arrival", "staging", "initial coordination"],
        equipment=["emergency vehicles", "protective equipment"],
        location_or_environment=["outdoor training area"],
        training_topics=["incident response", "scene staging"],
        observed_positive_behavior="Teams establish an organized arrival pattern before moving deeper into the scene.",
        search_tags=["arrival", "staging", "coordination", "emergency response"], confidence=.82,
    ),
    Scene(
        scene_id="scene-002", start_seconds=9.5, end_seconds=20,
        start_timestamp="00:09", end_timestamp="00:20",
        summary="Responders establish a working area and coordinate the first assessment of simulated casualties.",
        transcript_excerpt="The response team begins a structured initial assessment in the designated work area.",
        people_or_roles=["medical responders", "safety personnel"],
        activities=["assessment", "team communication"], equipment=["medical kits"],
        location_or_environment=["simulated disaster site"],
        training_topics=["initial assessment", "role coordination"],
        observed_issue="Some handoff details are not visually or audibly clear and require human review.",
        search_tags=["assessment", "communication", "handoff", "roles"], confidence=.76,
    ),
    Scene(
        scene_id="scene-003", start_seconds=20, end_seconds=32.5,
        start_timestamp="00:20", end_timestamp="00:32",
        summary="Medical personnel perform triage and prepare simulated casualties for movement.",
        transcript_excerpt="Medical teams continue triage while coordinating movement priorities.",
        people_or_roles=["medical team", "simulated casualties"],
        activities=["triage", "casualty assessment", "preparation for transport"],
        equipment=["stretcher", "medical equipment"],
        location_or_environment=["triage area"], training_topics=["triage", "medical response"],
        observed_positive_behavior="Responders work in parallel while maintaining attention on the casualty movement path.",
        search_tags=["triage", "medical", "stretcher", "team coordination"], confidence=.87,
    ),
    Scene(
        scene_id="scene-004", start_seconds=32.5, end_seconds=45,
        start_timestamp="00:32", end_timestamp="00:45",
        summary="A casualty movement sequence is coordinated between field responders and the transport team.",
        transcript_excerpt="The team transitions from treatment to transport and confirms the movement route.",
        people_or_roles=["transport team", "medical responders"],
        activities=["casualty movement", "transport handoff", "route clearance"],
        equipment=["stretcher", "ambulance"], location_or_environment=["vehicle access lane"],
        training_topics=["evacuation", "handoff communication"],
        observed_issue="The transition point is congested briefly before the route clears.",
        observed_positive_behavior="The team pauses, repositions, and resumes movement without abandoning the handoff.",
        search_tags=["evacuation", "handoff", "equipment problem", "recovery", "transport"], confidence=.8,
    ),
    Scene(
        scene_id="scene-005", start_seconds=45, end_seconds=57,
        start_timestamp="00:45", end_timestamp="00:57",
        summary="Responders complete the transport phase and maintain cross-team coordination around the vehicle area.",
        transcript_excerpt="Field and transport personnel close the movement sequence and continue coordinating at the vehicle.",
        people_or_roles=["field responders", "transport personnel"],
        activities=["transport completion", "cross-team coordination"], equipment=["ambulance"],
        location_or_environment=["transport area"], training_topics=["team coordination", "exercise closeout"],
        observed_positive_behavior="Roles remain coordinated through the final transfer instead of ending at initial contact.",
        search_tags=["effective team coordination", "transport", "communication", "closeout"], confidence=.84,
    ),
]


def demo_brief(cover_url: str = "", narration_url: str = "") -> Brief:
    return Brief(
        brief_id="11111111-1111-4111-8111-111111111111",
        project_id="demo-coordinated-response",
        title="Coordinated Triage-to-Transport Handoff",
        situation_summary="A public emergency-response exercise moved from arrival and triage into casualty transport.",
        what_occurred=[
            "Responders staged, assessed simulated casualties, and established a triage work area.",
            "Medical and transport teams coordinated a stretcher movement and vehicle handoff.",
        ],
        positive_behaviors=[
            "Teams maintained parallel work during triage.",
            "Responders recovered from brief congestion at the transition point.",
        ],
        improvement_opportunity="Review route-clearance and handoff wording before the movement begins.",
        discussion_questions=[
            "Which handoff details should be confirmed before a stretcher leaves the triage area?",
            "How could the transition point be kept clear during simultaneous operations?",
        ],
        source_timestamps=[
            {"scene_id": "scene-003", "label": "Triage preparation", "start_seconds": 20, "timestamp": "00:20–00:32"},
            {"scene_id": "scene-004", "label": "Transport handoff", "start_seconds": 32.5, "timestamp": "00:32–00:45"},
        ],
        review_notice="Generated from selected footage observations and must be reviewed by a qualified human.",
        cover_url=cover_url or None,
        narration_url=narration_url or None,
        provider="Seeded text-only preview; no provider call",
        models=[],
        generated_at=datetime(2026, 7, 31, 18, 0, tzinfo=timezone.utc),
        manifest_hash=None,
        verification_status="not_generated",
        provenance={
            "pipeline": "Not run for this seeded preview",
            "storage_sink": "Not used for this seeded preview",
            "note": "This seeded preview contains no generated media and does not claim a provider call or verified manifest.",
        },
        seeded_demo=True,
    )
