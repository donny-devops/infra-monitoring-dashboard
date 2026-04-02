from flask import Blueprint, jsonify, request, abort
from app.extensions import db
from app.models.host import Host
from app.services.metric_service import get_latest_cached

hosts_bp = Blueprint("hosts", __name__, url_prefix="/api/v1/hosts")


def _host_dict(host: Host, with_latest: bool = False) -> dict:
    d = {
        "id": host.id,
        "name": host.name,
        "hostname": host.hostname,
        "environment": host.environment,
        "tags": host.tags,
        "is_active": host.is_active,
        "created_at": host.created_at.isoformat() if host.created_at else None,
        "ingest_token": host.ingest_token,
    }
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
    if not data.get("name") or not data.get("hostname"):
        abort(400, description="name and hostname are required")
    if Host.query.filter_by(hostname=data["hostname"]).first():
        abort(409, description="hostname already registered")
    host = Host(
        name=data["name"],
        hostname=data["hostname"],
        environment=data.get("environment", "production"),
        tags=data.get("tags", {}),
    )
    db.session.add(host)
    db.session.commit()
    return jsonify(_host_dict(host)), 201


@hosts_bp.get("/<int:host_id>")
def get_host(host_id):
    host = db.get_or_404(Host, host_id)
    return jsonify(_host_dict(host, with_latest=True))


@hosts_bp.patch("/<int:host_id>")
def update_host(host_id):
    host = db.get_or_404(Host, host_id)
    data = request.get_json(silent=True) or {}
    for field in ("name", "environment", "tags", "is_active"):
        if field in data:
            setattr(host, field, data[field])
    db.session.commit()
    return jsonify(_host_dict(host))


@hosts_bp.delete("/<int:host_id>")
def decommission_host(host_id):
    host = db.get_or_404(Host, host_id)
    host.is_active = False
    db.session.commit()
    return "", 204
