#!/usr/bin/env python3

import json
from functools import wraps
from typing import Any, Callable, Generator, TypeVar

import redis
from flask import Blueprint, Response, g, jsonify, request, stream_with_context
from sqlalchemy.exc import SQLAlchemyError

from website.models import User
from website.stream import subscriptions
from website.web.bootstrap import csrf, vulnerabilitylookup

# Create the blueprint
pubsub_bp = Blueprint("pubsub", __name__, url_prefix="/pubsub")
csrf.exempt(pubsub_bp)


# Type variables for function typing
F = TypeVar("F", bound=Callable[..., Any])


def token_required(f: F) -> F:
    """
    Decorator to enforce authentication via X-API-KEY header.

    Args:
        f (Callable): The view function to decorate.

    Returns:
        Callable: The decorated view function.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Get the token from the header
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            return jsonify({"error": "Authentication token missing."}), 401

        try:
            # Query the database for a user with the given API key
            user = User.query.filter_by(apikey=api_key).first()
            if not user:
                return jsonify({"error": "Invalid API token"}), 403

            # Store the authenticated user in Flask's `g` object
            g.current_user = user
        except SQLAlchemyError as e:
            return jsonify({"error": "An internal error has occurred."}), 500

        return f(*args, **kwargs)

    return decorated_function  # type: ignore


# @pubsub_bp.route("/publish", methods=["POST"])
# def publish() -> Response | tuple[Response, int]:
#     """Publish a message to a topic"""
#     data: Any = request.json
#     if not data or "topic" not in data or "message" not in data:
#         return (
#             jsonify({"error": 'Invalid payload. "topic" and "message" are required.'}),
#             400,
#         )

#     topic: str = data["topic"]
#     message: str = data["message"]

#     # Ensure topic exists in default topics
#     if topic not in subscriptions:
#         return jsonify({"error": f"Topic '{topic}' is not available."}), 400

#     # Publish the message to the Redis channel
#     vulnerabilitylookup.redis_client.publish(topic, message)
#     return jsonify({"message": "Message published successfully"}), 200


@pubsub_bp.route("/subscribe/<string:topic>", methods=["GET"])
@token_required
def subscribe(topic: str) -> Response | tuple[Response, int]:
    """Subscribe to a topic and stream messages.
    Creates a new Pub/Sub subscription for the specific client making the request.
    Messages are streamed to the client via pubsub.listen().
    Subscriptions are simply protected with the X-API-KEY token.
    """
    if not vulnerabilitylookup.redis_client:
        return jsonify({"error": "Redis connection is not available."}), 500

    if topic not in subscriptions:
        available_topics = ", ".join(subscriptions.keys())
        return (
            jsonify(
                {
                    "error": f"Topic '{topic}' is not available.",
                    "available_topics": available_topics,
                }
            ),
            400,
        )

    def stream() -> Generator[str, None, None]:
        pubsub = vulnerabilitylookup.redis_client.pubsub()
        try:
            pubsub.subscribe(topic)
        except redis.exceptions.ConnectionError:
            return
        try:
            while True:
                message = pubsub.get_message(timeout=10)  # Timeout for listener
                if message and message["type"] == "message":
                    # Send entire JSON object as a single `data:` line
                    json_message = json.dumps(
                        message["data"]
                    )  # Ensure single-line JSON
                    yield f"data: {json_message}\n\n"
        except GeneratorExit:
            pubsub.unsubscribe(topic)
        except redis.exceptions.ConnectionError:
            return
        finally:
            pubsub.close()

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return Response(
        stream_with_context(stream()), content_type="text/event-stream", headers=headers
    )
