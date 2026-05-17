import xml.etree.ElementTree as ET
import json
import sys
import argparse

def parse_ddl(xml_path):
    # Namespace dictionary
    ns = {'an': 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD03'}
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        return {"error": str(e)}

    # 1. Metadata extraction
    metadata = {}
    
    # Identification
    work = root.find('.//an:FRBRWork', ns)
    if work is not None:
        metadata['date'] = work.find('an:FRBRdate', ns).attrib.get('date')
        metadata['number'] = work.find('an:FRBRnumber', ns).attrib.get('value')
        metadata['type'] = work.find('an:FRBRsubtype', ns).attrib.get('value')

    # Proponents (Senators)
    proponents = []
    # Find docProponent in coverPage
    for prop in root.findall('.//an:coverPage//an:docProponent', ns):
        person_id = prop.attrib.get('refersTo', '').lstrip('#')
        name = prop.text.strip() if prop.text else ""
        # Try to find the person details in references if needed, 
        # but for now, we take what's in docProponent
        proponents.append({"id": person_id, "name": name})
    
    metadata['proponents'] = proponents

    # 2. Body / Articles extraction
    articles = []
    body = root.find('.//an:body', ns)
    if body is not None:
        for art in body.findall('.//an:article', ns):
            art_id = art.attrib.get('id')
            num = art.find('an:num', ns).text if art.find('an:num', ns) is not None else ""
            
            heading_el = art.find('an:heading', ns)
            heading = ""
            if heading_el is not None:
                # Get all text from heading, including nested tags like <an:i>
                heading = "".join(heading_el.itertext()).strip()

            # Extract paragraphs
            paragraphs = []
            for p in art.findall('.//an:paragraph', ns):
                p_num = p.find('an:num', ns).text if p.find('an:num', ns) is not None else ""
                # Text content
                p_text = "".join(p.itertext()).strip()
                # Remove the leading number if it's repeated in the text
                if p_num and p_text.startswith(p_num):
                    p_text = p_text[len(p_num):].strip()
                
                paragraphs.append({
                    "num": p_num,
                    "text": p_text
                })

            articles.append({
                "id": art_id,
                "num": num,
                "heading": heading,
                "paragraphs": paragraphs
            })

    return {
        "metadata": metadata,
        "articles": articles
    }

def main():
    parser = argparse.ArgumentParser(description="Parse Akoma Ntoso DDL XML")
    parser.add_argument("file", help="Path to the XML file")
    parser.add_argument("--output", help="Path to save JSON output")
    args = parser.parse_args()

    result = parse_ddl(args.file)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Result saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
