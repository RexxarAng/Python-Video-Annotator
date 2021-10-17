from annotator.annotation_component import AnnotationGraphic


class AnnotationEvent:

    annotation: AnnotationGraphic
    is_interactive: bool = False

    def __init__(self, **kwargs):
        self.annotation = kwargs['annotation']

        if 'is_interactive' in kwargs:
            self.is_interactive = kwargs['is_interactive']

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
