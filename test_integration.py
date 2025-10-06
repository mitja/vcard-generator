"""Integration tests for vCard generator Docker deployment.

These tests verify that the application works correctly when deployed in a Docker container.
They test the full stack including HTTP endpoints, vCard generation, and QR code generation.

Run with: pytest test_integration.py -v
Or: ./test_integration.sh
"""

import pytest
import subprocess
import time
import requests
from pathlib import Path
import tempfile


# Test configuration
IMAGE_NAME = "vcard-generator:test"
CONTAINER_NAME = "vcard-test-integration"
TEST_PORT = 8889
BASE_URL = f"http://localhost:{TEST_PORT}"


@pytest.fixture(scope="module")
def docker_container():
    """Build and run Docker container for testing, then clean up."""

    # Build the Docker image
    print(f"\nBuilding Docker image: {IMAGE_NAME}")
    build_result = subprocess.run(
        ["docker", "build", "-t", IMAGE_NAME, "."],
        capture_output=True,
        text=True
    )

    if build_result.returncode != 0:
        pytest.fail(f"Docker build failed:\n{build_result.stderr}")

    # Stop and remove any existing container with the same name
    subprocess.run(
        ["docker", "rm", "-f", CONTAINER_NAME],
        capture_output=True
    )

    # Start the container
    print(f"Starting container: {CONTAINER_NAME} on port {TEST_PORT}")
    run_result = subprocess.run(
        [
            "docker", "run", "--rm", "-d",
            "-p", f"{TEST_PORT}:80",
            "--name", CONTAINER_NAME,
            IMAGE_NAME
        ],
        capture_output=True,
        text=True
    )

    if run_result.returncode != 0:
        pytest.fail(f"Docker run failed:\n{run_result.stderr}")

    container_id = run_result.stdout.strip()
    print(f"Container started: {container_id[:12]}")

    # Wait for container to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(BASE_URL, timeout=2)
            if response.status_code == 200:
                print("Container is ready!")
                break
        except requests.exceptions.RequestException:
            pass

        if i == max_retries - 1:
            # Get logs before failing
            logs = subprocess.run(
                ["docker", "logs", CONTAINER_NAME],
                capture_output=True,
                text=True
            )
            subprocess.run(["docker", "stop", CONTAINER_NAME], capture_output=True)
            pytest.fail(f"Container failed to start:\n{logs.stdout}\n{logs.stderr}")

        time.sleep(0.5)

    yield container_id

    # Cleanup
    print(f"\nStopping container: {CONTAINER_NAME}")
    subprocess.run(["docker", "stop", CONTAINER_NAME], capture_output=True)


class TestDockerDeployment:
    """Test Docker container deployment."""

    def test_container_running(self, docker_container):
        """Test that the container is running."""
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        assert CONTAINER_NAME in result.stdout

    def test_container_logs_no_errors(self, docker_container):
        """Test that container logs don't contain critical errors."""
        result = subprocess.run(
            ["docker", "logs", CONTAINER_NAME],
            capture_output=True,
            text=True
        )
        logs = result.stdout + result.stderr

        # Check for expected startup messages
        assert "Started server process" in logs
        assert "Uvicorn running" in logs

        # Check for common error patterns
        assert "ModuleNotFoundError" not in logs
        assert "ImportError" not in logs
        assert "Error" not in logs or "ERROR" not in logs


class TestHTTPEndpoints:
    """Test HTTP endpoints of the deployed application."""

    def test_homepage_accessible(self, docker_container):
        """Test that the homepage is accessible and returns 200."""
        response = requests.get(BASE_URL)
        assert response.status_code == 200
        assert "vCard" in response.text or "VCF" in response.text

    def test_homepage_content_type(self, docker_container):
        """Test that homepage returns HTML content."""
        response = requests.get(BASE_URL)
        assert "text/html" in response.headers.get("Content-Type", "")

    def test_homepage_contains_form(self, docker_container):
        """Test that homepage contains the vCard generation form."""
        response = requests.get(BASE_URL)
        # Check for form elements
        assert "first_name" in response.text or "First" in response.text
        assert "last_name" in response.text or "Last" in response.text


