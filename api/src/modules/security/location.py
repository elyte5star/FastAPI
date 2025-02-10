from modules.security.device import DeviceMetaDataChecker
from fastapi import Request
from modules.repository.schema.users import NewLocationToken, UserLocation, User
import geoip2.database
from modules.utils.misc import get_indent
from fastapi_events.dispatcher import dispatch
from modules.security.events.base import UserEvents, StrangeLocation


class DifferentLocationChecker(DeviceMetaDataChecker):

    async def check_strange_location(
        self,
        user: User,
        request: Request,
    ) -> bool:
        ip_address = self.get_client_ip_address(request)
        loc_token = await self.is_new_login_location(user, ip_address)
        if loc_token is not None:
            app_url = self.get_app_url(request)
            event_payload = StrangeLocation(
                app_url=app_url,
                ip=ip_address,
                token=loc_token.token,
                username=user.username,
                email=user.email,
                country=loc_token.location.country,
            )
            dispatch(UserEvents.STRANGE_LOCATION, event_payload)
            return True
        return False

    async def is_new_login_location(
        self, user: User, ip: str
    ) -> NewLocationToken | None:
        if not self.is_geo_ip_enabled():
            self.logger.warning("GEO IP DISABALED BY ADMIN")
            return None
        country = await self.get_country_from_ip(ip)
        self.logger.debug(f"country :: {country}")
        user_loc = await self.find_user_location_by_country_and_user_query(
            country, user
        )
        if user_loc is None:
            return await self.create_new_location_token(user, country)
        elif not user_loc.enabled:
            return user_loc.new_location
        return None

    async def create_new_location_token(
        self, user: User, country: str
    ) -> NewLocationToken | None:
        user_loc = UserLocation(id=get_indent(), country=country, owner=user)
        user_loc = await self.create_user_location_query(user_loc)
        token = self.create_timed_token(user.email)
        new_loc_token = NewLocationToken(
            id=get_indent(), token=token, location=user_loc
        )
        new_loc_token = await self.create_new_location_token_query(
            new_loc_token,
        )
        return new_loc_token

    async def get_country_from_ip(self, ip: str) -> str:
        country = "UNKNOWN"
        try:
            with geoip2.database.Reader(
                "./modules/static/maxmind/GeoLite2-Country.mmdb"
            ) as reader:
                response = reader.country(ip)
                country = response.country.name
                return country
        except Exception as e:
            self.logger.error(e)
            return country
