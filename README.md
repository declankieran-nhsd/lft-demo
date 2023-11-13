# lft-demo  

A demo using the [HAPI-FHIR Starter Project](https://github.com/hapifhir/hapi-fhir-jpaserver-starter) to construct a report for an [LFT order](https://simplifier.net/guide/pathology-fhir-implementation-guide/Home/FHIRAssets/AllAssets/All-Profiles/Examples/Bundles/Liver-Function-and-U-Es-Report) conformant to the [HL7 Europe Laboratory Report](https://build.fhir.org/ig/hl7-eu/laboratory) specification.

The steps in this demo are as follows:

## Bring up FHIR with UKCore package

The docker command

`docker run -d -p 8080:8080 hapiproject/hapi:v6.2.2`

will bring up [HAPI-FHIR Starter Project](https://github.com/hapifhir/hapi-fhir-jpaserver-starter) server on port 8080.  

To load the UKCore package a mount folder can be created and the package can be loaded using the following docker command, provided the package has been copied to the mount folder, i.e. `~/package`.  This also makes the server use UUIDs by default.

`docker run -d --v ~/package:/package -p 8080:8080 -e hapi.fhir.daoconfig_client_id_strategy=UUID -e hapi.fhir.client_id_strategy=ANY -e hapi.fhir.implementationguides.ukcore.name=fhir.r4.ukcore.stu3.currentbuild -e hapi.fhir.implementationguides.ukcore.version=0.0.3-pre-release -e hapi.fhir.implementationguides.ukcore.url=file:///package/ukcore-0.0.3-pre-release_with-precalculated-snapshots.tgz hapiproject/hapi:v6.2.2`

The server will take around a minute to a minute and a half to fully start.

## Create an LFT request and then update with Observations

Two [transaction Bundles](https://www.hl7.org/fhir/http.html#transaction) have been created for the examples for the [Liver Function examples](https://simplifier.net/guide/pathology-fhir-implementation-guide/Home/Examples/Examples-Index) in the pathlogy IG.  These transactions examples are using [PUTs](https://hl7.org/fhir/http.html#update) in the request, so it would be possible to modify and reload in an idempotent fashion. 

## Query for the resource associated with the LFT tests

The following query will return all the resources required to create a report for this particular request using the primary DiagnosticReport business identifier.

`http://localhost:8080/fhir/DiagnosticReport?identifier=REP-20220308-008902&_include=DiagnosticReport:based-on&_include=DiagnosticReport:specimen&_include:iterate=ServiceRequest:patient&_include=DiagnosticReport:result&_include:iterate=Observation:has-member`

This searchset Bundle is then transformed into a Document by inserting a Composition and the required metadata, as well as removing any redundant elements.  The python script [report.py](operations/report.py) provides this function in the pipeline.

## Output the example Document

These steps are all ran in a github action and the resulting document output is published as an artefact in the pipeline.

<img src="https://github.com/declankieran-nhsd/lft-demo/assets/93662162/47b93f8a-e06b-4b59-be15-9058ca33af99" width="50%">

## POSTMAN Examples

The entire set of interactions is also included in a [postman collection](postman/lft-example-interactions.postman_collection.json).  This includes:

* LFT Request
  * Transaction Bundle with initial LFT request
* LFT Result
  * Transaction Bundle to update with results, i.e add Observations
* LFT Report Query
  * A query that will return all resources available to construct the Document Bundle for the Laboratory Report
* Store Laboratory Report Document
  * A Document Bundle with an example Composition as well as the LFT resources
* Laboratory Report Document Bundle Query
  * A query for the Report using the primary business identifier used, i.e. REP-20220308-008902
