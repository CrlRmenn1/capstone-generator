from flask import Response, current_app, jsonify, request
from flask_login import current_user, login_required

from ..engines import OUTLINE_SECTIONS, SECTION_KEYS, EngineError, get_outline_engine
from ..engines.context import resolve_context
from ..exporter import safe_filename, to_docx, to_pdf
from ..extensions import db, limiter
from ..models import Outline, OutlineSection
from ..progress import mark
from . import api
from .common import body, error, text_field

MAX_OUTLINES = 50
MAX_SECTION_CHARS = 20000
HEADINGS = dict(OUTLINE_SECTIONS)


def _own_outline(outline_id: int) -> Outline | None:
    return current_user.outlines.filter_by(id=outline_id).first()


def _engine_error(exc: EngineError):
    return error(str(exc), 502 if exc.code != "no_key" else 400, exc.code, fallback=True)


@api.get("/outlines")
@login_required
def list_outlines():
    items = current_user.outlines.order_by(Outline.updated_at.desc()).all()
    return jsonify(outlines=[o.to_dict(with_sections=False) for o in items])


@api.post("/outlines")
@login_required
@limiter.limit("20 per minute")
def create_outline():
    data = body()
    title, err = text_field(data, "title", 300)
    if err:
        return error(err)
    system_name, err = text_field(data, "system_name", 60, required=False)
    if err:
        return error(err)
    if current_user.outlines.count() >= MAX_OUTLINES:
        return error(f"You can keep up to {MAX_OUTLINES} outlines. Delete some first.", 409, "limit")

    kb = current_app.extensions["kb"]
    context = data.get("context") if isinstance(data.get("context"), dict) else {}
    try:
        ctx = resolve_context(kb, title, context, system_name)
    except ValueError as exc:
        return error(str(exc), 400, "invalid_context")

    try:
        engine = get_outline_engine(current_app, current_user, data.get("engine"))
        written = engine.write_all(title, ctx, seed=0)
    except EngineError as exc:
        return _engine_error(exc)

    outline = Outline(user_id=current_user.id, title=title, system_name=ctx["system_name"],
                      context=ctx, mode=engine.source)
    for position, (key, heading) in enumerate(OUTLINE_SECTIONS):
        outline.sections.append(OutlineSection(key=key, heading=heading, position=position,
                                               content=written[key], source=engine.source))
    db.session.add(outline)
    db.session.commit()
    return jsonify(outline=outline.to_dict()), 201


@api.get("/outlines/<int:outline_id>")
@login_required
def get_outline(outline_id: int):
    outline = _own_outline(outline_id)
    if not outline:
        return error("Outline not found.", 404, "not_found")
    return jsonify(outline=outline.to_dict())


@api.delete("/outlines/<int:outline_id>")
@login_required
def delete_outline(outline_id: int):
    outline = _own_outline(outline_id)
    if not outline:
        return error("Outline not found.", 404, "not_found")
    db.session.delete(outline)
    db.session.commit()
    return jsonify(ok=True)


def _section(outline: Outline, key: str) -> OutlineSection | None:
    return next((s for s in outline.sections if s.key == key), None)


@api.patch("/outlines/<int:outline_id>/sections/<key>")
@login_required
def edit_section(outline_id: int, key: str):
    outline = _own_outline(outline_id)
    section = _section(outline, key) if outline else None
    if not section:
        return error("Section not found.", 404, "not_found")
    content = body().get("content")
    if not isinstance(content, str):
        return error("Content is required.")
    if len(content) > MAX_SECTION_CHARS:
        return error(f"A section can have at most {MAX_SECTION_CHARS} characters.")
    section.content = content.strip()
    section.is_edited = True
    section.source = "user"
    section.version += 1
    outline.updated_at = db.func.now()
    db.session.commit()
    return jsonify(section=section.to_dict())


@api.post("/outlines/<int:outline_id>/sections/<key>/regenerate")
@login_required
@limiter.limit("30 per minute")
def regenerate_section(outline_id: int, key: str):
    outline = _own_outline(outline_id)
    section = _section(outline, key) if outline else None
    if not section or key not in SECTION_KEYS:
        return error("Section not found.", 404, "not_found")
    current = {s.key: s.content for s in outline.sections if s.key != key}
    try:
        engine = get_outline_engine(current_app, current_user, body().get("engine"))
        content = engine.write_section(key, outline.title, outline.context,
                                       seed=section.version, current=current)
    except EngineError as exc:
        return _engine_error(exc)
    section.content = content
    section.is_edited = False
    section.source = engine.source
    section.version += 1
    outline.updated_at = db.func.now()
    db.session.commit()
    return jsonify(section=section.to_dict())


@api.get("/outlines/<int:outline_id>/export")
@login_required
@limiter.limit("20 per minute")
def export_outline(outline_id: int):
    outline = _own_outline(outline_id)
    if not outline:
        return error("Outline not found.", 404, "not_found")
    fmt = request.args.get("format", "docx")
    data = outline.to_dict()
    if fmt == "docx":
        payload = to_docx(data)
        mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif fmt == "pdf":
        payload = to_pdf(data)
        mimetype = "application/pdf"
    else:
        return error("Format must be docx or pdf.")
    mark(current_user, "exported")
    filename = safe_filename(outline.title, fmt)
    return Response(payload, mimetype=mimetype,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
