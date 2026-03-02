import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Tuple

import jsonschema  # type: ignore[import-untyped]
from flask_login import current_user  # type: ignore[import-untyped]
from flask_restx import (  # type: ignore[import-untyped]
    Namespace,
    Resource,
    abort,
    fields,
    reqparse,
)
from flask_restx.inputs import date_from_iso8601  # type: ignore[import-untyped]

from vulnerabilitylookup.default import get_config
from website.models import KEVEntry, KEVEvidence
from website.web.api.v1.common import auth_func, metada_params_model
from website.web.api.v1.types import ResultType
from website.web.bootstrap import db

from .decorator_helpers import typed

logger = logging.getLogger(__name__)

# Load BCP-07 JSON schema
SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "static",
    "schemas",
    "GCVE",
    "gcve-bcp-07.json",
)
with open(SCHEMA_PATH) as f:
    BCP07_SCHEMA = json.load(f)

kev_ns = Namespace("kev", description="KEV catalog operations (GCVE-BCP-07).")

local_instance_uuid = get_config("generic", "local_instance_uuid").lower()


# Request parsers
list_parser = reqparse.RequestParser()
list_parser.add_argument("page", type=int, default=1, help="Page number")
list_parser.add_argument(
    "per_page", type=int, default=100, help="Items per page (max 1000)"
)
list_parser.add_argument("vuln_id", type=str, help="Filter by vulnerability ID")
list_parser.add_argument(
    "status_reason",
    type=str,
    choices=["confirmed", "suspected", "disputed", "historical", "unknown"],
)
list_parser.add_argument("exploited", type=bool, help="Filter by exploited status")
list_parser.add_argument(
    "vulnerability_lookup_origin", type=str, help="Filter by origin instance UUID"
)
list_parser.add_argument(
    "date_from", type=date_from_iso8601, help="Filter from date (YYYY-MM-DD)"
)
list_parser.add_argument(
    "date_to", type=date_from_iso8601, help="Filter to date (YYYY-MM-DD)"
)
list_parser.add_argument("author", type=str, help="Filter by author login")


# Response models
gcve_root_model = kev_ns.model(
    "GCVERoot",
    {
        "origin_uuid": fields.String(
            description="UUID of the origin instance where the KEV assertion originated"
        ),
        "gna": fields.Integer(
            description="GNA ID identifying the origin of the KEV assertion (0-65535)",
            min=0,
            max=65535,
        ),
        "object_uuid": fields.String(
            description="UUID of the KEV assertion in the GCVE ecosystem"
        ),
    },
)

gcve_evidence_model = kev_ns.model(
    "GCVEEvidence",
    {
        "origin_uuid": fields.String(
            description="UUID of the origin instance where the assertion originated"
        ),
        "gna": fields.Integer(
            description="GNA ID identifying the origin of the assertion (0-65535)",
            min=0,
            max=65535,
        ),
        "object_uuid": fields.String(
            description="UUID of the assertion associated with this evidence in the GCVE ecosystem"
        ),
    },
)

evidence_model = kev_ns.model(
    "Evidence",
    {
        "type": fields.String(
            description="Evidence type (optional)",
            enum=[
                "incident_response",
                "telemetry",
                "honeypot",
                "sinkhole",
                "vendor_report",
                "csirt_report",
                "public_report",
                "research_report",
                "unknown",
            ],
        ),
        "source": fields.String(
            description="Evidence source (required)", required=True
        ),
        "signal": fields.Raw(
            description="Evidence signal (string or array of strings)"
        ),
        "confidence": fields.Raw(description="Confidence (number 0.0-1.0 or string)"),
        "details": fields.Raw(description="Implementation-specific details"),
    },
)

vulnerability_model = kev_ns.model(
    "Vulnerability",
    {
        "vulnId": fields.String(description="Vulnerability ID", required=True),
        "altId": fields.List(
            fields.String,
            description="Alternative vulnerability identifiers",
            skip_none=True,
            allow_null=False,
        ),
    },
)