class TestVCardGeneration:
    """Test vCard file generation via HTTP."""

    def test_generate_basic_vcard(self, docker_container):
        """Test generating a basic vCard with minimal data."""
        response = requests.post(
            f"{BASE_URL}/generate",
            data={
                "first_name": "John",
                "last_name": "Doe",
                "email_work": "john.doe@example.com",
                "tel_cell": "+1234567890"
            }
        )

        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "text/vcard; charset=utf-8"
        assert "attachment" in response.headers.get("Content-Disposition", "")

        # Verify vCard content
        vcf = response.text
        assert "BEGIN:VCARD" in vcf
        assert "VERSION:3.0" in vcf
        assert "N:Doe;John" in vcf
        assert "FN:John Doe" in vcf
        assert "EMAIL;TYPE=WORK:john.doe@example.com" in vcf
        assert "END:VCARD" in vcf

    def test_generate_full_vcard(self, docker_container):
        """Test generating a vCard with all fields."""
        response = requests.post(
            f"{BASE_URL}/generate",
            data={
                "prefix": "Dr.",
                "first_name": "Jane",
                "last_name": "Smith",
                "suffix": "PhD",
                "org": "Acme Corp",
                "title": "Senior Engineer",
                "email_work": "jane@acme.com",
                "tel_cell": "+9876543210",
                "work_street": "123 Main St",
                "work_city": "Boston",
                "work_postal": "02101",
                "work_country": "USA"
            }
        )

        assert response.status_code == 200
        vcf = response.text

        assert "N:Smith;Jane;;Dr.;PhD" in vcf
        assert "ORG:Acme Corp" in vcf
        assert "TITLE:Senior Engineer" in vcf
        assert "EMAIL;TYPE=WORK:jane@acme.com" in vcf
        assert "TEL;TYPE=CELL:+9876543210" in vcf

    def test_vcard_filename(self, docker_container):
        """Test that vCard filename is based on last name."""
        response = requests.post(
            f"{BASE_URL}/generate",
            data={
                "first_name": "Test",
                "last_name": "User"
            }
        )

        assert response.status_code == 200
        content_disp = response.headers.get("Content-Disposition", "")
        assert "User.vcf" in content_disp or "filename=" in content_disp


class TestQRCodeGeneration:
    """Test QR code generation via HTTP."""

    def test_generate_qr_code(self, docker_container):
        """Test generating a QR code with vCard data."""
        response = requests.post(
            f"{BASE_URL}/generate",
            data={
                "first_name": "QR",
                "last_name": "Test",
                "email_work": "qr@example.com",
                "action": "qrcode"
            }
        )

        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "image/png"
        assert "attachment" in response.headers.get("Content-Disposition", "")

        # Verify it's a PNG file
        assert response.content.startswith(b'\x89PNG')

    def test_qr_code_filename(self, docker_container):
        """Test that QR code filename is based on last name."""
        response = requests.post(
            f"{BASE_URL}/generate",
            data={
                "first_name": "QR",
                "last_name": "TestUser",
                "action": "qrcode"
            }
        )

        assert response.status_code == 200
        content_disp = response.headers.get("Content-Disposition", "")
        assert "TestUser.png" in content_disp or "filename=" in content_disp

    def test_qr_code_is_valid_png(self, docker_container):
        """Test that generated QR code is a valid PNG image."""
        response = requests.post(
            f"{BASE_URL}/generate",
            data={
                "first_name": "Valid",
                "last_name": "PNG",
                "action": "qrcode"
            }
        )

        # Save to temp file and verify with external tool
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(response.content)
            temp_path = f.name

        try:
            # Use 'file' command to verify PNG
            result = subprocess.run(
                ["file", temp_path],
                capture_output=True,
                text=True
            )
            assert "PNG image data" in result.stdout
        finally:
            Path(temp_path).unlink()


class TestDependencies:
    """Test that all required dependencies are installed in the container."""

    def test_segno_installed(self, docker_container):
        """Test that segno package is installed."""
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "python", "-c", "import segno"],
            capture_output=True
        )
        assert result.returncode == 0

    def test_fasthtml_installed(self, docker_container):
        """Test that python-fasthtml is installed."""
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "python", "-c", "import fasthtml"],
            capture_output=True
        )
        assert result.returncode == 0

    def test_monsterui_installed(self, docker_container):
        """Test that MonsterUI is installed."""
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "python", "-c", "import monsterui"],
            capture_output=True
        )
        assert result.returncode == 0

    def test_uvicorn_installed(self, docker_container):
        """Test that uvicorn is installed."""
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "python", "-c", "import uvicorn"],
            capture_output=True
        )
        assert result.returncode == 0


if __name__ == "__main__":
    # Allow running directly with: python test_integration.py
    pytest.main([__file__, "-v", "--tb=short"])
