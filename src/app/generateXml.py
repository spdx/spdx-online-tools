import math
import re
import xml.etree.ElementTree as ET
from itertools import chain, tee

entityMap = {
    '>': '&gt;',
    '<': '&lt;',
    "'": '&apos;',
    '"': '&quot;',
    '&': '&amp;'
}
letterBullets = r"^(\s*)([^\s\w]?(?!(v|V) ?\.)(?:[a-zA-Z]|[MDCLXVImdclxvi]+)[^\s\w])(\s)"
numberBullets = r"^(\s*)([^\s\w]?[0-9]+[^\s\w]|[^\s\w]?[0-9]+(?:\.[0-9]+)[^\s\w]?)(\s)"
symbolBullets = r"^(\s*)([*\u2022\-])(\s)"

    
def previous_and_current(some_iterable):
    prevs, items = tee(some_iterable, 2)
    prevs = chain([None], prevs)
    return list(zip(prevs, items))


def escapeXmlData(string):
    for initial,final in list(entityMap.items()):
        string.replace(initial, final)
    return string


def isBullet(string):
    """ To check if the line has bullet or not.
    """
    isLetterBullet = re.search(letterBullets, string)
    isNumberBullet = re.search(numberBullets, string)
    isSymbolBullet = re.search(symbolBullets, string)
    if isLetterBullet or isNumberBullet or isSymbolBullet:
        return True
    return False


def wrapBullets(string, item):
    """ Wrap bullets around the bullet tags.
    """
    letterBullet = re.search(letterBullets, string)
    numberBullet = re.search(numberBullets, string)
    symbolBullet = re.search(symbolBullets, string)
    bullet = letterBullet or numberBullet or symbolBullet    
    ET.SubElement(item, "bullet").text = bullet.group(2)
    string = string.replace(bullet.group(2), '').strip()
    return string


def groupLines(lines):
    """ Creates a list of dictionary of each line containing data, tagType and depth of the line. 
    """
    lis = []
    for line in lines:
        if isBullet(line):
            line = re.sub(r"\t", '      ', line)
            matches = re.search(r"^( *)", line).group(1)
            if not matches:
                depth = 0
            else:
                depth = int(math.floor(len(matches)/4))
            tagType = 'item'
            lis.append({'data':line, 'depth':depth, 'tagType':tagType})
        else:
            tagType = 'p'
            lis.append({'data':line, 'tagType':tagType})
    return lis


def insertOls(lines):
    """ Insert dictionary of tagType list before the the begining and after the ending of a list.
    """
    depth = -1
    newLines = []
    for line in lines:
        if isBullet(line.get('data')):
            if line.get('depth') < depth:
                while line.get('depth') < depth:
                    newLines.append({ 'tagType': 'list', 'isStart': False, 'data': '' })
                    depth -= 1
            elif line.get('depth') > depth:
                while line.get('depth') > depth:
                    newLines.append({ 'tagType': 'list', 'isStart': True, 'data': '' })
                    depth += 1
        newLines.append(line)
    while 0 <= depth:
        newLines.append({ 'tagType': 'list', 'isStart': False, 'data': '' })
        depth -= 1
    #newLines.append({ 'tagType': 'list', 'isStart': False, 'data': '' })
    return newLines


def getTextElement(points):
    """ Returns the text element of the license XML.
    """
    licenseTextElement = ET.Element("text")
    elements = []
    elements.append(licenseTextElement)
    for pp,point in previous_and_current(points):
        if point.get('isStart'):
            elements.append(ET.Element("list"))
        
        elif point.get('isStart') is False:
            n = len(elements)
            if elements[n-2].findall('item'):
                elements[n-2].findall('item')[-1].append(elements[n-1])
            else:
                 elements[n-2].append(elements[n-1])
            elements.pop()
        else:
            if pp:
                if point.get('tagType') == "p" and pp.get('tagType') == "item":
                    p = ET.Element("p")
                    p.text = point.get('data')
                    elements[-1].findall('item')[-1].append(p)
                    continue
            if point.get('tagType') == "p":
                p = ET.Element("p")
                p.text = point.get('data')
                elements[-1].append(p)
        
            elif point.get('tagType') == "item":
                item = ET.Element("item")
                ET.SubElement(item, "p").text = wrapBullets(point.get('data'), item)
                elements[-1].append(item)
    return elements[0]


def generateLicenseXml(licenseOsi, licenseIdentifier, licenseName, listVersionAdded, licenseSourceUrls, licenseHeader, licenseNotes, licenseText, isException=False):
    """ Generate a spdx license xml
    returns the license xml as a string
    """
    root = ET.Element("SPDXLicenseCollection", xmlns="http://www.spdx.org/license")
    if licenseOsi=="Approved":
        licenseOsi = "true"
    else:
        licenseOsi = "false"
    if isException:
        license = ET.SubElement(root, "exception", isOsiApproved=licenseOsi, licenseId=licenseIdentifier, listVersionAdded=listVersionAdded, name=licenseName)
    else:
        license = ET.SubElement(root, "license", isOsiApproved=licenseOsi, licenseId=licenseIdentifier, listVersionAdded=listVersionAdded, name=licenseName)
    crossRefs = ET.SubElement(license, "crossRefs")
    for sourceUrl in licenseSourceUrls:
        ET.SubElement(crossRefs, "crossRef").text = sourceUrl
    ET.SubElement(license, "standardLicenseHeader").text = licenseHeader
    ET.SubElement(license, "notes").text = licenseNotes
    licenseText = escapeXmlData(licenseText)
    licenseLines = licenseText.replace('\r','').split('\n\n')
    objList = groupLines(licenseLines)
    points = insertOls(objList)
    textElement = getTextElement(points)
    license.append(textElement)
    xmlString = ET.tostring(root, method='xml', encoding='unicode')
    return xmlString
