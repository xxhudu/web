class Context(dict):
    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)


class AppContext(Context):
    pass


class RouterContext(Context):
    app_ctx = None

    def with_app(self, app_ctx):
        self.app_ctx = app_ctx

    def __getattr__(self, item):
        if item in self.keys():
            return self[item]
        return getattr(self.app_ctx, item)

    def __setattr__(self, key, value):
        self[key] = value