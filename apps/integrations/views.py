from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


class HealthCheckView(APIView):
    """
    Lightweight health check endpoint for Docker container healthchecks and load balancers.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "healthy",
                "service": "qms-automotive",
                "version": "0.1.0",
                "mode": "modular_monolith"
            },
            status=status.HTTP_200_OK
        )
