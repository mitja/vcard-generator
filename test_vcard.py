"""Test suite for vCard generator and QR code functionality."""

import pytest
import vobject
from PIL import Image
from qreader import QReader
import io
import numpy as np

from app import build_vcard, generate_qr_code


class TestVCardGeneration:
    """Test vCard generation and parsing."""

    def test_basic_vcard_generation(self):
        """Test that a basic vCard can be generated and parsed."""
        data = {
            "first_name": "Max",
            "last_name": "Mustermann",
            "email_work": "max@example.com",
            "tel_cell": "+49 170 1234567"
        }

        vcf = build_vcard(data)

        # Parse the generated vCard
        vcard = vobject.readOne(vcf)

        # Verify basic fields
        assert vcard.n.value.given == "Max"
        assert vcard.n.value.family == "Mustermann"
        assert vcard.fn.value == "Max Mustermann"

    def test_vcard_with_all_fields(self):
        """Test vCard with all possible fields."""
        data = {
            "prefix": "Dr.",
            "first_name": "Max",
            "additional": "Alexander",
            "last_name": "Mustermann",
            "suffix": "PhD",
            "full_name": "Dr. Max Alexander Mustermann, PhD",
            "org": "Acme GmbH",
            "title": "Head of Product",
            "role": "Product Manager",
            "url": "https://acme.example",
            "bday": "1980-01-31",
            "email_work": "max@acme.example",
            "email_home": "max@example.com",
            "tel_cell": "+49 170 1234567",
            "tel_work": "+49 89 123456-0",
            "tel_home": "+49 30 1234567",
            "work_street": "Hauptstraße 10",
            "work_postal": "10115",
            "work_city": "Berlin",
            "work_region": "Berlin",
            "work_country": "Deutschland",
            "home_street": "Musterstraße 1",
            "home_postal": "80331",
            "home_city": "München",
            "home_region": "Bayern",
            "home_country": "Deutschland",
            "note": "Test contact"
        }

        vcf = build_vcard(data)
        vcard = vobject.readOne(vcf)

        # Verify name components
        assert vcard.n.value.prefix == "Dr."
        assert vcard.n.value.given == "Max"
        assert vcard.n.value.additional == "Alexander"
        assert vcard.n.value.family == "Mustermann"
        assert vcard.n.value.suffix == "PhD"
        assert vcard.fn.value == "Dr. Max Alexander Mustermann, PhD"

        # Verify organization
        assert vcard.org.value[0] == "Acme GmbH"
        assert vcard.title.value == "Head of Product"
        assert vcard.role.value == "Product Manager"

        # Verify URL and birthday
        assert vcard.url.value == "https://acme.example"
        assert vcard.bday.value == "1980-01-31"

        # Verify note
        assert vcard.note.value == "Test contact"

    def test_vcard_email_parsing(self):
        """Test that email addresses are correctly parsed."""
        data = {
            "first_name": "Test",
            "last_name": "User",
            "email_work": "work@example.com",
            "email_home": "home@example.com"
        }

        vcf = build_vcard(data)
        vcard = vobject.readOne(vcf)

        # Get all email addresses
        emails = {email.type_param[0]: email.value for email in vcard.email_list}

        assert "WORK" in emails
        assert emails["WORK"] == "work@example.com"
        assert "HOME" in emails
        assert emails["HOME"] == "home@example.com"

    def test_vcard_phone_parsing(self):
        """Test that phone numbers are correctly parsed."""
        data = {
            "first_name": "Test",
            "last_name": "User",
            "tel_cell": "+49 170 1234567",
            "tel_work": "+49 89 123456-0",
            "tel_home": "+49 30 1234567"
        }

        vcf = build_vcard(data)
        vcard = vobject.readOne(vcf)

        # Get all phone numbers
        phones = {tel.type_param[0]: tel.value for tel in vcard.tel_list}

        assert "CELL" in phones
        assert "WORK" in phones
        assert "HOME" in phones

    def test_vcard_address_parsing(self):
        """Test that addresses are correctly parsed."""
        data = {
            "first_name": "Test",
            "last_name": "User",
            "work_street": "Hauptstraße 10",
            "work_postal": "10115",
            "work_city": "Berlin",
            "work_region": "Berlin",
            "work_country": "Deutschland",
            "home_street": "Musterstraße 1",
            "home_postal": "80331",
            "home_city": "München",
            "home_region": "Bayern",
            "home_country": "Deutschland"
        }

        vcf = build_vcard(data)
        vcard = vobject.readOne(vcf)

        # Get all addresses
        addresses = {adr.type_param[0]: adr for adr in vcard.adr_list}

        assert "WORK" in addresses
        work_adr = addresses["WORK"]
        assert work_adr.value.street == "Hauptstraße 10"
        assert work_adr.value.city == "Berlin"
        assert work_adr.value.code == "10115"

        assert "HOME" in addresses
        home_adr = addresses["HOME"]
        assert home_adr.value.street == "Musterstraße 1"
        assert home_adr.value.city == "München"
        assert home_adr.value.code == "80331"

    def test_vcard_escaping(self):
        """Test that special characters are properly escaped."""
        data = {
            "first_name": "Test,Name",
            "last_name": "User;Name",
            "note": "Line1\nLine2"
        }

        vcf = build_vcard(data)

        # Should be parseable without errors
        vcard = vobject.readOne(vcf)

        # Verify escaping worked
        assert vcard.n.value.given == "Test,Name"
        assert vcard.n.value.family == "User;Name"
        assert "Line1" in vcard.note.value
        assert "Line2" in vcard.note.value


