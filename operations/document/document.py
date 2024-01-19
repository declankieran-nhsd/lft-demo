import resource
import requests
from datetime import datetime, timezone
import json

# Query on DiagnosticReport endpoint uses the report business identifier to return the DiagnosticReport, and
# includes all ServiceRequests linked to the DiagnosticReport, and
# includes all Specimens linked to the DiagnosticReport, and
# return all of the linked top level Observations referenced in the DiagnosticReport.result element, and
# for all ServiceRequests, returns the subject (which should only be one, TODO is this validated in a constraint?), and
# for all top level Observations, returns all Observations that are in the hasMember element of each Observation
# Note: This query will not return further nested Observations
diagnosticreport_endpoint = "http://localhost:8080/fhir/DiagnosticReport"
diagnosticreport_report_params = {
    'identifier': 'REP-20220308-008902', 
    '_include': [
        'DiagnosticReport:based-on', 
        'DiagnosticReport:specimen', 
        'DiagnosticReport:result'
    ], 
    '_include:iterate': [
        'ServiceRequest:patient', 
        'ServiceRequest:requester',
        'Observation:has-member'
    ]
}

report_resources = requests.get(diagnosticreport_endpoint, diagnosticreport_report_params)
bundle_document = json.loads(report_resources.text)

# Clean out searchset elements
bundle_document.pop('id')
bundle_document.pop('meta')
bundle_document.pop('type')
bundle_document.pop('total')
bundle_document.pop('link')
for e in bundle_document['entry']:
    e.pop('search')

# Create elements to make bundle a document

# Validate against UKCore.  TODO Add validation againt the EU laboratory package?
bundle_meta = {"meta" : {"profile" : ["https://fhir.hl7.org.uk/StructureDefinition/UKCore-Bundle"] }}
bundle_document.update(bundle_meta)

# This idenitifier is used in Composition and DiagnosticReport and can therefore be used to search for the report.  
# See dr-comp-identifier - https://build.fhir.org/ig/hl7-eu/laboratory/StructureDefinition-Bundle-eu-lab.html#constraints
bundle_identifier = {"identifier":  [{"system": "http://Y8J7D-pathlab001.com/report", "value": "REP-20220308-008902"}]}
bundle_document.update(bundle_identifier)

# Bundle of type document - see https://build.fhir.org/ig/hl7-eu/laboratory/index.html#background
bundle_type = {"type": "document"}
bundle_document.update(bundle_type)

# Timestamp is a mandatory - see https://build.fhir.org/ig/hl7-eu/laboratory/StructureDefinition-Bundle-eu-lab.html
timestamp = datetime.now(timezone.utc).isoformat()
bundle_timestamp = {"timestamp": str(timestamp)}
bundle_document.update(bundle_timestamp)

# Example composition to inject into document bundle.
bundle_entry_composition = \
   {
      "fullUrl": "http://localhost:8080/fhir/Composition/138ffee6-fbc1-49e2-bfbc-e14b777ab62a",
      "resource": {
        "resourceType": "Composition",
        "meta": {
          "profile": [
            "https://fhir.hl7.org.uk/StructureDefinition/UKCore-Composition"
          ]
        },
        "identifier": {
          "system": "http://Y8J7D-pathlab001.com/report",
          "value": "REP-20220308-008902"
        },
        "status": "final",
        "type": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "4241000179101",
              "display": "Laboratory report"
            }
          ],
          "text": "Laboratory report"
        },
        "subject": {
          "reference": "http://localhost:8080/fhir/Patient/ab87a3f8-1d37-44a9-804e-5e962598a6e4"
        },
        "date": "2022-03-30T11:24:26+01:00",
        "author": [
          {
            "reference": "http://localhost:8080/fhir/Practitioner/9a835acf-d715-4d84-8dcf-a8435f6417fe"
          }
        ],
        "title": "Laboratory report",
        "attester": [
          {
            "mode": "professional",
            "party": {
              "reference": "http://localhost:8080/fhir/Practitioner/9a835acf-d715-4d84-8dcf-a8435f6417fe"
            }
          },
          {
            "mode": "legal",
            "time": "2022-03-25T11:00:00+01:00",
            "party": {
              "reference": "http://localhost:8080/fhir/Practitioner/9a835acf-d715-4d84-8dcf-a8435f6417fe"
            }
          }
        ],
        "custodian": {
          "reference": "http://localhost:8080/fhir/Organization/3c43b5b3-06d6-445f-ae9a-48d5f05df434"
        },
        "section": [
          {
            "title": "Laboratory examinations",
            "code": {
              "coding": [
                {
                  "system": "https://fhir.hl7.org.uk/CodeSystem/UKCore-RecordStandardHeadings",
                  "code": "test-result",
                  "display": "Test result"
                }
              ]
            },
            "section": [
              {
                "title": "Liver functions tests",
                "code": {
                  "coding": [
                    {
                      "system": "http://snomed.info/sct",
                      "code": "26958001",
                      "display": "Hepatic function panel"
                    }
                  ]
                },
                "entry": [
                  {
                    "reference": "http://localhost:8080/fhir/Observation/33a88119-6dbc-4bdf-809a-c1d822b74e90"
                  }
                ]
              },
              {
                "title": "Urea and electrolytes",
                "code": {
                  "coding": [
                    {
                      "system": "http://snomed.info/sct",
                      "code": "26958001",
                      "display": "Hepatic function panel"
                    }
                  ]
                },
                "entry": [
                  {
                    "reference": "http://localhost:8080/fhir/Observation/a5c7f5e2-eb95-469b-b588-f7861c260ccb"
                  }
                ]
              }
            ]
          }
        ]
      }
    }

# Add the Composition to the Bundle to complete the document
bundle_document['entry'].insert(0, bundle_entry_composition)

# There is no default parameter for DiagnosticReport.custodian, would be easy enough to make a SearchParameter and drop it.
# TODO raise a HL7 Jira ticket for it.
# Just query and drop into bundle as a reminder to create a ticket for it
custodian_uri = "http://localhost:8080/fhir/Organization/3c43b5b3-06d6-445f-ae9a-48d5f05df434"
custodian_resource = json.loads(requests.get(custodian_uri).text)
custodian_bundle_entry = {"fullUrl": custodian_uri, "resource": custodian_resource}
bundle_document['entry'].append(custodian_bundle_entry)

lab_report = json.dumps(bundle_document)

# Update the FHIR server with the document. PUT will create if none exist, see - https://hl7.org/fhir/http.html#update
bundle_endpoint = "http://localhost:8080/fhir/Bundle"
bundle_identifier_param = {
    'identifier': 'REP-20220308-008902'
}
headers = {'Content-type': 'application/fhir+json;fhirVersion=4.0'}
response = requests.put(url=bundle_endpoint, params=bundle_identifier_param, data=lab_report, headers=headers)
