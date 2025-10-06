from fasthtml.common import *
from monsterui.all import *
import datetime
import re
import segno
import io

# ---------- FastHTML App setup with MonsterUI theme ----------

hdrs = Theme.blue.headers()  # pick any: Theme.slate / green / red / etc
app, rt = fast_app(hdrs=hdrs)

# ---------- Helpers ----------

def _escape(text: str) -> str:
    """Escape commas, semicolons, and newlines per vCard rules.
    vCard 3.0 requires escaping "," ";" and "\n" as <backslash>, <backslash>; 
    and <backslash>n in property values.
    """
    if text is None:
        return ""
    s = str(text)
    s = s.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,")
    s = s.replace("\r\n", r"\n").replace("\n", r"\n")
    return s


def build_vcard(data: dict) -> str:
    """Create a vCard 3.0 string from form data.

    We generate the minimal safe set of lines, then add optional blocks for
    multiple emails/phones and home/work addresses.
    """
    # Name components
    prefix = _escape(data.get("prefix", ""))
    first = _escape(data.get("first_name", ""))
    addl = _escape(data.get("additional", ""))
    last = _escape(data.get("last_name", ""))
    suffix = _escape(data.get("suffix", ""))

    fn = data.get("full_name") or " ".join(x for x in [prefix, first, addl, last, suffix] if x)
    fn = _escape(fn.strip())

    org = _escape(data.get("org", ""))
    title = _escape(data.get("title", ""))
    role = _escape(data.get("role", ""))
    url = _escape(data.get("url", ""))
    note = _escape(data.get("note", ""))

    # Birthday -> YYYY-MM-DD or empty
    bday = data.get("bday", "").strip()
    if bday:
        try:
            # Normalize to YYYY-MM-DD
            bday = datetime.date.fromisoformat(bday).isoformat()
        except Exception:
            # fallback: strip all non-digits and try YYYYMMDD
            bday = re.sub(r"[^0-9-]", "", bday)

    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{last};{first};{addl};{prefix};{suffix}",
        f"FN:{fn}",
    ]

    if org:
        lines.append(f"ORG:{org}")
    if title:
        lines.append(f"TITLE:{title}")
    if role:
        lines.append(f"ROLE:{role}")
    if url:
        lines.append(f"URL:{url}")
    if bday:
        lines.append(f"BDAY:{bday}")

    # Emails (comma-separated in form -> multiple EMAIL lines)
    for kind in ("work", "home"):
        val = data.get(f"email_{kind}", "").strip()
        if val:
            lines.append(f"EMAIL;TYPE={kind.upper()}:{_escape(val)}")

    # Phones
    for kind in ("cell", "work", "home"):
        val = data.get(f"tel_{kind}", "").strip()
        if val:
            lines.append(f"TEL;TYPE={kind.upper()}:{_escape(val)}")

    # Addresses
    def adr(prefix_key: str, kind: str):
        street = _escape(data.get(f"{prefix_key}_street", ""))
        city = _escape(data.get(f"{prefix_key}_city", ""))
        region = _escape(data.get(f"{prefix_key}_region", ""))
        postal = _escape(data.get(f"{prefix_key}_postal", ""))
        country = _escape(data.get(f"{prefix_key}_country", ""))
        # ADR format: PO Box;Extended;Street;City;Region;PostalCode;Country
        if any([street, city, region, postal, country]):
            lines.append(
                f"ADR;TYPE={kind.upper()}:;;{street};{city};{region};{postal};{country}"
            )

    adr("home", "home")
    adr("work", "work")

    if note:
        lines.append(f"NOTE:{note}")

    lines.append("END:VCARD")
    vcf = "\r\n".join(lines) + "\r\n"

    return vcf


def generate_qr_code(vcf_data: str) -> bytes:
    """Generate a QR code from vCard data and return as PNG bytes."""
    qr = segno.make(vcf_data, error='h')  # High error correction for better scanning
    buffer = io.BytesIO()
    qr.save(buffer, kind='png', scale=8)  # Scale=8 for good resolution
    buffer.seek(0)
    return buffer.read()


# ---------- UI ----------

def section_title(txt: str):
    return H3(txt, cls="text-lg font-semibold pt-4 mt-6 mb-2")