status_model = kev_ns.model(
    "Status",
    {
        "exploited": fields.Boolean(description="Exploitation observed", required=True),
        "status_reason": fields.String(
            description="Status reason",
            required=True,
            enum=["confirmed", "suspected", "disputed", "historical", "unknown"],
        ),
        "status_updated_at": fields.DateTime(
            description="Status update time", required=True
        ),
    },
)

kev_entry_model = kev_ns.model(
    "KEVEntry",
    {
        "uuid": fields.String(description="KEV entry UUID", readonly=True),
        "vulnerability": fields.Nested(vulnerability_model),
        "gcve": fields.Nested(
            gcve_root_model,
            description="GCVE origin metadata for the KEV assertion",
            skip_none=True,
        ),
        "status": fields.Nested(status_model),
        "characteristics": fields.Raw(
            description="Technical characteristics", skip_none=True
        ),
        "timestamps": fields.Raw(description="Temporal context", skip_none=True),
        "scope": fields.Raw(
            description="Geographical/sectoral context", skip_none=True
        ),
        "evidence": fields.List(
            fields.Nested(evidence_model), description="Supporting evidence"
        ),
        "references": fields.Raw(description="Related references", skip_none=True),
    },
)

kev_list_model = kev_ns.model(
    "KEVList",
    {
        "metadata": fields.Nested(kev_ns.model("ListMetadata", metada_params_model)),
        "data": fields.List(fields.Nested(kev_entry_model)),
    },
)


def validate_bcp07_payload(data: dict[str, Any]) -> Tuple[bool, str]:
    """Validate BCP-07 schema compliance using JSON Schema"""
    try:
        # Remove uuid field if present (it's added by us, not in BCP-07)
        validation_data = {k: v for k, v in data.items() if k != "uuid"}
        jsonschema.validate(instance=validation_data, schema=BCP07_SCHEMA)
        return True, ""
    except jsonschema.ValidationError as e:
        error_path = ".".join(str(p) for p in e.path) if e.path else "root"
        return False, f"Schema validation error at {error_path}: {e.message}"
    except jsonschema.SchemaError as e:
        logger.error(f"Invalid BCP-07 schema: {e}")
        return False, "Internal schema error"


