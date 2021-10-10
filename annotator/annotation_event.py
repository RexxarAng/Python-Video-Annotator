class AnnotationEvent:
    def __init__(self, **kwargs):
        self.annotation = kwargs['annotation']

    def __repr__(self):
        print('self.__class__.__name__' + ' : ' + str(self.annotation))


class AnnotationCreatedEvent(AnnotationEvent):
    pass


class AnnotationUpdatedEvent(AnnotationEvent):
    pass


class AnnotationDeletedEvent(AnnotationEvent):
    pass


class AnnotationSelectedEvent(AnnotationEvent):
    pass