@rt
def index():
    form = Form(
        section_title("Zur Person"),
        Div(
            LabelInput("Anrede / Präfix", id='prefix', placeholder='Dr.'),
            LabelInput("Vorname", id="first_name", placeholder="Max"),
            LabelInput("Weitere Namen", id="additional", placeholder=""),
            LabelInput("Nachname", id="last_name", placeholder="Mustermann"),
            LabelInput("Namenszusatz / Suffix", id="suffix", placeholder="PhD"),
            LabelInput("Vollständiger Anzeigename (optional)", id="full_name", placeholder="Dr. Max Mustermann, PhD"),
            cls="grid grid-cols-1 lg:grid-cols-2 gap-4",
        ),
        Div(
            LabelInput("Rolle (Role)", id="role", placeholder="Product Manager"),
            LabelInput("Titel (Job Title)", id="title", placeholder="Head of Product"),
            LabelInput("Unternehmen (ORG)", id="org", placeholder="Acme GmbH"),
            LabelInput("Website (URL)", id="url", placeholder="https://acme.example"),
            LabelInput("Geburtstag (YYYY-MM-DD)", id="bday", placeholder="1980-01-31", type_="date"),
            cls="grid grid-cols-1 lg:grid-cols-2 gap-4",
        ),
        section_title("E-Mail"),
        Div(
            LabelInput("E-Mail Arbeit", id="email_work", placeholder="max@acme.example"),
            LabelInput("E-Mail Privat", id="email_home", placeholder="max@example.com"),
            cls="grid grid-cols-1 lg:grid-cols-2 gap-4",
        ),
        section_title("Telefon"),
        Div(
            LabelInput("Mobil", id="tel_cell", placeholder="+49 170 1234567"),
            LabelInput("Arbeit", id="tel_work", placeholder="+49 89 123456-0"),
            LabelInput("Privat", id="tel_home", placeholder="+49 30 1234567"),
            cls="grid grid-cols-1 lg:grid-cols-3 gap-4",
        ),
        section_title("Firmenanschrift (WORK)"),
        Div(
            LabelInput("Straße", id="work_street", placeholder="Hauptstraße 10"),
            LabelInput("PLZ", id="work_postal", placeholder="10115"),
            LabelInput("Stadt", id="work_city", placeholder="Berlin"),
            LabelInput("Bundesland / Region", id="work_region", placeholder="Berlin"),
            LabelInput("Land", id="work_country", placeholder="Deutschland"),
            cls="grid grid-cols-1 lg:grid-cols-5 gap-4",
        ),
        section_title("Private Anschrift (HOME)"),
        Div(
            LabelInput("Straße", id="home_street", placeholder="Musterstraße 1"),
            LabelInput("PLZ", id="home_postal", placeholder="80331"),
            LabelInput("Stadt", id="home_city", placeholder="München"),
            LabelInput("Bundesland / Region", id="home_region", placeholder="Bayern"),
            LabelInput("Land", id="home_country", placeholder="Deutschland"),
            cls="grid grid-cols-1 lg:grid-cols-5 gap-4",
        ),
        section_title("Notiz"),
        Textarea(name="note", placeholder="Optionale Notiz…", cls="textarea textarea-bordered w-full"),
        Div(
            Button("VCF erzeugen", type="submit", cls="btn btn-primary", name="action", value="download"),
            Button("QR-Code erzeugen", type="submit", cls="btn btn-secondary ml-2", name="action", value="qrcode"),
            cls="mt-6"
        ),
        method="post", action="/generate", cls="space-y-2"
    )

    footer = Footer(
        Div(
            A("by Mitja Martini", href="https://mitjamartini.com/about/", cls="link link-hover"),
            A("Privacy", href="https://mitjamartini.com/privacy/", cls="link link-hover"),
            cls="flex gap-4 justify-center"
        ),
        cls="footer footer-center p-4 mt-8"
    )

    content = Card(
        P("Erzeugt eine .vcf-Datei im vCard 3.0 Format. Keine Daten werden gespeichert."),
        form,
        footer,
        cls="mt-4"
    )
    return Titled("vCard/VCF Generator", content)


@rt("/generate", methods=["post"])  # Starlette Request comes through
async def generate(req):
    form = await req.form()
    data = {k: (v if isinstance(v, str) else v.filename if hasattr(v, "filename") else str(v)) for k, v in form.items()}

    action = data.get("action", "download")
    vcf = build_vcard(data)

    if action == "qrcode":
        # Generate QR code
        qr_bytes = generate_qr_code(vcf)
        filename = (data.get("last_name") or data.get("full_name") or "contact").strip() or "contact"
        filename = re.sub(r"[^A-Za-z0-9_.-]", "_", filename) + ".png"

        headers = {
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Content-Type": "image/png",
        }
        return Response(qr_bytes, headers=headers)
    else:
        # Download VCF file
        filename = (data.get("last_name") or data.get("full_name") or "contact").strip() or "contact"
        filename = re.sub(r"[^A-Za-z0-9_.-]", "_", filename) + ".vcf"

        headers = {
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Content-Type": "text/vcard; charset=utf-8",
        }
        return Response(vcf, headers=headers)


if __name__ == "__main__":
    serve()
