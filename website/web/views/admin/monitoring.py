#!/usr/bin/env python3

import json
import re
import time
from typing import Generator

from flask import (
    Blueprint,
    Response,
    jsonify,
    render_template,
    stream_with_context,
)
from flask_login import (  # type: ignore[import-untyped]
    login_required,
)

from website.web.bootstrap import vulnerabilitylookup
from website.web.permissions import admin_permission

admin_monitoring_bp = Blueprint(
    "admin_monitoring_bp", __name__, url_prefix="/admin/monitoring"
)


@admin_monitoring_bp.route("/processes/get_heartbeats", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def sse_processes_heartbeats() -> Response | tuple[Response, int]:
    """
    Returns an text/event-stream with heartbeats information from the various processes.
    """
    if not vulnerabilitylookup.redis_client:
        return jsonify({"error": "Redis connection is not available."}), 500

    def stream() -> Generator[str, None, None]:
        # Regex pattern to match heartbeat keys of any scripts
        heartbeat_pattern = re.compile(r"^process_heartbeat_.*$")

        while True:
            # Fetch all keys matching the heartbeat pattern
            _, keys = vulnerabilitylookup.redis_client.scan(match="process_heartbeat_*")
            heartbeats = {}
            for key in keys:
                if heartbeat_pattern.match(key):
                    heartbeats[key] = float(
                        vulnerabilitylookup.redis_client.get(key) or 0
                    )

            json_message = json.dumps(heartbeats)  # Ensure single-line JSON

            yield f"data: {json_message}\n\n"
            time.sleep(5)

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return Response(
        stream_with_context(stream()), content_type="text/event-stream", headers=headers
    )


@admin_monitoring_bp.route("/get_logs/<string:component>", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def sse_processes_logs(component: str = "feeders") -> Response | tuple[Response, int]:
    """
    Returns a text/event-stream with logs from the various processes.
    """
    if not vulnerabilitylookup.redis_client:
        return jsonify({"error": "Redis connection is not available."}), 500

    def stream() -> Generator[str, None, None]:
        # Regex pattern to match error log keys of any scripts
        safe_component = re.escape(component)
        match_pattern = f"{safe_component}_logs_*"
        regex_pattern = f"^{safe_component}_logs.*$"
        error_log_pattern = re.compile(regex_pattern)

        while True:
            # Fetch all keys matching the error log pattern
            _, keys = vulnerabilitylookup.redis_client.scan(match=match_pattern)
            error_logs = {}

            for key in keys:
                if error_log_pattern.match(key):
                    # logs = vulnerabilitylookup.redis_client.lrange(key, 0, -1)
                    error_logs[key] = vulnerabilitylookup.redis_client.lrange(
                        key, -50, -1
                    )

            json_message = json.dumps(error_logs)  # Ensure single-line JSON

            yield f"data: {json_message}\n\n"
            time.sleep(5)

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return Response(
        stream_with_context(stream()), content_type="text/event-stream", headers=headers
    )


@admin_monitoring_bp.route("/processes", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def processes() -> str:
    """Returns an HTML page that establishes a connection to various event streams to display logs."""
    return render_template("admin/processes.html")


@admin_monitoring_bp.route("/feeders", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def feeders() -> str:
    """Returns an HTML page that establishes a connection to various event streams to display logs."""
    return render_template("admin/feeders.html")