@kev_ns.route("")
@kev_ns.route("/")
class KEVList(Resource):  # type: ignore[misc]
    @typed(kev_ns.marshal_with(kev_list_model))
    @typed(kev_ns.expect(list_parser))
    def get(self) -> Tuple[ResultType, int]:
        """List KEV entries with pagination and filtering"""
        args = list_parser.parse_args()
        page = args.pop("page", 1)
        per_page = min(args.pop("per_page", 100), 1000)

        query = KEVEntry.query

        # Apply filters
        if args.get("vuln_id"):
            query = query.filter(KEVEntry.vuln_id.ilike(f"%{args['vuln_id']}%"))
        if args.get("status_reason"):
            query = query.filter(KEVEntry.status_reason == args["status_reason"])
        if args.get("exploited") is not None:
            query = query.filter(KEVEntry.exploited == args["exploited"])
        if args.get("vulnerability_lookup_origin"):
            try:
                origin_uuid = uuid.UUID(args["vulnerability_lookup_origin"])
                query = query.filter(
                    KEVEntry.vulnerability_lookup_origin == origin_uuid
                )
            except ValueError:
                abort(400, "Invalid UUID format for vulnerability_lookup_origin")
        if args.get("date_from"):
            query = query.filter(KEVEntry.creation_timestamp >= args["date_from"])
        if args.get("date_to"):
            query = query.filter(KEVEntry.creation_timestamp <= args["date_to"])
        if args.get("author"):
            from website.models import User

            user = User.query.filter(User.login == args["author"]).first()
            if user:
                query = query.filter(KEVEntry.author_id == user.id)
            else:
                # No entries if user doesn't exist
                query = query.filter(KEVEntry.author_id == -1)

        # Order and paginate
        query = query.order_by(KEVEntry.creation_timestamp.desc())
        total_count = query.count()
        entries = query.offset((page - 1) * per_page).limit(per_page).all()

        result: ResultType = {
            "metadata": {"count": total_count, "page": page, "per_page": per_page},
            "data": [entry.to_dict() for entry in entries],
        }
        return result, 200

    @typed(auth_func)
    @typed(kev_ns.expect(kev_entry_model))
    @typed(kev_ns.marshal_with(kev_entry_model, code=201))
    def post(self) -> Tuple[dict[str, Any], int]:
        """Create new KEV entry (requires reporter or admin role)"""
        if not (current_user.is_reporter or current_user.is_admin):
            abort(403, "Reporter or admin role required")

        payload = kev_ns.payload

        # Determine origin_uuid from gcve.origin_uuid (priority) or vulnerability_lookup_origin (fallback)
        # Priority: gcve.origin_uuid > vulnerability_lookup_origin > local_instance_uuid
        gcve_metadata = payload.get("gcve", {})
        origin_uuid_str = gcve_metadata.get("origin_uuid")

        if not origin_uuid_str:
            # Fallback to vulnerability_lookup_origin field (for backward compatibility)
            origin_uuid_str = payload.pop("vulnerability_lookup_origin", None)

        if not origin_uuid_str:
            # Final fallback to local instance UUID
            origin_uuid_str = local_instance_uuid

        try:
            origin_uuid = uuid.UUID(origin_uuid_str)
        except (ValueError, AttributeError, TypeError):
            abort(400, "Invalid UUID format for origin_uuid")

        # Validate BCP-07 schema (after removing vulnerability_lookup_origin if present)
        payload.pop("vulnerability_lookup_origin", None)
        valid, error = validate_bcp07_payload(payload)
        if not valid:
            print("validation error:", error)
            abort(400, error)

        # Extract data
        vulnerability = payload["vulnerability"]
        vuln_id = vulnerability["vulnId"]
        alt_id = vulnerability.get("altId", [])
        status = payload["status"]

        # Check for duplicate in the same catalog
        existing = KEVEntry.query.filter(
            KEVEntry.vuln_id == vuln_id.upper(),
            KEVEntry.vulnerability_lookup_origin == origin_uuid,
        ).first()
        if existing:
            abort(
                409,
                f"KEV entry for {vuln_id.upper()} already exists in catalog {origin_uuid}",
            )

        # Parse status_updated_at
        status_updated_at_str = status.get("status_updated_at")
        if status_updated_at_str:
            if isinstance(status_updated_at_str, str):
                status_updated_at = datetime.fromisoformat(
                    status_updated_at_str.replace("Z", "+00:00")
                )
            else:
                status_updated_at = status_updated_at_str
        else:
            status_updated_at = datetime.now(timezone.utc)

        # Generate UUID for the KEV entry (used for both entry.uuid and gcve.object_uuid)
        kev_entry_uuid = uuid.uuid4()

        # Ensure GCVE metadata is properly set with origin_uuid and object_uuid
        gcve_metadata["origin_uuid"] = str(origin_uuid)
        # object_uuid should be the same as the KEV entry's UUID
        gcve_metadata["object_uuid"] = str(kev_entry_uuid)
        # Try to set GNA if available and not already set
        if not gcve_metadata.get("gna"):
            try:
                local_gna_id = get_config("generic", "local_instance_name")
                if local_gna_id:
                    gna_id = int(local_gna_id.replace("gna-", ""))
                    gcve_metadata["gna"] = gna_id
            except (ValueError, AttributeError):
                # GNA not configured or invalid, skip it
                pass

        # Create KEV entry
        kev_entry = KEVEntry(
            uuid=kev_entry_uuid,
            vuln_id=vuln_id,
            alt_id=alt_id,
            exploited=status.get("exploited", True),
            status_reason=status.get("status_reason", "unknown"),
            status_updated_at=status_updated_at,
            gcve_metadata=gcve_metadata,
            characteristics=payload.get("characteristics", {}),
            timestamps=payload.get("timestamps", {}),
            scope=payload.get("scope", {}),
            references=payload.get("references", []),
            vulnerability_lookup_origin=origin_uuid,
            author_id=current_user.id,
        )

        # Create evidence
        for ev_data in payload.get("evidence", []):
            evidence = KEVEvidence(
                evidence_type=ev_data.get("type"),  # Optional per schema
                source=ev_data["source"],  # Required per schema
                signal=ev_data.get("signal"),
                confidence=ev_data.get("confidence"),
                details=ev_data.get("details", {}),
                gcve_metadata=ev_data.get("gcve", {}),
                kev_entry_uuid=kev_entry.uuid,
            )
            db.session.add(evidence)

        db.session.add(kev_entry)
        db.session.commit()

        return kev_entry.to_dict(), 201


