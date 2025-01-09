import threading

import redis

from website.stream import subscriptions
from website.web.bootstrap import vulnerabilitylookup

# ### Global subscription mechanism.
#
# Act as a persistent listener to Redis channels, independent of individual
# clients connecting to /subscribe/.
# To perform server-side processing of messages (e.g., logging, analytics,
# or relaying messages to another system).
#


def start_subscriber() -> None:
    """Background worker for handling subscriptions."""
    pubsub = vulnerabilitylookup.redis_client.pubsub()

    # Only subscribe if there are keys in subscriptions
    if subscriptions:
        try:
            pubsub.subscribe(*subscriptions.keys())
        except redis.exceptions.ConnectionError:
            return
    else:
        print("No channels to subscribe to. Waiting for subscriptions…")
        return  # Exit the function as there's nothing to do

    try:
        for message in pubsub.listen():  # type: ignore[no-untyped-call]
            if message["type"] == "message":
                topic: str = message["channel"]
                if topic in subscriptions:
                    for callback in subscriptions[topic]:
                        callback(message["data"])
    except redis.exceptions.ResponseError as e:
        print(f"Redis ResponseError: {e}")
    except Exception as e:
        print(f"Unexpected error in subscriber thread: {e}")


def start_thread() -> None:
    """Start the global subscriber in a separate thread."""
    subscription_thread: threading.Thread = threading.Thread(
        target=start_subscriber, daemon=True
    )
    subscription_thread.start()
    print("started")
