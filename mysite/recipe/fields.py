from rest_framework.serializers import RelatedField


class CustomTagField(RelatedField):
    """ custom tag field represented tag by id and name """

    def to_representation(self, value):
        tag = {
            'id': value.id,
            'name': value.name
        }
        return tag
