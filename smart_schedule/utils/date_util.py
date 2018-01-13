from datetime import datetime
import pytz

jst = pytz.timezone('Asia/Tokyo')


def is_over_now(dt):
    """
    Checking the month and day, judge over from now or not.
    :param dt: datetime.datetime
    :return: boolean
    """
    now = datetime.now(jst)
    if dt.month - now.month >= 0:
        if dt.day - now.day >= 0:
            return True
    return False
