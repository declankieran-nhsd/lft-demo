# https://build.fhir.org/ig/hl7-eu/laboratory/artifacts.html#structures-resource-profiles
import copy
import argparse
import json
from jinja2 import Template
import pdfkit

def select_resources(document, resourceType):
    if 'entry' not in document:
        return None
    
    # TODO more validation
    
    resources = []

    for entry in document['entry']:
        if entry['resource']['resourceType'] == resourceType:
            resources.append(entry['resource'])

    return resources

def select_composition_sections(composition):
    if 'section' not in composition:
        return None
    
    # TODO more validation

    sections = []

    for section in composition['section']:
        title = copy.deepcopy(section)
        title.pop('section')

        sections.append(title)

        for level1_section in section['section']:
            sections.append(level1_section)
    
    return sections

def get_panel_values(observation, specimens):
    return (
        observation["id"], 
        observation["code"]["coding"][0]
    )

def get_item_values(observation, specimens):
    specimen_id = observation["specimen"]["reference"].split('/')[-1]

    for specimen in specimens:
        if specimen_id == specimen["id"]:
            value = ""
            if "valueString" in observation:
                value = observation["valueString"]
            elif "valueQuantity" in observation:
                value = observation["valueQuantity"]

            return (
                observation["derivedFrom"][0]["reference"].split('/')[-1],
                specimen["identifier"][0]["value"], 
                observation["code"]["coding"][0], 
                value
            )

def organise_observations(observations, specimens):
    panels = []
    items = []

    for observation in observations:
        # relying on derivedFrom here feels like a bit of a hack     
        if "derivedFrom" not in observation:
            panel = get_panel_values(observation, specimens)
            panels.append(panel)
        else:
            item = get_item_values(observation, specimens)
            items.append(item)

    organised = []

    for panel in panels:
        for item in items:
            if panel[0] == item[0]:
                result = {}
                result[panel[1]["code"]] = (item[1], item[2], item[3], panel[0], panel[1]['display'])
                organised.append(result)

    return organised

def organise_by_section(composition, organised_observations):
    organised = []
    
    for section in composition["section"][0]["section"]:
        panels = []
        panels.append(section["title"])
        panels.append([])
        for panel in organised_observations:
            panel_code = list(panel.keys())[0]
            if(section["code"]["coding"][0]["code"] == panel_code) and \
               section["entry"][0]["reference"].split(':')[-1] == panel[panel_code][3]:
                panitem = {}
                panitem["code"] = section["code"]["coding"][0]["code"]
                panitem["item"] = panel[section["code"]["coding"][0]["code"]]
                panels[1].append(panitem)
        organised.append(panels)

    return organised

############################# MAIN #############################

# Get args
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--document", type=str, help="The document Bundle in JSON format.", required=True)
parser.add_argument("-t", "--template", type=str, help="The jinja2 template to use.", required=True)
parser.add_argument("-o", "--out", type=str, help="File path to output html and pdf render.")
args = parser.parse_args()
document = json.load(open(args.document))

# Get resources
composition = select_resources(document, 'Composition')
diagnostic_report = select_resources(document, 'DiagnosticReport')
observations = select_resources(document, 'Observation')
patient = select_resources(document, 'Patient')
specimens = select_resources(document, 'Specimen')

# Organise panels and sections
organised_observations = organise_observations(observations, specimens)
sections = organise_by_section(composition[0], organised_observations)

# Setup template
template = open("report.j2").read()
stylesheet = open("style.css").read()
t = Template(template)

# Render the template
render = t.render(composition=composition[0],
                  patient=patient[0],
                  specimens=specimens,
                  sections=sections,
                  stylesheet=stylesheet)

# Print html to stdout
print(render)

# Output html and pdf files
if args.out is not None:
    html = open(args.out + '.html', 'w')
    html.writelines(render)
    html.close()
    pdfkit.from_file(args.out + '.html', args.out + '.pdf')



