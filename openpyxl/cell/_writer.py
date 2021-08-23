# Copyright (c) 2010-2021 openpyxl

from openpyxl.compat import safe_string
from openpyxl.xml.functions import Element, SubElement, whitespace, XML_NS, REL_NS
from openpyxl import LXML
from openpyxl.utils.datetime import to_excel, to_ISO8601
from datetime import timedelta


def _set_attributes(cell, styled=None):
    """
    Set coordinate and datatype
    """
    coordinate = cell.coordinate
    attrs = {'r': coordinate}
    if styled:
        attrs['s'] = f"{cell.style_id}"

    if cell.data_type == "s":
        attrs['t'] = "inlineStr"
    elif cell.data_type != 'f':
        attrs['t'] = cell.data_type

    value = cell._value

    if cell.data_type == "d":
        if hasattr(value, "tzinfo") and value.tzinfo is not None:
            raise TypeError("Excel does not support timezones in datetimes. "
                    "The tzinfo in the datetime/time object must be set to None.")

        if cell.parent.parent.iso_dates and not isinstance(value, timedelta):
            value = to_ISO8601(value)
        else:
            attrs['t'] = "n"
            value = to_excel(value, cell.parent.parent.epoch)

    if cell.hyperlink:
        cell.parent._hyperlinks.append(cell.hyperlink)

    return value, attrs


def etree_write_cell(xf, worksheet, cell, styled=None):

    value, attributes = _set_attributes(cell, styled)

    print("etree_write_cell")
    print(f"value: {value}")
    print(f"attributes: {attributes}")

    el = Element("c", attributes)
    if value is None or value == "":
        xf.write(el)
        return

    if cell.data_type == 'f':
        print("Formula type...")
        shared_formula = worksheet.formula_attributes.get(cell.coordinate, {})
        print(f"Shared formula: {shared_formula}")
        formula = SubElement(el, 'f', {"v": "1"})
        # pre_computed_value = SubElement(el, 'v')
        # pre_computed_value.text = 1
        print(f"Formula: {formula}")
        print(f"Value is: {value}")
        if value is not None:
            formula.text = value[1:]
            value = None

    if cell.data_type == 's':
        print("Cell data type is 's'")
        inline_string = SubElement(el, 'is')
        text = SubElement(inline_string, 't')
        text.text = value
        whitespace(text)


    else:
        cell_content = SubElement(el, 'v')
        if value is not None:
            cell_content.text = safe_string(value)
        else:
            if cell.data_type == 'f' and value is None:
                cell_content.text = safe_string('1') # Trying to avoid #Value! error

    print(f"~~~~~~~~ Etree cell")
    print(f"{el.attrib}")
    print("Keys:")
    for k in el.keys():
        print(f"{k}")
    print("Text:")
    print(el.text)
    print(f"~~~~~~~~ Etree cell")

    xf.write(el)


def lxml_write_cell(xf, worksheet, cell, styled=False):
    value, attributes = _set_attributes(cell, styled)

    if value == '' or value is None:
        with xf.element("c", attributes):
            return

    with xf.element('c', attributes):
        if cell.data_type == 'f':
            shared_formula = worksheet.formula_attributes.get(cell.coordinate, {})
            with xf.element('f', shared_formula):
                if value is not None:
                    xf.write(value[1:])
                    value = None
            print(f"lxml formula cell: {shared_formula}")

        if cell.data_type == 's':
            with xf.element("is"):
                attrs = {}
                if value != value.strip():
                    attrs["{%s}space" % XML_NS] = "preserve"
                el = Element("t", attrs) # lxml can't handle xml-ns
                el.text = value
                xf.write(el)

                print(f"lxml string cell: {el}")
                #with xf.element("t", attrs):
                    #xf.write(value)
        else:
            with xf.element("v"):
                if value is not None:
                    xf.write(safe_string(value))


if LXML:
    write_cell = lxml_write_cell
else:
    write_cell = etree_write_cell
