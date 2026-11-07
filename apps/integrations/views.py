from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from apps.iqc.services import process_wms_inbound_shipment
from apps.ipqc.models.ipqc_inspection import IpqcInspection
from apps.ipqc.services import evaluate_and_release_fai, process_cycle_telemetry

User = get_user_model()


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
                "mode": "modular_monolith",
            },
            status=status.HTTP_200_OK,
        )


class WmsShipmentReceivedWebhookView(APIView):
    """
    Webhook ingested when raw resin material arrives at the dock.
    Companion WMS notifies QMS to initiate Incoming Quality Control (IQC).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            task = process_wms_inbound_shipment(request.data)
            return Response(
                {
                    "status": "SUCCESS",
                    "iqc_task_id": str(task.id),
                    "wms_event_id": task.wms_event_id,
                    "lot_number": task.lot_number,
                    "inspection_status": task.status,
                    "material_code": task.material.material_code,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValueError as err:
            return Response(
                {"status": "ERROR", "message": str(err)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as err:
            return Response(
                {"status": "ERROR", "message": f"Internal ingestion error: {str(err)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MesCycleTelemetryWebhookView(APIView):
    """
    Ingests pre-aggregated cycle telemetry summary metrics from MES edge collector.
    Evaluates screw cushion drift (+/- 0.5mm window) and trips Andon line stops
    when 3 consecutive shots breach tolerances.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            summary = process_cycle_telemetry(request.data)
            return Response(
                {
                    "status": "INGESTED",
                    "summary_id": summary.id,
                    "machine_code": summary.machine_code,
                    "shot_number": summary.shot_number,
                    "cushion_mm": str(summary.cushion_mm),
                    "cushion_drift_alert": summary.cushion_drift_alert,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValueError as err:
            return Response(
                {"status": "ERROR", "message": str(err)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as err:
            return Response(
                {"status": "ERROR", "message": f"Internal telemetry error: {str(err)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class IpqcFaiApprovalView(APIView):
    """
    Sub-200ms hard-gating First Article Inspection approval endpoint.
    Validates cavity samples and returns cryptographic release token for MES.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        inspection_id = request.data.get("inspection_id")
        if not inspection_id:
            return Response(
                {"status": "ERROR", "message": "Missing required inspection_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            inspection = IpqcInspection.objects.get(id=inspection_id)
        except IpqcInspection.DoesNotExist:
            return Response(
                {"status": "ERROR", "message": f"Inspection {inspection_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        inspector = None
        badge_number = request.data.get("badge_number")
        if badge_number:
            inspector = User.objects.filter(badge_number=badge_number).first()
        if not inspector and request.user.is_authenticated:
            inspector = request.user

        approved, token, message = evaluate_and_release_fai(inspection, inspector)
        if approved:
            return Response(
                {
                    "status": "APPROVED",
                    "inspection_id": str(inspection.id),
                    "disposition": "RELEASED",
                    "signature_token": token,
                    "mes_run_id": inspection.mes_run_id,
                    "machine_code": inspection.machine_code,
                    "message": message,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "status": "REJECTED",
                    "inspection_id": str(inspection.id),
                    "disposition": "REJECTED",
                    "message": message,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
