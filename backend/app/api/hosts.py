from flask import Blueprint, jsonify, request, abort
from app.extensions import db
from app.models.host import Host
from app.services.metric_service import get_latest_cached
import re

hosts_bp = Blueprint("hosts", __name__, url_prefix="/api/v1/hosts")

ENVIRONMENTS = {"production", "staging", "development"}
HOSTNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")


def _text(value, field: str, max_len: int = 128) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > max_len:
        abort(400, description=f"{field} must be a non-empty string up to {max_len} characters")
    return value.strip()


def _host_dict(host: Host, with_latest: bool = False, include_token: bool = False) -> dict:
    d = {
        "id": host.id,
        "name": host.name,
        "hostname": host.hostname,
        "environment": host.environment,
        "tags": host.tags,
        "is_active": host.is_active,
        "created_at": host.created_at.isoformat() if host.created_at else None,
    }
    if include_token:
        d["ingest_token"] = host.ingest_token
    if with_latest:
        d["latest_metrics"] = get_latest_cached(host.id)
    return d


@hosts_bp.get("")
def list_hosts():
    hosts = Host.query.filter_by(is_active=True).order_by(Host.name).all()
    return jsonify([_host_dict(h, with_latest=True) for h in hosts])


@hosts_bp.post("")
def create_host():
    data = request.get_json(silent=True) or {}
    name = _text(data.get("name"), "name")
    hostname = _text(data.get("hostname"), "hostname", 253)
    if not HOSTNAME_RE.match(hostname):
        abort(400, description="hostname contains unsupported characters")
    environment = data.get("environment", "production")
    if environment not in ENVIRONMENTS:
        abort(400, description="environment must be production, staging, or development")
    tags = data.get("tags", {})
    if not isinstance(tags, dict):
        abort(400, description="tags must be an object")
    if Host.query.filter_by(hostname=hostname).first():
        abort(409, description="hostname already registered")
    host = Host(
        name=name,
        hostname=hostname,
        environment=environment,
        tags=tags,
    )
    db.session.add(host)
    db.session.commit()
    return jsonify(_host_dict(host, include_token=True)), 201


@hosts_bp.get("/<int:host_id>")
def get_host(host_id):
    host = db.get_or_404(Host, host_id)
    return jsonify(_host_dict(host, with_latest=True))


@hosts_bp.patch("/<int:host_id>")
def update_host(host_id):
    host = db.get_or_404(Host, host_id)
    data = request.get_json(silent=True) or {}
    if "name" in data:
        host.name = _text(data["name"], "name")
    if "environment" in data:
        if data["environment"] not in ENVIRONMENTS:
            abort(400, description="environment must be production, staging, or development")
        host.environment = data["environment"]
    if "tags" in data:
        if not isinstance(data["tags"], dict):
            abort(400, description="tags must be an object")
        host.tags = data["tags"]
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            abort(400, description="is_active must be a boolean")
        host.is_active = data["is_active"]
    db.session.commit()
    return jsonify(_host_dict(host))


@hosts_bp.delete("/<int:host_id>")
def decommission_host(host_id):
    host = db.get_or_404(Host, host_id)
    host.is_active = False
    db.session.commit()
    return "", 204