@kev_ns.route("/<string:kev_uuid>")
class KEVDetail(Resource):  # type: ignore[misc]
    @typed(kev_ns.marshal_with(kev_entry_model))
    def get(self, kev_uuid: str) -> Tuple[dict[str, Any], int]:
        """Get single KEV entry"""
        try:
            kev_entry = KEVEntry.query.filter(
                KEVEntry.uuid == uuid.UUID(kev_uuid)
            ).first()
        except ValueError:
            abort(400, "Invalid UUID format")

        if not kev_entry:
            abort(404, "KEV entry not found")

        return kev_entry.to_dict(), 200

    @typed(auth_func)
    @typed(kev_ns.expect(kev_entry_model))
    @typed(kev_ns.marshal_with(kev_entry_model))
    def put(self, kev_uuid: str) -> Tuple[dict[str, Any], int]:
        """Update KEV entry (author or admin only)"""
        try:
            kev_entry = KEVEntry.query.filter(
                KEVEntry.uuid == uuid.UUID(kev_uuid)
            ).first()
        except ValueError:
            abort(400, "Invalid UUID format")

        if not kev_entry:
            abort(404, "KEV entry not found")

        # Check permissions
        if kev_entry.author_id != current_user.id and not current_user.is_admin:
            abort(403, "Only the author or admin can update this KEV entry")

        payload = kev_ns.payload

        # Validate BCP-07 schema
        valid, error = validate_bcp07_payload(payload)
        if not valid:
            abort(400, error)

        # Update fields
        if "vulnerability" in payload:
            vulnerability = payload["vulnerability"]
            new_vuln_id = vulnerability["vulnId"].upper()

            # Check if changing vuln_id would create a duplicate in the same catalog
            if new_vuln_id != kev_entry.vuln_id:
                existing = KEVEntry.query.filter(
                    KEVEntry.vuln_id == new_vuln_id,
                    KEVEntry.vulnerability_lookup_origin
                    == kev_entry.vulnerability_lookup_origin,
                    KEVEntry.uuid != kev_entry.uuid,
                ).first()
                if existing:
                    abort(
                        409,
                        f"KEV entry for {new_vuln_id} already exists in this catalog",
                    )

            kev_entry.vuln_id = new_vuln_id
            if "altId" in vulnerability:
                kev_entry.alt_id = vulnerability["altId"]

        if "status" in payload:
            status = payload["status"]
            kev_entry.exploited = status.get("exploited", kev_entry.exploited)
            kev_entry.status_reason = status.get(
                "status_reason", kev_entry.status_reason
            )
            if "status_updated_at" in status:
                status_updated_at_str = status["status_updated_at"]
                if isinstance(status_updated_at_str, str):
                    kev_entry.status_updated_at = datetime.fromisoformat(
                        status_updated_at_str.replace("Z", "+00:00")
                    )
                else:
                    kev_entry.status_updated_at = status_updated_at_str

        # Update optional fields
        if "gcve" in payload:
            gcve_metadata = payload["gcve"]
            # Origin should not change after creation - always use existing vulnerability_lookup_origin
            gcve_metadata["origin_uuid"] = str(kev_entry.vulnerability_lookup_origin)

            # object_uuid must always match the KEV entry's UUID
            gcve_metadata["object_uuid"] = str(kev_entry.uuid)

            # Try to set GNA if available and not already set
            if not gcve_metadata.get("gna"):
                try:
                    local_gna_id = get_config("generic", "local_instance_name")
                    if local_gna_id:
                        gna_id = int(local_gna_id.replace("gna-", ""))
                        gcve_metadata["gna"] = gna_id
                except (ValueError, AttributeError):
                    # GNA not configured or invalid, skip it
                    pass
            kev_entry.gcve_metadata = gcve_metadata
        if "characteristics" in payload:
            kev_entry.characteristics = payload["characteristics"]
        if "timestamps" in payload:
            kev_entry.timestamps = payload["timestamps"]
        if "scope" in payload:
            kev_entry.scope = payload["scope"]
        if "references" in payload:
            kev_entry.references = payload["references"]

        # Update evidence (replace all)
        if "evidence" in payload:
            KEVEvidence.query.filter(
                KEVEvidence.kev_entry_uuid == kev_entry.uuid
            ).delete()
            for ev_data in payload["evidence"]:
                evidence = KEVEvidence(
                    evidence_type=ev_data.get("type"),  # Optional per schema
                    source=ev_data["source"],  # Required per schema
                    signal=ev_data.get("signal"),
                    confidence=ev_data.get("confidence"),
                    details=ev_data.get("details", {}),
                    gcve_metadata=ev_data.get("gcve", {}),
                    kev_entry_uuid=kev_entry.uuid,
                )
                db.session.add(evidence)

        kev_entry.updated_timestamp = datetime.now(timezone.utc)
        db.session.commit()

        return kev_entry.to_dict(), 200

    @typed(auth_func)
    def delete(self, kev_uuid: str) -> Tuple[dict[str, str], int]:
        """Delete KEV entry (admin only)"""
        if not current_user.is_admin:
            abort(403, "Admin role required to delete KEV entries")

        try:
            kev_entry = KEVEntry.query.filter(
                KEVEntry.uuid == uuid.UUID(kev_uuid)
            ).first()
        except ValueError:
            abort(400, "Invalid UUID format")

        if not kev_entry:
            abort(404, "KEV entry not found")

        db.session.delete(kev_entry)
        db.session.commit()

        return {"message": "KEV entry deleted successfully"}, 200


