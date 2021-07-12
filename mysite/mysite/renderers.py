from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.reverse import reverse


#class CustomRenderer(JSONRenderer):
class CustomRenderer(BrowsableAPIRenderer, JSONRenderer):

    def get_default_renderer(self, view):
        return JSONRenderer()

    def render(self, data, accepted_media_type=None, renderer_context=None):
        user = renderer_context.get('request').user
        links = []
        if user.is_authenticated:
            links = renderer_context.get('links')

        required = renderer_context.get('required')
        status_code = renderer_context['response'].status_code
        response = {
          "status": "success",
          "code": status_code,
          "data": data,
          "message": None,
          "required": required,
          "_links": links
        }

        if not str(status_code).startswith('2'):
            response["status"] = "error"
            response["data"] = None
            try:
                response["message"] = data["detail"]
            except (KeyError, TypeError):
                response["data"] = data
        return super(CustomRenderer, self).render(response, accepted_media_type, renderer_context)