class TestQRCodeGeneration:
    """Test QR code generation and scanning."""

    def test_qr_code_generation(self):
        """Test that QR code can be generated."""
        data = {
            "first_name": "Max",
            "last_name": "Mustermann",
            "email_work": "max@example.com"
        }

        vcf = build_vcard(data)
        qr_bytes = generate_qr_code(vcf)

        # Verify it's a valid PNG
        assert qr_bytes.startswith(b'\x89PNG')
        assert len(qr_bytes) > 0

    def test_qr_code_scanning(self):
        """Test that generated QR code can be scanned and contains vCard data."""
        data = {
            "first_name": "Max",
            "last_name": "Mustermann",
            "email_work": "max@example.com",
            "tel_cell": "+49 170 1234567"
        }

        # Generate vCard and QR code
        vcf = build_vcard(data)
        qr_bytes = generate_qr_code(vcf)

        # Load QR code image and convert to RGB numpy array
        image = Image.open(io.BytesIO(qr_bytes)).convert('RGB')
        image_array = np.array(image)

        # Decode QR code
        qreader = QReader()
        decoded = qreader.detect_and_decode(image=image_array)

        # Verify QR code was decoded
        assert decoded is not None
        assert len(decoded) > 0
        assert decoded[0] is not None
        qr_data = decoded[0]

        # Verify QR code contains vCard data
        assert qr_data == vcf

        # Verify the vCard in QR code is parseable
        vcard = vobject.readOne(qr_data)
        assert vcard.n.value.given == "Max"
        assert vcard.n.value.family == "Mustermann"

    def test_qr_code_with_full_vcard(self):
        """Test QR code with complete vCard data."""
        data = {
            "prefix": "Dr.",
            "first_name": "Max",
            "last_name": "Mustermann",
            "suffix": "PhD",
            "org": "Acme GmbH",
            "title": "Head of Product",
            "email_work": "max@acme.example",
            "tel_cell": "+49 170 1234567",
            "work_street": "Hauptstraße 10",
            "work_postal": "10115",
            "work_city": "Berlin",
            "work_country": "Deutschland"
        }

        # Generate vCard and QR code
        vcf = build_vcard(data)
        qr_bytes = generate_qr_code(vcf)

        # Scan QR code
        image = Image.open(io.BytesIO(qr_bytes)).convert('RGB')
        image_array = np.array(image)
        qreader = QReader()
        decoded = qreader.detect_and_decode(image=image_array)

        assert decoded is not None
        assert len(decoded) > 0
        assert decoded[0] is not None
        qr_data = decoded[0]

        # Parse vCard from QR code
        vcard = vobject.readOne(qr_data)

        # Verify all fields
        assert vcard.n.value.prefix == "Dr."
        assert vcard.n.value.given == "Max"
        assert vcard.n.value.family == "Mustermann"
        assert vcard.n.value.suffix == "PhD"
        assert vcard.org.value[0] == "Acme GmbH"
        assert vcard.title.value == "Head of Product"


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_vcard_to_qr_to_vcard_roundtrip(self):
        """Test complete roundtrip: data -> vCard -> QR code -> scanned vCard -> parsed data."""
        original_data = {
            "first_name": "Anna",
            "last_name": "Schmidt",
            "org": "Test AG",
            "email_work": "anna@test.example",
            "tel_cell": "+49 171 9876543",
            "work_city": "Hamburg"
        }

        # Step 1: Generate vCard
        vcf = build_vcard(original_data)

        # Step 2: Generate QR code
        qr_bytes = generate_qr_code(vcf)

        # Step 3: Scan QR code
        image = Image.open(io.BytesIO(qr_bytes)).convert('RGB')
        image_array = np.array(image)
        qreader = QReader()
        decoded = qreader.detect_and_decode(image=image_array)
        scanned_vcf = decoded[0]

        # Step 4: Parse scanned vCard
        vcard = vobject.readOne(scanned_vcf)

        # Verify data integrity
        assert vcard.n.value.given == "Anna"
        assert vcard.n.value.family == "Schmidt"
        assert vcard.org.value[0] == "Test AG"

        # Verify the scanned vCard matches the original
        assert scanned_vcf == vcf
