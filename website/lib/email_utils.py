import json
import dns.resolver

from vulnerabilitylookup.default import get_homedir
from website.web.bootstrap import application


def is_email_in_misp_disposable_list(domain: str) -> bool:
    """Verify if a domain name is present is the MISP warning list
    of disposable email."""
    homedir = get_homedir()
    disposable_emails_list = homedir.joinpath(
        "data/misp/misp-warninglists/lists/disposable-email/list.json"
    )
    if disposable_emails_list.exists():
        with open(disposable_emails_list) as file:
            data = json.load(file)
            disposable_domains = data.get("list", [])
            return domain.lower() in (
                blocked_domain.lower() for blocked_domain in disposable_domains
            )
    else:
        return False


def is_email_in_block_list(domain: str) -> bool:
    """
    Check whether an email domain is blocked from registration.

    The domain is validated, normalized (lowercased and stripped),
    and compared against the configured block list
    (``BLOCKED_DOMAINS_FOR_REGISTRATION``).

    Both exact domain matches and wildcard entries (e.g. ``*.example.com``)
    are supported.

    :param domain: Email domain to validate (e.g. ``example.com``).
    :raises ValueError: If the domain is not a non-empty string.
    :raises TypeError: If the block list configuration is not a set.
    :return: ``True`` if the domain is blocked, ``False`` otherwise.
    """
    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("Invalid domain input")
    domain = domain.lower().strip()
    blocked_domains = application.config.get("BLOCKED_DOMAINS_FOR_REGISTRATION", set())

    if not isinstance(blocked_domains, set):
        raise TypeError("BLOCKED_DOMAINS_FOR_REGISTRATION must be a set")

    # Check exact match
    if domain in blocked_domains:
        return True

    # Check wildcard matches (e.g., *.example.com)
    for blocked in blocked_domains:
        if blocked.startswith("*.") and domain.endswith(blocked[2:]):
            return True

    return False


def is_email_in_allow_list(domain: str) -> bool:
    """
    Return True if the email domain is allowed to register.

    If the allow list (ACCEPTED_DOMAINS_FOR_REGISTRATION) is empty,
    all domains are considered allowed.

    Exact matches and wildcard entries (e.g. ``*.example.com``)
    are supported.
    """
    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("Invalid domain input")

    domain = domain.lower().strip()
    allowed_domains = application.config.get("ACCEPTED_DOMAINS_FOR_REGISTRATION", set())

    if not isinstance(allowed_domains, set):
        raise TypeError("ACCEPTED_DOMAINS_FOR_REGISTRATION must be a set")

    # Empty allow list → allow everything
    if not allowed_domains:
        return True

    # Exact match
    if domain in allowed_domains:
        return True

    # Wildcard match (e.g. *.example.com)
    for allowed in allowed_domains:
        if allowed.startswith("*.") and domain.endswith(allowed[2:]):
            return True

    return False


def has_mx_record(domain: str) -> bool:
    """Return True if the domain has MX or A/AAAA records (RFC 5321 §5.1)."""
    try:
        answers = dns.resolver.resolve(domain, "MX")
        return len(answers) > 0
    except dns.resolver.NoAnswer:
        # No MX record, try A/AAAA fallback
        try:
            dns.resolver.resolve(domain, "A")
            return True
        except dns.resolver.NoAnswer:
            try:
                dns.resolver.resolve(domain, "AAAA")
                return True
            except dns.resolver.NoAnswer:
                return False
    except dns.resolver.NXDOMAIN:
        return False
    except Exception:
        # Catch timeouts or configuration issues conservatively as False
        return False