@kev_ns.route("/catalog/<string:catalog_uuid>")
class KEVCatalogBatch(Resource):  # type: ignore[misc]
    @typed(auth_func)
    def delete(self, catalog_uuid: str) -> Tuple[dict[str, Any], int]:
        """Delete all KEV entries from a specific catalog (admin only)"""
        if not current_user.is_admin:
            abort(403, "Admin role required to delete KEV catalogs")

        # Validate UUID format
        try:
            origin_uuid = uuid.UUID(catalog_uuid)
        except ValueError:
            abort(400, "Invalid UUID format for catalog_uuid")

        # Count entries before deletion
        entries_query = KEVEntry.query.filter(
            KEVEntry.vulnerability_lookup_origin == origin_uuid
        )
        count_before = entries_query.count()

        if count_before == 0:
            return {
                "message": f"No KEV entries found for catalog {catalog_uuid}",
                "deleted_count": 0,
                "catalog_uuid": catalog_uuid,
            }, 200

        # Delete all entries from this catalog
        # Evidence will be cascade deleted due to the relationship configuration
        entries_query.delete(synchronize_session=False)
        db.session.commit()

        return {
            "message": f"Successfully deleted all KEV entries from catalog {catalog_uuid}",
            "deleted_count": count_before,
            "catalog_uuid": catalog_uuid,
        }, 200
