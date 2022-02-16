
SOFTWARE_NAME = 'EARK Mets Generator'
SOFTWARE_VERSION = '0.0.1-alpha'

NAMESPACES = {
    "": "http://www.loc.gov/METS/",
    "xlink": "http://www.w3.org/1999/xlink",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "csip": "https://DILCIS.eu/XML/METS/CSIPExtensionMETS",
    # "premis": "info:lc/xmlns/premis-v2",
    # "dcterms": "http://purl.org/dc/terms/",
    # "fits": "http://hul.harvard.edu/ois/xml/ns/fits/fits_output",
    # "dc": "http://purl.org/dc/elements/1.1/",
    # "sip": "https://DILCIS.eu/XML/METS/SIPExtensionMETS"
}

SCHEMA_LOCATIONS = (
    "http://www.loc.gov/METS/"
    + " http://www.loc.gov/standards/mets/mets.xsd"
    + " http://www.w3.org/1999/xlink"
    + " http://www.loc.gov/standards/mets/xlink.xsd"
    + " https://DILCIS.eu/XML/METS/CSIPExtensionMETS"
    + " https://earkcsip.dilcis.eu/schema/DILCISExtensionMETS.xsd"
)

CSIP_PROFILE = "https://earkcsip.dilcis.eu/profile/E-ARK-CSIP.xml"
SIP_PROFILE = "https://earksip.dilcis.eu/profile/E-ARK-SIP.xml"

VALID_CITS = {'citsehpj_v1_0': 'Patient Medical Records'}
VALID_TYPES = []