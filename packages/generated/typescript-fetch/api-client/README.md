# @placeframe/api-client@0.1.0

A TypeScript SDK client for the localhost API.

## Usage

First, install the SDK from npm.

```bash
npm install @placeframe/api-client --save
```

Next, try it out.


```ts
import {
  Configuration,
  DefaultApi,
} from '@placeframe/api-client';
import type { CreateCaptureSessionRequest } from '@placeframe/api-client';

async function example() {
  console.log("🚀 Testing @placeframe/api-client SDK...");
  const api = new DefaultApi();

  const body = {
    // DeviceType
    deviceType: ...,
    // Blob
    data: BINARY_DATA_HERE,
    // string
    name: name_example,
    // string (optional)
    id: 38400000-8cf0-11bd-b23e-10b96e4ef00d,
    // Date | datetime with the constraint that the value must have timezone info (optional)
    recordedAt: 2013-10-20T19:20:30+01:00,
  } satisfies CreateCaptureSessionRequest;

  try {
    const data = await api.createCaptureSession(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```


## Documentation

### API Endpoints

All URIs are relative to *http://localhost:8000*

| Class | Method | HTTP request | Description
| ----- | ------ | ------------ | -------------
*DefaultApi* | [**createCaptureSession**](docs/DefaultApi.md#createcapturesession) | **POST** /capture_sessions | CreateCaptureSession
*DefaultApi* | [**createCaptureSessions**](docs/DefaultApi.md#createcapturesessions) | **POST** /capture_sessions/bulk | CreateCaptureSessions
*DefaultApi* | [**createGraph**](docs/DefaultApi.md#creategraphoperation) | **POST** /graph | CreateGraph
*DefaultApi* | [**createGroup**](docs/DefaultApi.md#creategroup) | **POST** /groups | CreateGroup
*DefaultApi* | [**createGroupsBatch**](docs/DefaultApi.md#creategroupsbatch) | **POST** /groups/batch | CreateGroupsBatch
*DefaultApi* | [**createLayer**](docs/DefaultApi.md#createlayer) | **POST** /layers | CreateLayer
*DefaultApi* | [**createLocalizationMap**](docs/DefaultApi.md#createlocalizationmap) | **POST** /localization-maps | CreateLocalizationMap
*DefaultApi* | [**createNode**](docs/DefaultApi.md#createnode) | **POST** /nodes | CreateNode
*DefaultApi* | [**createNodesBatch**](docs/DefaultApi.md#createnodesbatch) | **POST** /nodes/batch | CreateNodesBatch
*DefaultApi* | [**createReconstruction**](docs/DefaultApi.md#createreconstruction) | **POST** /reconstructions | CreateReconstruction
*DefaultApi* | [**deleteCaptureSession**](docs/DefaultApi.md#deletecapturesession) | **DELETE** /capture_sessions/{id} | DeleteCaptureSession
*DefaultApi* | [**deleteGroups**](docs/DefaultApi.md#deletegroups) | **DELETE** /groups | DeleteGroups
*DefaultApi* | [**deleteLayers**](docs/DefaultApi.md#deletelayers) | **DELETE** /layers | DeleteLayers
*DefaultApi* | [**deleteLocalizationMap**](docs/DefaultApi.md#deletelocalizationmap) | **DELETE** /localization-maps/{id} | DeleteLocalizationMap
*DefaultApi* | [**deleteLocalizationMaps**](docs/DefaultApi.md#deletelocalizationmaps) | **DELETE** /localization-maps | DeleteLocalizationMaps
*DefaultApi* | [**deleteNodes**](docs/DefaultApi.md#deletenodes) | **DELETE** /nodes | DeleteNodes
*DefaultApi* | [**deleteReconstruction**](docs/DefaultApi.md#deletereconstruction) | **DELETE** /reconstructions/{id} | DeleteReconstruction
*DefaultApi* | [**downloadCaptureSessionTar**](docs/DefaultApi.md#downloadcapturesessiontar) | **GET** /capture_sessions/{id}/tar | DownloadCaptureSessionTar
*DefaultApi* | [**exportReconstructionTar**](docs/DefaultApi.md#exportreconstructiontar) | **GET** /reconstructions/{id}/tar | ExportReconstructionTar
*DefaultApi* | [**getCaptureSession**](docs/DefaultApi.md#getcapturesession) | **GET** /capture_sessions/{id} | GetCaptureSession
*DefaultApi* | [**getCaptureSessionFramesCsv**](docs/DefaultApi.md#getcapturesessionframescsv) | **GET** /capture_sessions/{id}/frames.csv | GetCaptureSessionFramesCsv
*DefaultApi* | [**getCaptureSessionImage**](docs/DefaultApi.md#getcapturesessionimage) | **GET** /capture_sessions/{id}/images/{frame_timestamp} | GetCaptureSessionImage
*DefaultApi* | [**getCaptureSessionManifestFile**](docs/DefaultApi.md#getcapturesessionmanifestfile) | **GET** /capture_sessions/{id}/manifest.json | GetCaptureSessionManifestFile
*DefaultApi* | [**getCaptureSessionReconstructions**](docs/DefaultApi.md#getcapturesessionreconstructions) | **GET** /capture_sessions/{id}/reconstructions | GetCaptureSessionReconstructions
*DefaultApi* | [**getCaptureSessionRigConfig**](docs/DefaultApi.md#getcapturesessionrigconfig) | **GET** /capture_sessions/{id}/rig_config | GetCaptureSessionRigConfig
*DefaultApi* | [**getCaptureSessions**](docs/DefaultApi.md#getcapturesessions) | **GET** /capture_sessions | GetCaptureSessions
*DefaultApi* | [**getCaptureSessionsExpanded**](docs/DefaultApi.md#getcapturesessionsexpanded) | **GET** /capture_sessions/expanded | GetCaptureSessionsExpanded
*DefaultApi* | [**getGroups**](docs/DefaultApi.md#getgroups) | **GET** /groups | GetGroups
*DefaultApi* | [**getLayers**](docs/DefaultApi.md#getlayers) | **GET** /layers | GetLayers
*DefaultApi* | [**getLocalizationMap**](docs/DefaultApi.md#getlocalizationmap) | **GET** /localization-maps/{id} | GetLocalizationMap
*DefaultApi* | [**getLocalizationMaps**](docs/DefaultApi.md#getlocalizationmaps) | **GET** /localization-maps | GetLocalizationMaps
*DefaultApi* | [**getLocalizerVersion**](docs/DefaultApi.md#getlocalizerversion) | **GET** /localize/version | GetLocalizerVersion
*DefaultApi* | [**getNodes**](docs/DefaultApi.md#getnodes) | **GET** /nodes | GetNodes
*DefaultApi* | [**getReconstruction**](docs/DefaultApi.md#getreconstruction) | **GET** /reconstructions/{id} | GetReconstruction
*DefaultApi* | [**getReconstructionFramePoses**](docs/DefaultApi.md#getreconstructionframeposes) | **GET** /reconstructions/{id}/frame_poses | GetReconstructionFramePoses
*DefaultApi* | [**getReconstructionLocalizationMap**](docs/DefaultApi.md#getreconstructionlocalizationmap) | **GET** /reconstructions/{id}/localization_map | GetReconstructionLocalizationMap
*DefaultApi* | [**getReconstructionMetrics**](docs/DefaultApi.md#getreconstructionmetrics) | **GET** /reconstructions/{id}/metrics | GetReconstructionMetrics
*DefaultApi* | [**getReconstructionPoints**](docs/DefaultApi.md#getreconstructionpoints) | **GET** /reconstructions/{id}/points | GetReconstructionPoints
*DefaultApi* | [**getReconstructions**](docs/DefaultApi.md#getreconstructions) | **GET** /reconstructions | GetReconstructions
*DefaultApi* | [**getServerInfo**](docs/DefaultApi.md#getserverinfo) | **GET** /server-info | GetServerInfo
*DefaultApi* | [**importReconstructionTar**](docs/DefaultApi.md#importreconstructiontar) | **POST** /reconstructions/tar | ImportReconstructionTar
*DefaultApi* | [**listLocalizationEvaluations**](docs/DefaultApi.md#listlocalizationevaluations) | **GET** /reconstructions/{reconstruction_id}/localization-evaluations | ListLocalizationEvaluations
*DefaultApi* | [**localizeImage**](docs/DefaultApi.md#localizeimage) | **POST** /localize | LocalizeImage
*DefaultApi* | [**pauseReconstruction**](docs/DefaultApi.md#pausereconstruction) | **POST** /reconstructions/{id}/pause | PauseReconstruction
*DefaultApi* | [**resumeReconstruction**](docs/DefaultApi.md#resumereconstruction) | **POST** /reconstructions/{id}/resume | ResumeReconstruction
*DefaultApi* | [**updateCaptureSession**](docs/DefaultApi.md#updatecapturesession) | **PATCH** /capture_sessions/{id} | UpdateCaptureSession
*DefaultApi* | [**updateCaptureSessions**](docs/DefaultApi.md#updatecapturesessions) | **PATCH** /capture_sessions | UpdateCaptureSessions
*DefaultApi* | [**updateGroups**](docs/DefaultApi.md#updategroups) | **PATCH** /groups | UpdateGroups
*DefaultApi* | [**updateLayers**](docs/DefaultApi.md#updatelayers) | **PATCH** /layers | UpdateLayers
*DefaultApi* | [**updateLocalizationMap**](docs/DefaultApi.md#updatelocalizationmap) | **PATCH** /localization-maps/{id} | UpdateLocalizationMap
*DefaultApi* | [**updateLocalizationMaps**](docs/DefaultApi.md#updatelocalizationmaps) | **PATCH** /localization-maps | UpdateLocalizationMaps
*DefaultApi* | [**updateNodes**](docs/DefaultApi.md#updatenodes) | **PATCH** /nodes | UpdateNodes
*DefaultApi* | [**upsertLocalizationEvaluation**](docs/DefaultApi.md#upsertlocalizationevaluation) | **POST** /reconstructions/{reconstruction_id}/localization-evaluations | UpsertLocalizationEvaluation


### Models

- [AxisConvention](docs/AxisConvention.md)
- [CaptureSessionBatchUpdate](docs/CaptureSessionBatchUpdate.md)
- [CaptureSessionCreate](docs/CaptureSessionCreate.md)
- [CaptureSessionManifest](docs/CaptureSessionManifest.md)
- [CaptureSessionRead](docs/CaptureSessionRead.md)
- [CaptureSessionUpdate](docs/CaptureSessionUpdate.md)
- [CaptureSessionsExpanded](docs/CaptureSessionsExpanded.md)
- [CreateGraphRequest](docs/CreateGraphRequest.md)
- [CreateGraphResponse](docs/CreateGraphResponse.md)
- [DeviceType](docs/DeviceType.md)
- [ExpandedCaptureSession](docs/ExpandedCaptureSession.md)
- [ExpandedReconstruction](docs/ExpandedReconstruction.md)
- [Float3](docs/Float3.md)
- [Float4](docs/Float4.md)
- [GetCaptureSessions400Response](docs/GetCaptureSessions400Response.md)
- [GetCaptureSessions400ResponseExtra](docs/GetCaptureSessions400ResponseExtra.md)
- [GroupBatchCreate](docs/GroupBatchCreate.md)
- [GroupBatchUpdate](docs/GroupBatchUpdate.md)
- [GroupCreate](docs/GroupCreate.md)
- [GroupRead](docs/GroupRead.md)
- [LabelType](docs/LabelType.md)
- [LayerBatchUpdate](docs/LayerBatchUpdate.md)
- [LayerCreate](docs/LayerCreate.md)
- [LayerRead](docs/LayerRead.md)
- [LinkType](docs/LinkType.md)
- [LocalizationEvaluationCreate](docs/LocalizationEvaluationCreate.md)
- [LocalizationEvaluationRead](docs/LocalizationEvaluationRead.md)
- [LocalizationMapBatchUpdate](docs/LocalizationMapBatchUpdate.md)
- [LocalizationMapCreate](docs/LocalizationMapCreate.md)
- [LocalizationMapRead](docs/LocalizationMapRead.md)
- [LocalizationMapUpdate](docs/LocalizationMapUpdate.md)
- [LocalizationMetrics](docs/LocalizationMetrics.md)
- [MapLocalization](docs/MapLocalization.md)
- [NodeBatchCreate](docs/NodeBatchCreate.md)
- [NodeBatchUpdate](docs/NodeBatchUpdate.md)
- [NodeCreate](docs/NodeCreate.md)
- [NodeRead](docs/NodeRead.md)
- [PhaseTiming](docs/PhaseTiming.md)
- [PinholeCameraConfig](docs/PinholeCameraConfig.md)
- [ReconstructionCreate](docs/ReconstructionCreate.md)
- [ReconstructionCreateWithOptions](docs/ReconstructionCreateWithOptions.md)
- [ReconstructionMetrics](docs/ReconstructionMetrics.md)
- [ReconstructionOptions](docs/ReconstructionOptions.md)
- [ReconstructionReadWithQueue](docs/ReconstructionReadWithQueue.md)
- [ReconstructionStatus](docs/ReconstructionStatus.md)
- [RigCameraConfig](docs/RigCameraConfig.md)
- [RigConfig](docs/RigConfig.md)
- [ServerInfo](docs/ServerInfo.md)
- [Transform](docs/Transform.md)

### Authorization

Endpoints do not require authorization.


## About

This TypeScript SDK client supports the [Fetch API](https://fetch.spec.whatwg.org/)
and is automatically generated by the
[OpenAPI Generator](https://openapi-generator.tech) project:

- API version: `0.1.0`
- Package version: `0.1.0`
- Generator version: `7.22.0`
- Build package: `org.openapitools.codegen.languages.TypeScriptFetchClientCodegen`

The generated npm module supports the following:

- Environments
  * Node.js
  * Webpack
  * Browserify
- Language levels
  * ES5 - you must have a Promises/A+ library installed
  * ES6
- Module systems
  * CommonJS
  * ES6 module system


## Development

### Building

To build the TypeScript source code, you need to have Node.js and npm installed.
After cloning the repository, navigate to the project directory and run:

```bash
npm install
npm run build
```

### Publishing

Once you've built the package, you can publish it to npm:

```bash
npm publish
```

## License

[]()
