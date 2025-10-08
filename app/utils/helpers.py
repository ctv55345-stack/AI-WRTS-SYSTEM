from datetime import datetime, timezone, timedelta

def get_vietnam_time():
    """
    Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7)
    """
    vietnam_tz = timezone(timedelta(hours=7))
    return datetime.now(vietnam_tz)

def get_vietnam_time_naive():
    """
    Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7) nhưng trả về naive datetime
    Để tương thích với database datetime (naive)
    """
    vietnam_tz = timezone(timedelta(hours=7))
    return datetime.now(vietnam_tz).replace(tzinfo=None)

def utc_to_vietnam(utc_datetime):
    """
    Chuyển đổi UTC datetime sang múi giờ Việt Nam (UTC+7)
    """
    if utc_datetime is None:
        return None
    
    vietnam_tz = timezone(timedelta(hours=7))
    if utc_datetime.tzinfo is None:
        # Nếu datetime không có timezone info, giả sử là UTC
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    return utc_datetime.astimezone(vietnam_tz)

def vietnam_to_utc(vietnam_datetime):
    """
    Chuyển đổi múi giờ Việt Nam (UTC+7) sang UTC
    """
    if vietnam_datetime is None:
        return None
    
    vietnam_tz = timezone(timedelta(hours=7))
    if vietnam_datetime.tzinfo is None:
        # Nếu datetime không có timezone info, giả sử là Vietnam time
        vietnam_datetime = vietnam_datetime.replace(tzinfo=vietnam_tz)
    
    return vietnam_datetime.astimezone(timezone.utc)
