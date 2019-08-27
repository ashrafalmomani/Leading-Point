# -*- coding: utf-8 -*-
{
    "name": """Gantt Native Web view""",
    "summary": """Added support Gantt Chart Widget View""",
    "category": "Project",
    "images": ['static/description/icon.png'],
    "version": "12.18.11.9.0",
    "description": """
        Update: python 3.6.3 and click to gantt line
        Fix: momentjs fix
        Update: Calendar
        Update: Info bar before and after Gantt Bar (it can use for addition info)
        Update: Project manual start - and date, sorting from kanban / stage, small fix.
        fix: sotring problem
        Update: Drag UI.
        Update: bug fix group by date 
        Update: Folding
        Update: Remove Canvas and Draw Line by div.
        Update: version and remove js canvas
        Fix: arrow FF position for UI, readonly check
        UI: improve
        UI: more improve
        UI: Fix horizonatal scroll.
        Update: Taks info and Critocal path
        Update: UI not need to much block
        Update: 12.0
        Update: Detail plan, fix ghost bar, fix default start time: allow neagative value..
        Fix: mouse flicker 
        Update: UI - new arrows designe.
    """,
    "author": "Viktor Vorobjov",
    "license": "OPL-1",
    "website": "https://straga.github.io",
    "support": "vostraga@gmail.com",
    "depends": ["web", "web_widget_time_delta"],
    "external_dependencies": {"python": [], "bin": []},
    "data": ['views/web_gantt_src.xml',],
    "qweb": ['static/src/xml/*.xml',],
    "installable": True,
    "auto_install": False,
    "application": False,
}
