from __future__ import annotations

STATUS_PENDING = "pending"
STATUS_INGESTION_IN_PROGRESS = "ingestion_in_progress"
STATUS_INGESTION_COMPLETE = "ingestion_complete"
STATUS_TIMELINE_IN_PROGRESS = "timeline_in_progress"
STATUS_TIMELINE_COMPLETE = "timeline_complete"
STATUS_PLOT_HOLE_IN_PROGRESS = "plot_hole_in_progress"
STATUS_PLOT_HOLE_COMPLETE = "plot_hole_complete"
STATUS_FAILED = "failed"

TERMINAL_JOB_STATUSES = {
    STATUS_PLOT_HOLE_COMPLETE,
    STATUS_FAILED,
}

