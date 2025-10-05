"""
CHANGELOG
=========

1) Class schedules feature (multiple sessions per class)
- Model: `app/models/class_schedule.py` (imported in `app/models/__init__.py`)
- Form: `app/forms/schedule_forms.py`
- Service: `app/services/schedule_service.py`
- Routes (Instructor): `app/routes/instructor.py`
  + GET  /instructor/classes/<class_id>/schedules
  + GET  /instructor/classes/<class_id>/schedules/add
  + POST /instructor/classes/<class_id>/schedules/add
  + GET  /instructor/schedules/<schedule_id>/edit
  + POST /instructor/schedules/<schedule_id>/edit
  + POST /instructor/schedules/<schedule_id>/delete
- Templates:
  + `templates/instructor/class_schedules.html`
  + `templates/instructor/schedule_add.html`
  + `templates/instructor/schedule_edit.html`
  + `templates/instructor/class_detail.html` (added links and schedule display)
- Migration: ensure table `class_schedules` exists; if needed:
  flask db migrate -m "Add class_schedules table" && flask db upgrade

2) Class approval workflow (pending/approved/rejected)
- Migration (SQL columns): see Alembic history; if needed rerun:
  flask db migrate -m "Add class approval workflow" && flask db upgrade
- Model update: `app/models/class_model.py` (approval fields and relationships)
- Forms: `app/forms/class_forms.py` (added `ClassApprovalForm`)
- Services: `app/services/class_service.py` (create proposal, approve, reject, queries)
- Instructor routes: `app/routes/instructor.py` (dashboard filtering, proposals, propose form)
- Manager routes: `app/routes/manager.py` (pending list, review approve/reject, all-classes)
- Templates:
  + `templates/instructor/dashboard.html` (update)
  + `templates/instructor/class_propose.html` (new)
  + `templates/instructor/my_proposals.html` (new)
  + `templates/manager/dashboard.html` (update)
  + `templates/manager/pending_classes.html` (new)
  + `templates/manager/review_class.html` (new)

Notes
- Large inline code samples previously stored here have been removed to avoid duplication and drift.
- Refer to the files above for the authoritative implementations.
"""