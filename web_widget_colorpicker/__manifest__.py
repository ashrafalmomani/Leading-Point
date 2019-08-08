# -*- coding: utf-8 -*-
{
    "name": """Web Widget Colorpicker""",
    "summary": """Added Color Picker for From""",
    "category": "Project",
    "images": ['static/description/icon.png'],
    "version": "12.18.10.11.0",
    "description": """
            For Form View - added = widget="colorpicker"
            ...
            <field name="arch" type="xml">
                <form string="View name">
                    ...
                    <field name="colorpicker" widget="colorpicker"/>
                    ...
                </form>
            </field>
            ...
    """,
    "author": "Viktor Vorobjov",
    "license": "LGPL-3",
    "website": "https://straga.github.io",
    "support": "vostraga@gmail.com",
    "depends": ["web"],
    "external_dependencies": {"python": [], "bin": []},
    "data": ['view/web_widget_colorpicker_view.xml'],
    "qweb": ['static/src/xml/widget.xml',],
    "installable": True,
    "auto_install": False,
    "application": False,
}
