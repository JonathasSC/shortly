from django.views.generic import TemplateView


class NotFoundView(TemplateView):
    template_name = "common/404.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.status_code = 404
        return response
