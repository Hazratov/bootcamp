from rest_framework.views import APIView
from rest_framework.response import Response


class HelloWorldAPIView(APIView):
    def get(self, request):
        return Response(data={"message": "hello world"})
    
    def post(self, request):
        message = f'Hello {request.data['name']} welcome to pdp university'
        return Response(data={"greetings": message})
