from django.shortcuts import render

def custom_404_view(request, exception):
    response = render(request, '404.html', status=404)
    response.status_code = 404
    return response
