import dash


def try_invest_amount_conv(invest_amount_):
    """Handles exception when incorrect invest amount is inputted"""
    error_info = None
    try:
        invest_amount_float = float(invest_amount_)
        if (
            invest_amount_float < 0
        ):  # TODO: store these prompts in another collection in DB
            error_info = "Please enter valid investment amount."
    except ValueError:
        invest_amount_float = None
        error_info = "Please enter valid investment amount."
    return invest_amount_float, error_info
