class AuthenticationEvent:

    def on_success_login(self):
        pass

    def on_failure_login(self):
        pass

    def login_notification(self):
        pass

    def is_geo_ip_lib_enabled(self) -> bool:
        pass
