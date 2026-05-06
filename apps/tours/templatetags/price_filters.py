from django import template

register = template.Library()


@register.filter
def currency_vnd(value, currency='VNĐ'):
    """
    Format number as Vietnamese currency with dot as thousands separator.
    Examples:
        3500000 -> '3.500.000 VNĐ'
        3500000.5 -> '3.500.000,50 VNĐ'
    """
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return value

    neg = amount < 0
    amount_abs = abs(amount)

    # Integer amounts: no decimals
    if amount_abs.is_integer():
        integer = int(amount_abs)
        formatted_int = f"{integer:,}".replace(',', '.')
        formatted = f"-{formatted_int}" if neg else formatted_int
    else:
        # Use two decimal places; integer thousands use dot, decimal separated by comma
        formatted_full = f"{amount_abs:,.2f}"  # e.g. '3,500,000.50'
        int_part, dec_part = formatted_full.split('.')
        int_part = int_part.replace(',', '.')
        formatted = f"{int_part},{dec_part}"
        if neg:
            formatted = "-" + formatted

    return f"{formatted} {currency}"
