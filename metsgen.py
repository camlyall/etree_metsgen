import getopt
import hashlib
import mimetypes
import os
import uuid
import xml.etree.ElementTree as ET
import sys
import utils
from pathlib import Path
from datetime import datetime, timedelta


def remove_package_divider(package: str, is_prefix: bool) -> str:
    possible_dividers = ['-', '_']

    package = package.strip()

    for divider in possible_dividers:
        if is_prefix:
            if package.endswith(divider):
                return package[:-1].strip()
        else:
            if package.startswith(divider):
                return package[1:].strip()


def get_package_name(package: str) -> str:

    pkg_name = ""

    UUID4_LENGTH = 36

    # Determine location of uuid if present
    if len(package) >= UUID4_LENGTH:
        test_prefix = 'uuid-'
        # See if the package is just uuid
        if is_valid_uuid(package):
            return ''

        if test_prefix in package:
            prefix_index = package.index(test_prefix)
            uuid_index = prefix_index + len(test_prefix)
            try:
                test_uuid = package[uuid_index:uuid_index+36]
            except IndexError:
                pass
            else:
                if is_valid_uuid(test_uuid):
                    pre_uuid = package[:prefix_index]
                    post_uuid = package[uuid_index+36:]
                    if pre_uuid != '':
                        pkg_name = remove_package_divider(pre_uuid, is_prefix=True)
                    elif post_uuid != '':
                        pkg_name = remove_package_divider(post_uuid, is_prefix=False)
                    return pkg_name

        if is_valid_uuid(package[-36:]):
            return remove_package_divider(package[:-36], is_prefix=True)

        if is_valid_uuid(package[:36]):
            return remove_package_divider(package[36:], is_prefix=False)

    return package


def is_valid_uuid(string: str) -> bool:
    try:
        uuid.UUID(string, version=4)
    except ValueError:
        return False
    else:
        return True


