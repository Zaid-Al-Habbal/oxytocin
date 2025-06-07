from django.core.cache import cache as default_cache
from django.core.exceptions import ImproperlyConfigured

import time

from rest_framework.settings import api_settings
from rest_framework.throttling import BaseThrottle

from .models import CustomUser as User


def strip_unit_from_value(s):
    i = len(s)
    while i > 0 and s[i - 1].isalpha():
        i -= 1
    if i <= 0:
        return s[0], int(1)
    return s[i:][0], int(s[:i])


class OTPThrottle(BaseThrottle):
    cache = default_cache
    timer = time.time
    scope = "otp"
    DAILY_SUFFIX = "_daily"
    INTERVAL_SUFFIX = "_interval"
    THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES

    def __init__(self):
        self.daily_rate = self.get_rate(self.DAILY_SUFFIX)
        self.daily_requests, self.daily_duration = self.parse_rate(self.daily_rate)

        self.interval_rate = self.get_rate(self.INTERVAL_SUFFIX)
        self.interval_requests, self.interval_duration = self.parse_rate(
            self.interval_rate
        )

    def get_rate(self, suffix):
        try:
            return self.THROTTLE_RATES[self.scope + suffix]
        except KeyError:
            msg = "No default throttle rate set for '%s' scope" % self.scope + suffix
            raise ImproperlyConfigured(msg)

    def parse_rate(self, rate):
        if rate is None:
            return (None, None)
        num, period = rate.split("/")
        num_requests = int(num)
        unit, value = strip_unit_from_value(period)
        duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        return (num_requests, value * duration)

    def get_ident(self, request):
        phone = request.data.get("phone")
        if not phone:
            return super().get_ident(request)
        try:
            user = User.objects.not_deleted().get(phone=phone)
            return user.id
        except User.DoesNotExist:
            return super().get_ident(request)

    def allow_request(self, request, view):
        ident = self.get_ident(request)
        if not ident:
            return True

        daily_key = f"{self.scope}{self.DAILY_SUFFIX}_{ident}"
        interval_key = f"{self.scope}{self.INTERVAL_SUFFIX}_{ident}"

        self.now = self.timer()

        # Check daily throttle
        daily_history = self.cache.get(daily_key, [])
        while daily_history and daily_history[-1] <= self.now - self.daily_duration:
            daily_history.pop()

        if len(daily_history) >= self.daily_requests:
            self.duration = self.daily_duration
            self.throttle_timestamp = daily_history[0]
            return False

        # Check interval throttle
        interval_history = self.cache.get(interval_key, [])
        while (
            interval_history
            and interval_history[-1] <= self.now - self.interval_duration
        ):
            interval_history.pop()

        if len(interval_history) >= self.interval_requests:
            self.duration = self.interval_duration
            self.throttle_timestamp = interval_history[0]
            return False

        # Passed both checks — allow request
        daily_history.append(self.now)
        interval_history.append(self.now)

        self.cache.set(daily_key, daily_history, self.daily_duration)
        self.cache.set(interval_key, interval_history, self.interval_duration)

        return True

    def wait(self):
        if hasattr(self, "duration") and hasattr(self, "throttle_timestamp"):
            elapsed = self.now - self.throttle_timestamp
            return max(self.duration - elapsed, 0)
        return None


class ChangePhoneOTPThrottle(OTPThrottle):

    def get_ident(self, request):
        user = request.user
        if user is None:
            return super().get_ident(request)
        return user.id
