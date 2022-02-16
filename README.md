## ElementTree Mets Generator
EARK METS.xml generator for EARK SIPS. For use in digital archiving.
METS.xml files are generated on the representation and root level.

<br>

### Requirements
Python3.9+

<br>

### Generate METS.xml
python3 metsgen.py -i \<SIP directory>

Options:

-i &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; --input &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; \<SIP input> &nbsp;&nbsp;&nbsp;&nbsp; (Mandatory)

-c &nbsp;&nbsp;&nbsp;&nbsp; --contentinfotype &nbsp;&nbsp;&nbsp;&nbsp; \<ContentInformationType> &nbsp;&nbsp;&nbsp;&nbsp; (Optional)

<br>

#### Currently supported CITs
- citsehpj_v1_0

