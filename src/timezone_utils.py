from datetime import datetime, timezone, timedelta

def get_helsinki_now() -> datetime:
    """获取赫尔辛基时区当前时间。在缺少系统 tzdata 数据库时（如未配 tzdata 的原生 Windows 环境），
    平滑回退至基于芬兰冬令时(UTC+2)/夏令时(UTC+3)规则的精确时间计算，确保在任何操作系统下永不报错。"""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Helsinki"))
    except Exception:
        now_utc = datetime.now(timezone.utc)
        year = now_utc.year
        # 芬兰夏令时规则：3月最后一个周日 01:00 UTC 开始，10月最后一个周日 01:00 UTC 结束
        march_last = max(d for d in range(25, 32) if datetime(year, 3, d).weekday() == 6)
        dst_start = datetime(year, 3, march_last, 1, 0, tzinfo=timezone.utc)
        oct_last = max(d for d in range(25, 32) if datetime(year, 10, d).weekday() == 6)
        dst_end = datetime(year, 10, oct_last, 1, 0, tzinfo=timezone.utc)
        offset = timedelta(hours=3) if dst_start <= now_utc < dst_end else timedelta(hours=2)
        return now_utc.astimezone(timezone(offset))
