"""Validate Composio execution envelopes without interpreting source content as status."""
class ProviderFailure(RuntimeError):
    pass


def check_result(value):
    """Require affirmative status, and reject errors in every nested execution result."""
    confirmations = []

    def visit(item):
        if isinstance(item, list):
            if not item:
                raise ProviderFailure('Provider returned an empty result')
            for child in item:
                before = len(confirmations)
                visit(child)
                if len(confirmations) == before:
                    raise ProviderFailure('Provider returned an unconfirmed execution result')
        elif isinstance(item, dict):
            for key in ('success', 'successful'):
                if key in item:
                    if item[key] is not True:
                        raise ProviderFailure('Provider reported an unsuccessful operation')
                    confirmations.append(True)
            if item.get('error'):
                raise ProviderFailure('Provider reported an operation error')
            # Only transport/envelope fields: email/event text is untrusted content.
            for key in ('data', 'result', 'results', 'response', 'response_data'):
                if key in item:
                    visit(item[key])

    visit(value)
    if not confirmations:
        raise ProviderFailure('Provider returned no affirmative success status')
    return value


def resource_id(value):
    if isinstance(value, dict):
        for key in ('id', 'messageId', 'message_id', 'event_id', 'draft_id'):
            identifier = value.get(key)
            if isinstance(identifier, str) and identifier:
                return identifier
        for key in ('data', 'result', 'results', 'response', 'response_data', 'message'):
            if key in value:
                found = resource_id(value[key])
                if found:
                    return found
    elif isinstance(value, list):
        for item in value:
            found = resource_id(item)
            if found:
                return found
    return None
