import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
class TestFrontendDashboardAndTerminals:
    def test_dashboard_view_renders_200(self, client):
        url = reverse("dashboard")
        response = client.get(url)
        assert response.status_code == 200
        assert "Plant Quality & Andon Overview" in response.content.decode()

    def test_iqc_terminal_renders_200(self, client):
        url = reverse("iqc:index")
        response = client.get(url)
        assert response.status_code == 200
        assert "Incoming QC & Resin Acceptance" in response.content.decode()

    def test_ipqc_terminal_renders_200(self, client):
        url = reverse("ipqc:index")
        response = client.get(url)
        assert response.status_code == 200
        assert "Shopfloor Machine Surveillance" in response.content.decode()

    def test_oqc_terminal_renders_200(self, client):
        url = reverse("oqc:index")
        response = client.get(url)
        assert response.status_code == 200
        assert "Outgoing QC" in response.content.decode()
        assert "Shipping Quality Clearance" in response.content.decode()