def get_checksum(file: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


def new_uuid(prefix: str) -> str:
    return prefix + str(uuid.uuid4())


def discover_files(directory: Path, ) -> dict:
    files_dict = {}
    for root, dirs, files in os.walk(directory):
        if files:
            if 'METS.xml' in files:
                dirs[:] = []
            files_dict[str(Path(root).relative_to(directory.parent))] = files
    return files_dict


def generate_mets(directory: Path, content_info_type: str, agent_data: dict, is_root_mets = True):

    nsmap = utils.NAMESPACES
    schemas = utils.SCHEMA_LOCATIONS

    if is_root_mets and agent_data:
        schemas = schemas + " " + agent_data["patientclinicalschemaDataLink"]
    elif agent_data:
        schemas = schemas + " " + agent_data.get("patientschemaDataLink")

    now = datetime.utcnow()
    bst_now = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S%z")

    # Mets attributes, dependant on the content information type

    if is_root_mets:
        objid = get_package_name(directory.name) + ' - ' + new_uuid('uuid-')

    else:
        objid = directory.name

    mets_element_attrib = {
        'OBJID': objid,
        'LABEL': "CSIP Information Package",
        'TYPE': 'OTHER',
        '{%s}OTHERTYPE' % nsmap['csip']: 'MIXED',
        '{%s}CONTENTINFORMATIONTYPE' % nsmap['csip']: 'MIXED',
        'PROFILE': utils.CSIP_PROFILE,
        '{%s}schemaLocation' % nsmap['xsi']: schemas
        }
    if content_info_type in utils.VALID_CITS.keys():
        mets_element_attrib['{%s}CONTENTINFORMATIONTYPE' % nsmap['csip']] = content_info_type
        mets_type = utils.VALID_CITS[content_info_type]
        if mets_type in utils.VALID_TYPES:
            mets_element_attrib['TYPE'] = mets_type
            mets_element_attrib.pop('{%s}OTHERTYPE' % nsmap['csip'])
        else:
            mets_element_attrib['{%s}OTHERTYPE' % nsmap['csip']] = mets_type

    mets_element = ET.Element('{%s}mets' % nsmap[''], attrib=mets_element_attrib)

    # Mets Header
    metsHdr_element = ET.SubElement(mets_element, '{%s}metsHdr' % nsmap[''],
                                    attrib={
                                        'CREATEDATE': bst_now,
                                        'LASTMODDATE': bst_now,
                                        'RECORDSTATUS': 'NEW',
                                        '{%s}OAISPACKAGETYPE' % nsmap['csip']: 'SIP'
                                    })

    ## Agents
    sofware_agent = ET.SubElement(metsHdr_element, '{%s}agent' % nsmap[''], attrib={'ROLE': 'CREATOR', 'TYPE': 'OTHER', 'OTHERTYPE': 'SOFTWARE'})
    software_agent_name = ET.SubElement(sofware_agent, '{%s}name' % nsmap[''])
    software_agent_name.text = utils.SOFTWARE_NAME
    software_agent_note = ET.SubElement(sofware_agent, '{%s}note' % nsmap[''], attrib={'{%s}NOTETYPE' % nsmap['csip']: 'SOFTWARE VERSION'})
    if agent_data['softwareVersion']:
        software_agent_note.text = agent_data['softwareVersion']
    else:
        software_agent_note.text = utils.SOFTWARE_VERSION
    if agent_data:
        if agent_data['creatorName'] and agent_data['creatorID']:
            creator_agent = ET.SubElement(metsHdr_element, '{%s}agent' % nsmap[''], attrib={'ROLE': 'CREATOR', 'TYPE': 'OTHER', 'OTHERTYPE': 'ORGANISATION'})
            creator_agent_name = ET.SubElement(creator_agent, '{%s}name' % nsmap[''])
            creator_agent_name.text = agent_data['creatorName']
            creator_agent_note = ET.SubElement(creator_agent, '{%s}note' % nsmap[''], attrib={'{%s}NOTETYPE' % nsmap['csip']: 'IDENTIFICATIONCODE'})
            creator_agent_note.text = agent_data['creatorID']
        if agent_data['submitterName'] and agent_data['submitterdetails']:
            submitter_agent = ET.SubElement(metsHdr_element, '{%s}agent' % nsmap[''], attrib={'ROLE': 'OTHER', 'OTHERTYPE': 'SUBMITTER', 'TYPE': 'INDIVIDUAL'})
            submitter_agent_name = ET.SubElement(submitter_agent, '{%s}name' % nsmap[''])
            submitter_agent_name.text = agent_data['submitterName']
            submitter_agent_note = ET.SubElement(submitter_agent, '{%s}note' % nsmap[''], attrib={'{%s}NOTETYPE' % nsmap['csip']: 'IDENTIFICATIONCODE'})
            submitter_agent_note.text = agent_data['submitterdetails']
        if agent_data['archiveName'] and agent_data['archiveID']:
            archivist_agent = ET.SubElement(metsHdr_element, '{%s}agent' % nsmap[''], attrib={'ROLE': 'ARCHIVIST', 'TYPE': 'OTHER', 'OTHERTYPE': "ORGANISATION"})
            archivist_agent_name = ET.SubElement(archivist_agent, '{%s}name' % nsmap[''])
            archivist_agent_name.text = agent_data['archiveName']
            archivist_agent_note = ET.SubElement(archivist_agent, '{%s}note' % nsmap[''], attrib={'{%s}NOTETYPE' % nsmap['csip']: 'IDENTIFICATIONCODE'})
            archivist_agent_note.text = agent_data['archiveID']
        if agent_data['preservation'] and agent_data['preservationID']:
            presevation_agent = ET.SubElement(metsHdr_element, '{%s}agent' % nsmap[''], attrib={'ROLE': 'PRESERVATION', 'TYPE': 'OTHER', 'OTHERTYPE': "ORGANISATION"})
            presevation_agent_name = ET.SubElement(presevation_agent, '{%s}name' % nsmap[''])
            presevation_agent_name.text = agent_data['preservation']
            presevation_agent_note = ET.SubElement(presevation_agent, '{%s}note' % nsmap[''], attrib={'{%s}NOTETYPE' % nsmap['csip']: 'IDENTIFICATIONCODE'})
            presevation_agent_note.text = agent_data['preservationID']

        ## AltRecordIDs
        alt_ids = ['submissionagreement', 'referencecode', 'previoussubmissionagreement', 'previousreferencecode']
        for alt_id in alt_ids:
            if agent_data[alt_id]:
                alt_rec_id_element = ET.SubElement(metsHdr_element, '{%s}altRecordID' % nsmap[''], attrib={'TYPE': alt_id.upper()})
                alt_rec_id_element.text = agent_data[alt_id]

    # DMD Sec
    # if descriptive metadata
    descriptive_metadata_directory = directory / 'metadata' / 'descriptive'
    if descriptive_metadata_directory.is_dir():
        for file in descriptive_metadata_directory.iterdir():
            dmdSec_element = ET.SubElement(mets_element, '{%s}dmdSec' % nsmap[''],
                                           attrib={
                                               'ID': new_uuid('uuid-'),
                                               'CREATED': bst_now,
                                               'STATUS': 'CURRENT'
                                           })
            mdRef_element = ET.SubElement(dmdSec_element, '{%s}mdRef' % nsmap[''],
                                          attrib={
                                              '{%s}href' % nsmap['xlink']: str(file.relative_to(directory)),
                                              '{%s}type' % nsmap['xlink']: 'simple',
                                              'MDTYPE': 'OTHER',
                                              'OTHERMDTYPE': 'othermdtype',
                                              'LOCTYPE': 'URL',
                                              'MIMETYPE': str(mimetypes.guess_type(file)[0]),
                                              'SIZE': str(file.stat().st_size),
                                              'CREATED': datetime.fromtimestamp(file.stat().st_ctime).strftime("%Y-%m-%dT%H:%M:%S%z"),
                                              'CHECKSUM': get_checksum(file),
                                              'CHECKSUMTYPE': 'SHA-256',
                                          })
    
    # FileSec
    fileSec_element = ET.SubElement(mets_element, '{%s}fileSec' % nsmap[''], attrib={'ID': new_uuid('uuid-')})
    if is_root_mets:
        accepted_directories = ['documentation', 'representations', 'schemas']
    else:
        accepted_directories = ['data', 'schemas']
    for folder in directory.iterdir():
        if folder.is_dir() and folder.name in accepted_directories:
            files = discover_files(folder)
            for path in files.keys():
                if content_info_type in utils.VALID_CITS.keys():
                    fileGrp_use = Path(path).parts[0].capitalize()
                else:
                    fileGrp_use = path.capitalize()
                fileGrp_element = ET.SubElement(fileSec_element, '{%s}fileGrp' % nsmap[''],
                                                attrib={
                                                    'USE': fileGrp_use,
                                                    'ID': new_uuid('uuid-')
                                                })
                for file in files[path]:
                    file_path: Path = directory / path / file
                    file_element = ET.SubElement(fileGrp_element, '{%s}file' % nsmap[''],
                                                 attrib={
                                                     'ID': new_uuid('ID-'),
                                                     'CHECKSUM': get_checksum(file_path),
                                                     'CHECKSUMTYPE': 'SHA-256',
                                                     'MIMETYPE': str(mimetypes.guess_type(file_path)[0]),
                                                     'SIZE': str(file_path.stat().st_size),
                                                     'CREATED': datetime.fromtimestamp(file_path.stat().st_ctime).strftime("%Y-%m-%dT%H:%M:%S%z")
                                                 })
                                                 
                    ET.SubElement(file_element, '{%s}FLocat' % nsmap[''],
                                    attrib={
                                        '{%s}href' % nsmap['xlink']: str(file_path.relative_to(directory)),
                                        'LOCTYPE': 'URL',
                                        '{%s}type' % nsmap['xlink']: 'simple'
                                    })
                                                   
    # Add structmap
    mets_element.append(csip_struct_map(mets_element, content_info_type, nsmap))

    mets = ET.ElementTree(mets_element)

    ET.indent(mets, space='    ', level=0)
    mets.write(directory / "METS.xml", encoding='utf-8', xml_declaration=True)


def csip_struct_map(mets: ET.ElementTree, cit: str, nsmap: dict) -> ET.Element:
    # Struct Map
    structMap = ET.Element('{%s}structMap' % nsmap[''],
                           attrib={
                               'ID': new_uuid('uuid-'),
                               'TYPE': 'PHYSICAL',
                               'LABEL': "CSIP"
                           })
    root_div = ET.SubElement(structMap, '{%s}div' % nsmap[''],
                            attrib={
                                'ID': new_uuid('uuid-'),
                                'LABEL': mets.get('OBJID')
                            })
    for dmdSec in mets.findall('{%s}dmdSec' % nsmap['']):
        dmdSec_div = ET.SubElement(root_div, '{%s}div' % nsmap[''], attrib={
                                       'ID': new_uuid('uuid-'),
                                       'DMDID': dmdSec.get('ID'),
                                       'LABEL': 'Metadata'
                                   })
    for fileGrp in mets.find('{%s}fileSec' % nsmap['']).findall('{%s}fileGrp' % nsmap['']):
        
        sub_div = ET.SubElement(root_div, '{%s}div' % nsmap[''], attrib={'ID': new_uuid('uuid-'), 'LABEL': fileGrp.get('USE')})

        files = fileGrp.findall('{%s}file' % nsmap[''])

        # If the file is mets.xml use mptr else use fptr
        if len(files) == 1 and files[0].get('MIMETYPE').endswith('/xml'):
            flocat = files[0].find('{%s}FLocat' % nsmap[''])
            href = Path(flocat.get('{%s}href' % nsmap['xlink']))

            div_to_use = sub_div
            if cit in utils.VALID_CITS.keys():
                for parent in range(len(href.parent.parts[1:])):
                    parent_div = ET.SubElement(div_to_use, '{%s}div' % nsmap[''], attrib={'ID': new_uuid('uuid-'), 'LABEL': '/'.join(href.parent.parts[:parent+2])})
                    div_to_use = parent_div
            if str(href).lower().endswith('mets.xml'):
                ET.SubElement(div_to_use, '{%s}mptr' % nsmap[''],
                            attrib={
                                '{%s}type' % nsmap['xlink']: 'simple',
                                '{%s}href' % nsmap['xlink']: str(href),
                                '{%s}title' % nsmap['xlink']: fileGrp.get('ID'),
                                'LOCTYPE': 'URL'
                            })
        else:
            ET.SubElement(sub_div, '{%s}fptr' % nsmap[''],
                        attrib={
                            'FILEID': fileGrp.get('ID')
                        })
    return structMap


def extract_agent_data(metadata_file):
    metadata_dict = {}
    open_metadata_file = open(metadata_file, "r")
    metadata_content = open_metadata_file.read()
    open_metadata_file.close()
    tree = ET.fromstring(metadata_content)
    for c in tree:
        metadata_dict[c.tag] = c.text.strip()
    return metadata_dict


def main(argv):
    sip_dir = ''
    cit = 'MIXED' # Content Information Type
    try:
        opts, args = getopt.getopt(argv,"hi:c:",["input=, contentinfotype="])
    except getopt.GetoptError:
        print('metsgen.py -i <SIP directory> (Optional: -c <contentinfotype>) >')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('metsgen.py -i <SIP directory> (Optional: -c <contentinfotype>)')
            sys.exit()
        elif opt in ("-i", "--input"):
            input_arg = Path(arg)
            if input_arg.is_dir() and (input_arg / 'representations').is_dir() :
                sip_dir = input_arg
            else:
                print("Input is not a valid directory")
                sys.exit()
        elif opt in ('-c', '--contentinfotype'):
            if arg:
                cit = arg

    if sip_dir == '':
        print('No input directory given')
        sys.exit()

    # Register Namespaces
    for prefix, uri in utils.NAMESPACES.items():
        ET.register_namespace(prefix, uri)

    # Extract agent metadata from root metadata.xml
    if (sip_dir / 'metadata.xml').is_file():
        agent_data = extract_agent_data(sip_dir / 'metadata.xml')

    # Generate METS.xml for each representation
    for rep_dir in (sip_dir / 'representations').iterdir():
        if rep_dir.is_dir():
            generate_mets(rep_dir, cit, agent_data, is_root_mets=False)
    # Generate root METS.xml
    generate_mets(sip_dir, cit, agent_data)


if __name__ == '__main__':
    main(sys.argv[1:])