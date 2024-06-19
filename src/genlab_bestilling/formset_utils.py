from formset.collection import FormCollection


class ContextFormCollection(FormCollection):
    def __init__(self, *args, context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = context or {}

        for name, holder in self.declared_holders.items():
            self.update_holder_instances(name, holder)

    def update_holder_instances(self, name, holder):
        pass
