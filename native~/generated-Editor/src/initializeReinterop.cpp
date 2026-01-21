#include <cassert>
#include <cstdint>
#include <DotNet/CesiumForUnity/AssetTroubleshootingDetails.h>
#include <DotNet/CesiumForUnity/Cesium3DTile.h>
#include <DotNet/CesiumForUnity/Cesium3DTileset.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include <DotNet/CesiumForUnity/Cesium3DTilesetLoadFailureDetails.h>
#include <DotNet/CesiumForUnity/CesiumAzureMapsRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumBingMapsRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumCameraManager.h>
#include <DotNet/CesiumForUnity/CesiumCartographicPolygon.h>
#include <DotNet/CesiumForUnity/CesiumCredit.h>
#include <DotNet/CesiumForUnity/CesiumCreditComponent.h>
#include <DotNet/CesiumForUnity/CesiumCreditSystem.h>
#include <DotNet/CesiumForUnity/CesiumDebugColorizeTilesRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumEditorUtility.h>
#include <DotNet/CesiumForUnity/CesiumEditorWindow.h>
#include <DotNet/CesiumForUnity/CesiumEllipsoid.h>
#include <DotNet/CesiumForUnity/CesiumFeature.h>
#include <DotNet/CesiumForUnity/CesiumFeatureIdAttribute.h>
#include <DotNet/CesiumForUnity/CesiumFeatureIdSet.h>
#include <DotNet/CesiumForUnity/CesiumFeatureIdTexture.h>
#include <DotNet/CesiumForUnity/CesiumGeoreference.h>
#include <DotNet/CesiumForUnity/CesiumGlobeAnchor.h>
#include <DotNet/CesiumForUnity/CesiumGoogleMapTilesRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumIntMat2x2.h>
#include <DotNet/CesiumForUnity/CesiumIntMat3x3.h>
#include <DotNet/CesiumForUnity/CesiumIntMat4x4.h>
#include <DotNet/CesiumForUnity/CesiumIntVec2.h>
#include <DotNet/CesiumForUnity/CesiumIntVec3.h>
#include <DotNet/CesiumForUnity/CesiumIntVec4.h>
#include <DotNet/CesiumForUnity/CesiumIonAsset.h>
#include <DotNet/CesiumForUnity/CesiumIonRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumIonServer.h>
#include <DotNet/CesiumForUnity/CesiumIonServerManager.h>
#include <DotNet/CesiumForUnity/CesiumIonSession.h>
#include <DotNet/CesiumForUnity/CesiumMetadata.h>
#include <DotNet/CesiumForUnity/CesiumMetadataValue.h>
#include <DotNet/CesiumForUnity/CesiumMetadataValueType.h>
#include <DotNet/CesiumForUnity/CesiumModelMetadata.h>
#include <DotNet/UnityEngine/Mesh.h>
#include <DotNet/CesiumForUnity/CesiumObjectPool1.h>
#include <DotNet/CesiumForUnity/CesiumObjectPools.h>
#include <DotNet/CesiumForUnity/CesiumPointCloudRenderer.h>
#include <DotNet/CesiumForUnity/CesiumPolygonRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/CesiumForUnity/CesiumPropertyArray.h>
#include <DotNet/CesiumForUnity/CesiumPropertyTable.h>
#include <DotNet/CesiumForUnity/CesiumPropertyTableProperty.h>
#include <DotNet/CesiumForUnity/CesiumRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumRasterOverlayLoadFailureDetails.h>
#include <DotNet/CesiumForUnity/CesiumRuntimeSettings.h>
#include <DotNet/CesiumForUnity/CesiumSampleHeightResult.h>
#include <DotNet/CesiumForUnity/CesiumSimplePlanarEllipsoidCurve.h>
#include <DotNet/CesiumForUnity/CesiumTileExcluder.h>
#include <DotNet/CesiumForUnity/CesiumTileMapServiceRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumUintMat2x2.h>
#include <DotNet/CesiumForUnity/CesiumUintMat3x3.h>
#include <DotNet/CesiumForUnity/CesiumUintMat4x4.h>
#include <DotNet/CesiumForUnity/CesiumUintVec2.h>
#include <DotNet/CesiumForUnity/CesiumUintVec3.h>
#include <DotNet/CesiumForUnity/CesiumUintVec4.h>
#include <DotNet/CesiumForUnity/CesiumUrlTemplateRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumWebMapServiceRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumWebMapTileServiceRasterOverlay.h>
#include <DotNet/CesiumForUnity/HeaderEntry.h>
#include <DotNet/CesiumForUnity/Helpers.h>
#include <DotNet/CesiumForUnity/IonAssetDetails.h>
#include <DotNet/CesiumForUnity/IonAssetsTreeView.h>
#include <DotNet/CesiumForUnity/IonMissingAssetWindow.h>
#include <DotNet/CesiumForUnity/IonTokenTroubleshootingWindow.h>
#include <DotNet/CesiumForUnity/NativeCoroutine.h>
#include <DotNet/CesiumForUnity/NativeDownloadHandler.h>
#include <DotNet/CesiumForUnity/QuickAddItem.h>
#include <DotNet/CesiumForUnity/SelectIonTokenWindow.h>
#include <DotNet/CesiumForUnity/TestGltfModel.h>
#include <DotNet/CesiumForUnity/TestReinterop.h>
#include <DotNet/CesiumForUnity/TokenTroubleshootingDetails.h>
#include <DotNet/Reinterop/ObjectHandleUtility.h>
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/System/Action.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/UnityEngine/AsyncOperation.h>
#include <DotNet/System/Action1.h>
#include <DotNet/System/Array.h>
#include <DotNet/System/Array1.h>
#include <DotNet/System/String.h>
#include <DotNet/Unity/Mathematics/double3.h>
#include <DotNet/Unity/Mathematics/float2.h>
#include <DotNet/Unity/Mathematics/float2x2.h>
#include <DotNet/Unity/Mathematics/float3.h>
#include <DotNet/Unity/Mathematics/float3x3.h>
#include <DotNet/Unity/Mathematics/float4.h>
#include <DotNet/Unity/Mathematics/float4x4.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/UnityEngine/Rendering/VertexAttributeDescriptor.h>
#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/System/Collections/Generic/Dictionary2.h>
#include <DotNet/System/Collections/Generic/Enumerator0.h>
#include <DotNet/System/Collections/Generic/KeyValuePair2.h>
#include <DotNet/System/Collections/Generic/List1.h>
#include <DotNet/CesiumForUnity/GoogleMapTilesLayerType.h>
#include <DotNet/Unity/Mathematics/double2.h>
#include <DotNet/UnityEngine/Camera.h>
#include <DotNet/UnityEngine/Texture2D.h>
#include <DotNet/System/Delegate.h>
#include <DotNet/System/Environment.h>
#include <DotNet/System/Exception.h>
#include <DotNet/System/Object.h>
#include <DotNet/System/Func2.h>
#include <DotNet/System/MulticastDelegate.h>
#include <DotNet/System/OperatingSystem.h>
#include <DotNet/System/Runtime/InteropServices/Marshal.h>
#include <DotNet/System/Text/Encoding.h>
#include <DotNet/System/Threading/Tasks/Task.h>
#include <DotNet/System/Threading/Tasks/TaskCompletionSource1.h>
#include <DotNet/Unity/Collections/LowLevel/Unsafe/NativeArrayUnsafeUtility.h>
#include <DotNet/UnityEngine/Vector2.h>
#include <DotNet/Unity/Collections/NativeArray1.h>
#include <DotNet/Unity/Mathematics/double2x2.h>
#include <DotNet/Unity/Mathematics/double3x3.h>
#include <DotNet/Unity/Mathematics/double4.h>
#include <DotNet/Unity/Mathematics/double4x4.h>
#include <DotNet/Unity/Mathematics/int2.h>
#include <DotNet/Unity/Mathematics/int2x2.h>
#include <DotNet/Unity/Mathematics/int3.h>
#include <DotNet/Unity/Mathematics/int3x3.h>
#include <DotNet/Unity/Mathematics/int4.h>
#include <DotNet/Unity/Mathematics/int4x4.h>
#include <DotNet/Unity/Mathematics/uint2.h>
#include <DotNet/Unity/Mathematics/uint2x2.h>
#include <DotNet/Unity/Mathematics/uint3.h>
#include <DotNet/Unity/Mathematics/uint3x3.h>
#include <DotNet/Unity/Mathematics/uint4.h>
#include <DotNet/Unity/Mathematics/uint4x4.h>
#include <DotNet/UnityEditor/AssemblyReloadCallback.h>
#include <DotNet/UnityEditor/AssemblyReloadEvents.h>
#include <DotNet/UnityEditor/CallbackFunction.h>
#include <DotNet/UnityEditor/EditorApplication.h>
#include <DotNet/UnityEditor/EditorPrefs.h>
#include <DotNet/UnityEditor/EditorUtility.h>
#include <DotNet/UnityEditor/EditorWindow.h>
#include <DotNet/UnityEditor/IMGUI/Controls/MultiColumnHeader.h>
#include <DotNet/UnityEditor/IMGUI/Controls/TreeView.h>
#include <DotNet/UnityEditor/IMGUI/Controls/TreeViewItem.h>
#include <DotNet/UnityEditor/IMGUI/Controls/TreeViewState.h>
#include <DotNet/UnityEditor/SceneView.h>
#include <DotNet/UnityEditor/ScriptableSingleton1.h>
#include <DotNet/UnityEditor/Selection.h>
#include <DotNet/UnityEngine/Application.h>
#include <DotNet/UnityEngine/Behaviour.h>
#include <DotNet/UnityEngine/Bounds.h>
#include <DotNet/UnityEngine/Component.h>
#include <DotNet/UnityEngine/Debug.h>
#include <DotNet/UnityEngine/GUI.h>
#include <DotNet/UnityEngine/Material.h>
#include <DotNet/UnityEngine/Matrix4x4.h>
#include <DotNet/UnityEngine/Rendering/MeshUpdateFlags.h>
#include <DotNet/UnityEngine/MeshCollider.h>
#include <DotNet/UnityEngine/MeshData.h>
#include <DotNet/UnityEngine/MeshDataArray.h>
#include <DotNet/UnityEngine/MeshFilter.h>
#include <DotNet/UnityEngine/MeshRenderer.h>
#include <DotNet/UnityEngine/MonoBehaviour.h>
#include <DotNet/UnityEngine/Networking/DownloadHandler.h>
#include <DotNet/UnityEngine/Networking/UnityWebRequest.h>
#include <DotNet/UnityEngine/Networking/UnityWebRequestAsyncOperation.h>
#include <DotNet/UnityEngine/Networking/UnityWebRequestTexture.h>
#include <DotNet/UnityEngine/Networking/UploadHandlerRaw.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/UnityEngine/Physics.h>
#include <DotNet/UnityEngine/Quaternion.h>
#include <DotNet/UnityEngine/RaycastHit.h>
#include <DotNet/UnityEngine/Rect.h>
#include <DotNet/UnityEngine/Renderer.h>
#include <DotNet/UnityEngine/Rendering/SubMeshDescriptor.h>
#include <DotNet/UnityEngine/Resources.h>
#include <DotNet/UnityEngine/SceneManagement/Scene.h>
#include <DotNet/UnityEngine/SceneManagement/SceneManager.h>
#include <DotNet/UnityEngine/Shader.h>
#include <DotNet/UnityEngine/SystemInfo.h>
#include <DotNet/UnityEngine/Texture.h>
#include <DotNet/UnityEngine/Time.h>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/UnityEngine/Vector4.h>

namespace DotNet::Unity::Mathematics {
struct double4x4;
}
namespace DotNet::CesiumForUnity {
struct Cesium3DTilesetLoadFailureDetails;
}
namespace DotNet::UnityEngine {
class GameObject;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System::Collections {
class IEnumerator;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}
namespace DotNet::System {
class String;
}
namespace DotNet::CesiumForUnity {
class CesiumIonServer;
}
namespace DotNet::UnityEngine {
class Material;
}
namespace DotNet::CesiumForUnity {
enum class CesiumDataSource;
}
namespace DotNet::CesiumForUnity {
class Cesium3DTileset;
}
namespace DotNet::CesiumForUnity {
enum class Cesium3DTilesetLoadType;
}
namespace DotNet::CesiumForUnity {
enum class AzureMapsTilesetId;
}
namespace DotNet::CesiumForUnity {
enum class BingMapsStyle;
}
namespace DotNet::UnityEngine {
struct Matrix4x4;
}
namespace DotNet::CesiumForUnity {
class CesiumCreditComponent;
}
namespace DotNet::System::Collections::Generic {
template <typename T0> class List1;
}
namespace DotNet::Unity::Mathematics {
struct double3;
}
namespace DotNet::System {
template <typename T0> class Array1;
}
namespace DotNet::CesiumForUnity {
enum class CesiumFeatureIdAttributeStatus;
}
namespace DotNet::CesiumForUnity {
enum class CesiumFeatureIdTextureStatus;
}
namespace DotNet::System {
class Action;
}
namespace DotNet::CesiumForUnity {
class CesiumEllipsoid;
}
namespace DotNet::CesiumForUnity {
enum class CesiumGeoreferenceOriginAuthority;
}
namespace DotNet::CesiumForUnity {
enum class CesiumGeoreferenceOriginPlacement;
}
namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::UnityEngine {
struct Quaternion;
}
namespace DotNet::CesiumForUnity {
enum class GoogleMapTilesLayerType;
}
namespace DotNet::CesiumForUnity {
enum class GoogleMapTilesMapType;
}
namespace DotNet::CesiumForUnity {
enum class GoogleMapTilesScale;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntVec2;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntMat2x2;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntVec3;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntMat3x3;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntVec4;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntMat4x4;
}
namespace DotNet::UnityEngine {
class Transform;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::Unity::Mathematics {
struct double2;
}
namespace DotNet::Unity::Mathematics {
struct float3x3;
}
namespace DotNet::Unity::Mathematics {
struct double3x3;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintVec2;
}
namespace DotNet::Unity::Mathematics {
struct float3;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintVec3;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintVec4;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat2x2;
}
namespace DotNet::Unity::Mathematics {
struct double4;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat4x4;
}
namespace DotNet::Unity::Mathematics {
struct float2x2;
}
namespace DotNet::Unity::Mathematics {
struct float2;
}
namespace DotNet::Unity::Mathematics {
struct double2x2;
}
namespace DotNet::Unity::Mathematics {
struct float4;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat3x3;
}
namespace DotNet::CesiumForUnity {
class CesiumPropertyArray;
}
namespace DotNet::Unity::Mathematics {
struct float4x4;
}
namespace DotNet::CesiumForUnity {
struct CesiumMetadataValueType;
}
namespace DotNet::CesiumForUnity {
enum class CesiumMetadataType;
}
namespace DotNet::CesiumForUnity {
enum class CesiumMetadataComponentType;
}
namespace DotNet::CesiumForUnity {
class CesiumPropertyTable;
}
namespace DotNet::UnityEngine {
class Mesh;
}
namespace DotNet::CesiumForUnity {
struct Cesium3DTileInfo;
}
namespace DotNet::CesiumForUnity {
class CesiumCartographicPolygon;
}
namespace DotNet::CesiumForUnity {
class CesiumFeatureIdSet;
}
namespace DotNet::CesiumForUnity {
class CesiumMetadataValue;
}
namespace DotNet::CesiumForUnity {
class CesiumPropertyTableProperty;
}
namespace DotNet::System::Collections::Generic {
template <typename T0, typename T1> class Dictionary2;
}
namespace DotNet::CesiumForUnity {
enum class CesiumPropertyTableStatus;
}
namespace DotNet::CesiumForUnity {
enum class CesiumPropertyTablePropertyStatus;
}
namespace DotNet::CesiumForUnity {
struct CesiumRasterOverlayLoadFailureDetails;
}
namespace DotNet::CesiumForUnity {
class CesiumRasterOverlay;
}
namespace DotNet::CesiumForUnity {
enum class CesiumRasterOverlayLoadType;
}
namespace DotNet::CesiumForUnity {
class Cesium3DTile;
}
namespace DotNet::CesiumForUnity {
enum class CesiumUrlTemplateRasterOverlayProjection;
}
namespace DotNet::CesiumForUnity {
class HeaderEntry;
}
namespace DotNet::CesiumForUnity {
enum class CesiumWebMapTileServiceRasterOverlayProjection;
}
namespace DotNet::UnityEngine {
enum class RuntimePlatform;
}
namespace DotNet::UnityEditor::IMGUI::Controls {
class TreeViewState;
}
namespace DotNet::UnityEditor::IMGUI::Controls {
class MultiColumnHeader;
}
namespace DotNet::CesiumForUnity {
class CesiumIonAsset;
}
namespace DotNet::System {
template <typename T0, typename T1> class Func2;
}
namespace DotNet::CesiumForUnity {
enum class QuickAddItemType;
}
namespace DotNet::CesiumForUnity {
enum class IonTokenSource;
}
namespace DotNet::System {
class MulticastDelegate;
}
namespace DotNet::System {
class Delegate;
}
namespace DotNet::UnityEngine {
class AsyncOperation;
}
namespace DotNet::CesiumForUnity {
class CesiumCredit;
}
namespace DotNet::CesiumForUnity {
class QuickAddItem;
}
namespace DotNet::System {
enum class StringComparison;
}
namespace DotNet::System {
class Exception;
}
namespace DotNet::CesiumForUnity {
class CesiumSampleHeightResult;
}
namespace DotNet::Unity::Collections {
template <typename T0> struct NativeArray1;
}
namespace DotNet::UnityEngine {
struct Vector2;
}
namespace DotNet::Unity::Collections {
enum class Allocator;
}
namespace DotNet::Unity::Collections {
enum class NativeArrayOptions;
}
namespace DotNet::Unity::Mathematics {
struct int2;
}
namespace DotNet::Unity::Mathematics {
struct int2x2;
}
namespace DotNet::Unity::Mathematics {
struct int3;
}
namespace DotNet::Unity::Mathematics {
struct int3x3;
}
namespace DotNet::Unity::Mathematics {
struct int4;
}
namespace DotNet::Unity::Mathematics {
struct int4x4;
}
namespace DotNet::Unity::Mathematics {
struct uint2;
}
namespace DotNet::Unity::Mathematics {
struct uint2x2;
}
namespace DotNet::Unity::Mathematics {
struct uint3;
}
namespace DotNet::Unity::Mathematics {
struct uint3x3;
}
namespace DotNet::Unity::Mathematics {
struct uint4;
}
namespace DotNet::Unity::Mathematics {
struct uint4x4;
}
namespace DotNet::UnityEditor {
class AssemblyReloadCallback;
}
namespace DotNet::System {
template <typename T0> class Action1;
}
namespace DotNet::UnityEngine {
struct Bounds;
}
namespace DotNet::UnityEngine {
enum class StereoscopicEye;
}
namespace DotNet::UnityEngine {
struct Rect;
}
namespace DotNet::UnityEngine {
class Texture;
}
namespace DotNet::UnityEngine {
struct Vector4;
}
namespace DotNet::UnityEngine {
class Shader;
}
namespace DotNet::UnityEngine {
struct MeshDataArray;
}
namespace DotNet::UnityEngine::Rendering {
enum class MeshUpdateFlags : uint32_t;
}
namespace DotNet::UnityEngine {
enum class MeshTopology;
}
namespace DotNet::UnityEngine::Rendering {
enum class IndexFormat;
}
namespace DotNet::UnityEngine::Rendering {
struct SubMeshDescriptor;
}
namespace DotNet::UnityEngine::Rendering {
struct VertexAttributeDescriptor;
}
namespace DotNet::UnityEngine::Networking {
class DownloadHandler;
}
namespace DotNet::UnityEngine::Networking {
class UploadHandler;
}
namespace DotNet::UnityEngine {
struct RaycastHit;
}
namespace DotNet::UnityEngine::Experimental::Rendering {
enum class GraphicsFormat;
}
namespace DotNet::UnityEngine::Experimental::Rendering {
enum class FormatUsage;
}
namespace DotNet::UnityEngine {
enum class FilterMode;
}
namespace DotNet::UnityEngine {
enum class TextureWrapMode;
}
namespace DotNet::UnityEngine {
enum class TextureFormat;
}

void start();

void stop();

extern "C" {
#if defined(_WIN32)
__declspec(dllexport)
#endif
std::uint8_t initializeReinterop(std::uint64_t validationHashValue, void** functionPointers, std::int32_t count) {
  // Make sure the C++ and C# layers are in sync.
  if (count != 1898)
    return 0;
  if (validationHashValue != 9824312933344955837ULL)
    return 0;

  ::DotNet::CesiumForUnity::AssetTroubleshootingDetails::Property_get_assetExistsInUserAccount = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[0]);
  ::DotNet::CesiumForUnity::AssetTroubleshootingDetails::Property_get_loaded = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1]);
  ::DotNet::CesiumForUnity::AssetTroubleshootingDetails::Property_set_assetExistsInUserAccount = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[2]);
  ::DotNet::CesiumForUnity::AssetTroubleshootingDetails::Property_set_loaded = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[3]);
  ::DotNet::CesiumForUnity::Cesium3DTile::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[4]);
  ::DotNet::CesiumForUnity::Cesium3DTile::Field_get__pTile = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[5]);
  ::DotNet::CesiumForUnity::Cesium3DTile::Field_get__pTileEllipsoid = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[6]);
  ::DotNet::CesiumForUnity::Cesium3DTile::Field_get__transform = reinterpret_cast<void (*)(void* thiz, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException)>(functionPointers[7]);
  ::DotNet::CesiumForUnity::Cesium3DTile::Field_set__pTile = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[8]);
  ::DotNet::CesiumForUnity::Cesium3DTile::Field_set__pTileEllipsoid = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[9]);
  ::DotNet::CesiumForUnity::Cesium3DTile::Field_set__transform = reinterpret_cast<void (*)(void* thiz, const ::DotNet::Unity::Mathematics::double4x4* value, void** reinteropException)>(functionPointers[10]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::CallBroadcastCesium3DTilesetLoadFailure_EA9gid9gf99C0Ye5ZgnZYw = reinterpret_cast<void (*)(void*, void**)>(functionPointers[11]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::CallBroadcastNewGameObjectCreated_PB2O3_b6vvn_5vRyfrXK8g = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[12]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[13]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[14]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[15]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[16]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::CallRecreateTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[17]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[18]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[19]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_createPhysicsMeshes = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[20]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_culledScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[21]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[22]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_enableFogCulling = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[23]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_enableFrustumCulling = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[24]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_enforceCulledScreenSpaceError = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[25]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_forbidHoles = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[26]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[27]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_generateSmoothNormals = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[28]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[29]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_ignoreKhrMaterialsUnlit = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[30]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_ionAccessToken = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[31]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_ionAssetID = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[32]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_ionServer = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[33]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_loadingDescendantLimit = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[34]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_logSelectionStats = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[35]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_maximumCachedBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[36]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[37]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[38]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[39]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[40]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_opaqueMaterial = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[41]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_preloadAncestors = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[42]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_preloadSiblings = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[43]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_previousSuspendUpdate = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[44]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[45]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_showTilesInHierarchy = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[46]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_suspendUpdate = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[47]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_tilesetSource = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[48]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[49]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_updateInEditor = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[50]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_get_url = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[51]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_createPhysicsMeshes = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[52]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_culledScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[53]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[54]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_enableFogCulling = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[55]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_enableFrustumCulling = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[56]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_enforceCulledScreenSpaceError = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[57]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_forbidHoles = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[58]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_generateSmoothNormals = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[59]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[60]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_ignoreKhrMaterialsUnlit = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[61]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_ionAccessToken = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[62]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_ionAssetID = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[63]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_ionServer = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[64]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_loadingDescendantLimit = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[65]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_logSelectionStats = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[66]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_maximumCachedBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[67]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[68]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[69]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[70]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_opaqueMaterial = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[71]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_preloadAncestors = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[72]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_preloadSiblings = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[73]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_previousSuspendUpdate = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[74]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[75]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_showTilesInHierarchy = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[76]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_suspendUpdate = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[77]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_tilesetSource = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[78]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_updateInEditor = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[79]);
  ::DotNet::CesiumForUnity::Cesium3DTileset::Property_set_url = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[80]);
  ::DotNet::CesiumForUnity::Cesium3DTilesetLoadFailureDetails::Construct_lQ2_FlEU3TadAE4hjbl4Mw = reinterpret_cast<void* (*)(void*, ::std::uint32_t, ::std::int64_t, void*, void**)>(functionPointers[81]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[82]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[83]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[84]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[85]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[86]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[87]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[88]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[89]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_apiVersion = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[90]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[91]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[92]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[93]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_key = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[94]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_language = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[95]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_materialKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[96]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[97]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[98]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_maximumTextureSize = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[99]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[100]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[101]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[102]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_subTileCacheBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[103]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_tilesetId = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[104]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[105]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_get_view = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[106]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_apiVersion = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[107]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[108]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[109]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_key = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[110]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_language = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[111]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_materialKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[112]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[113]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[114]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_maximumTextureSize = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[115]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[116]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[117]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_subTileCacheBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[118]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_tilesetId = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[119]);
  ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay::Property_set_view = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[120]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[121]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[122]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[123]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[124]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[125]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[126]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[127]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[128]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_bingMapsKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[129]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[130]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[131]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[132]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_mapStyle = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[133]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_materialKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[134]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[135]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[136]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_maximumTextureSize = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[137]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[138]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[139]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[140]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_subTileCacheBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[141]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[142]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_set_bingMapsKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[143]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[144]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[145]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_set_mapStyle = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[146]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_set_materialKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[147]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[148]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[149]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_set_maximumTextureSize = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[150]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[151]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[152]);
  ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay::Property_set_subTileCacheBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[153]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[154]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[155]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::CallGetOrCreate__t6GMXW_JRJi50mec2n__dA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[156]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[157]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[158]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[159]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_get_additionalCameras = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[160]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[161]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[162]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[163]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[164]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[165]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_get_useMainCamera = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[166]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_get_useSceneViewCameraInEditor = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[167]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[168]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[169]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[170]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_set_useMainCamera = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[171]);
  ::DotNet::CesiumForUnity::CesiumCameraManager::Property_set_useSceneViewCameraInEditor = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[172]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::CallGetCartographicPoints_3PzhCLUvxkK__aqlAOgTXoA = reinterpret_cast<void* (*)(void*, const ::DotNet::UnityEngine::Matrix4x4*, void**)>(functionPointers[173]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[174]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[175]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[176]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[177]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[178]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[179]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[180]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[181]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[182]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[183]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[184]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[185]);
  ::DotNet::CesiumForUnity::CesiumCartographicPolygon::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[186]);
  ::DotNet::CesiumForUnity::CesiumCredit::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[187]);
  ::DotNet::CesiumForUnity::CesiumCredit::Construct_qXRB_eg5WNz__5KHXUesADw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[188]);
  ::DotNet::CesiumForUnity::CesiumCredit::Property_get_components = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[189]);
  ::DotNet::CesiumForUnity::CesiumCreditComponent::Construct_hnJK39H7_p9CsaJF5ySJ5Q = reinterpret_cast<void* (*)(void*, void*, ::std::int32_t, void**)>(functionPointers[190]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::CallBroadcastCreditsUpdate_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[191]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[192]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::CallGetDefaultCreditSystem_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[193]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[194]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::CallGetNumberOfLoadingImages_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[195]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::CallLoadImage_i4__FgVIR5VYHO4KBzPBwNQ = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[196]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[197]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[198]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[199]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[200]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[201]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[202]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_images = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[203]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[204]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[205]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_onScreenCredits = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[206]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_popupCredits = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[207]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[208]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[209]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[210]);
  ::DotNet::CesiumForUnity::CesiumCreditSystem::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[211]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[212]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[213]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[214]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[215]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[216]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[217]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[218]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[219]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[220]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[221]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[222]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_materialKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[223]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[224]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[225]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_maximumTextureSize = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[226]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[227]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[228]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[229]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_subTileCacheBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[230]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[231]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[232]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[233]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_set_materialKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[234]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[235]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[236]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_set_maximumTextureSize = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[237]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[238]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[239]);
  ::DotNet::CesiumForUnity::CesiumDebugColorizeTilesRasterOverlay::Property_set_subTileCacheBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[240]);
  ::DotNet::CesiumForUnity::CesiumEditorUtility::CallAddBaseOverlayToTileset_GE91HI1OIybUlB1E__yYJCQ = reinterpret_cast<void* (*)(void*, ::std::int64_t, void**)>(functionPointers[241]);
  ::DotNet::CesiumForUnity::CesiumEditorUtility::CallCreateTileset_jsvXjE1xIXP0dz0Yem4Nag = reinterpret_cast<void* (*)(void*, ::std::int64_t, void**)>(functionPointers[242]);
  ::DotNet::CesiumForUnity::CesiumEditorUtility::CallFindFirstTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[243]);
  ::DotNet::CesiumForUnity::CesiumEditorUtility::CallFindFirstTilesetWithAssetID_OUsZiF60__hSy6sWtVPSwsA = reinterpret_cast<void* (*)(::std::int64_t, void**)>(functionPointers[244]);
  ::DotNet::CesiumForUnity::CesiumEditorWindow::CallClose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[245]);
  ::DotNet::CesiumForUnity::CesiumEditorWindow::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[246]);
  ::DotNet::CesiumForUnity::CesiumEditorWindow::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[247]);
  ::DotNet::CesiumForUnity::CesiumEditorWindow::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[248]);
  ::DotNet::CesiumForUnity::CesiumEditorWindow::Field_get_currentWindow = reinterpret_cast<void* (*)(void** reinteropException)>(functionPointers[249]);
  ::DotNet::CesiumForUnity::CesiumEditorWindow::Field_set_currentWindow = reinterpret_cast<void (*)(void* value, void** reinteropException)>(functionPointers[250]);
  ::DotNet::CesiumForUnity::CesiumEditorWindow::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[251]);
  ::DotNet::CesiumForUnity::CesiumEditorWindow::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[252]);
  ::DotNet::CesiumForUnity::CesiumEditorWindow::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[253]);
  ::DotNet::CesiumForUnity::CesiumEditorWindow::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[254]);
  ::DotNet::CesiumForUnity::CesiumEditorWindow::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[255]);
  ::DotNet::CesiumForUnity::CesiumEllipsoid::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[256]);
  ::DotNet::CesiumForUnity::CesiumEllipsoid::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[257]);
  ::DotNet::CesiumForUnity::CesiumEllipsoid::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[258]);
  ::DotNet::CesiumForUnity::CesiumEllipsoid::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[259]);
  ::DotNet::CesiumForUnity::CesiumEllipsoid::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[260]);
  ::DotNet::CesiumForUnity::CesiumEllipsoid::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[261]);
  ::DotNet::CesiumForUnity::CesiumEllipsoid::Property_get_radii = reinterpret_cast<void (*)(void*, ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[262]);
  ::DotNet::CesiumForUnity::CesiumEllipsoid::Property_get_WGS84 = reinterpret_cast<void* (*)(void**)>(functionPointers[263]);
  ::DotNet::CesiumForUnity::CesiumEllipsoid::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[264]);
  ::DotNet::CesiumForUnity::CesiumEllipsoid::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[265]);
  ::DotNet::CesiumForUnity::CesiumEllipsoid::Property_set_radii = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[266]);
  ::DotNet::CesiumForUnity::CesiumFeature::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[267]);
  ::DotNet::CesiumForUnity::CesiumFeature::Property_get_className = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[268]);
  ::DotNet::CesiumForUnity::CesiumFeature::Property_get_featureTableName = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[269]);
  ::DotNet::CesiumForUnity::CesiumFeature::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[270]);
  ::DotNet::CesiumForUnity::CesiumFeature::Property_get_properties = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[271]);
  ::DotNet::CesiumForUnity::CesiumFeature::Property_set_className = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[272]);
  ::DotNet::CesiumForUnity::CesiumFeature::Property_set_featureTableName = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[273]);
  ::DotNet::CesiumForUnity::CesiumFeature::Property_set_properties = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[274]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[275]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[276]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Property_get_featureCount = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[277]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Property_get_label = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[278]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[279]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Property_get_nullFeatureId = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[280]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Property_get_propertyTableIndex = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[281]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Property_get_status = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[282]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Property_set_featureCount = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[283]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Property_set_label = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[284]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Property_set_nullFeatureId = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[285]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Property_set_propertyTableIndex = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[286]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdAttribute::Property_set_status = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[287]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdSet::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[288]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdSet::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[289]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdSet::Construct_AdNLRR1TzhjQ9htOxA80Nw = reinterpret_cast<void* (*)(::std::int64_t, void**)>(functionPointers[290]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_get_featureCount = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[291]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_get_label = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[292]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_get_nullFeatureId = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[293]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_get_propertyTableIndex = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[294]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_set_featureCount = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[295]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_set_label = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[296]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_set_nullFeatureId = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[297]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdSet::Property_set_propertyTableIndex = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[298]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[299]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[300]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_get_featureCount = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[301]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_get_label = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[302]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[303]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_get_nullFeatureId = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[304]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_get_propertyTableIndex = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[305]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_get_status = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[306]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_set_featureCount = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[307]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_set_label = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[308]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_set_nullFeatureId = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[309]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_set_propertyTableIndex = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[310]);
  ::DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_set_status = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[311]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Calladd_changed_lHaT5LN6vSYwmLLE2__7bOw = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[312]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[313]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[314]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::CallMoveOrigin_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[315]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[316]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[317]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Callremove_changed_lHaT5LN6vSYwmLLE2__7bOw = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[318]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[319]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_ecefToLocalMatrix = reinterpret_cast<void (*)(void*, ::DotNet::Unity::Mathematics::double4x4*, void**)>(functionPointers[320]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_ecefX = reinterpret_cast<double (*)(void*, void**)>(functionPointers[321]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_ecefY = reinterpret_cast<double (*)(void*, void**)>(functionPointers[322]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_ecefZ = reinterpret_cast<double (*)(void*, void**)>(functionPointers[323]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_ellipsoid = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[324]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[325]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[326]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_height = reinterpret_cast<double (*)(void*, void**)>(functionPointers[327]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[328]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_latitude = reinterpret_cast<double (*)(void*, void**)>(functionPointers[329]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_longitude = reinterpret_cast<double (*)(void*, void**)>(functionPointers[330]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[331]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[332]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_originAuthority = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[333]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_originPlacement = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[334]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_scale = reinterpret_cast<double (*)(void*, void**)>(functionPointers[335]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[336]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_ecefX = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[337]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_ecefY = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[338]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_ecefZ = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[339]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_ellipsoid = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[340]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[341]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_height = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[342]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[343]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_latitude = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[344]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_longitude = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[345]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[346]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_originAuthority = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[347]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_originPlacement = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[348]);
  ::DotNet::CesiumForUnity::CesiumGeoreference::Property_set_scale = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[349]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[350]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[351]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[352]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[353]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[354]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::CallUpdateGeoreferenceIfNecessary_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[355]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__georeference = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[356]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__lastEllipsoidRadii = reinterpret_cast<::std::uint8_t (*)(void* thiz, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException)>(functionPointers[357]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__lastLocalPosition = reinterpret_cast<void (*)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException)>(functionPointers[358]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__lastLocalRotation = reinterpret_cast<void (*)(void* thiz, ::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException)>(functionPointers[359]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__lastLocalsAreValid = reinterpret_cast<::std::uint8_t (*)(void* thiz, void** reinteropException)>(functionPointers[360]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__lastLocalScale = reinterpret_cast<void (*)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException)>(functionPointers[361]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__localToGlobeFixedMatrix = reinterpret_cast<void (*)(void* thiz, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException)>(functionPointers[362]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__localToGlobeFixedMatrixIsValid = reinterpret_cast<::std::uint8_t (*)(void* thiz, void** reinteropException)>(functionPointers[363]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__georeference = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[364]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__lastEllipsoidRadii = reinterpret_cast<void (*)(void* thiz, const ::DotNet::Unity::Mathematics::double3* value, void** reinteropException)>(functionPointers[365]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__lastLocalPosition = reinterpret_cast<void (*)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException)>(functionPointers[366]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__lastLocalRotation = reinterpret_cast<void (*)(void* thiz, const ::DotNet::UnityEngine::Quaternion* value, void** reinteropException)>(functionPointers[367]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__lastLocalsAreValid = reinterpret_cast<void (*)(void* thiz, ::std::uint8_t value, void** reinteropException)>(functionPointers[368]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__lastLocalScale = reinterpret_cast<void (*)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException)>(functionPointers[369]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__localToGlobeFixedMatrix = reinterpret_cast<void (*)(void* thiz, const ::DotNet::Unity::Mathematics::double4x4* value, void** reinteropException)>(functionPointers[370]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__localToGlobeFixedMatrixIsValid = reinterpret_cast<void (*)(void* thiz, ::std::uint8_t value, void** reinteropException)>(functionPointers[371]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_adjustOrientationForGlobeWhenMoving = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[372]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_detectTransformChanges = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[373]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[374]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[375]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[376]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_localToGlobeFixedMatrix = reinterpret_cast<void (*)(void*, ::DotNet::Unity::Mathematics::double4x4*, void**)>(functionPointers[377]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_longitudeLatitudeHeight = reinterpret_cast<void (*)(void*, ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[378]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[379]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_positionGlobeFixed = reinterpret_cast<void (*)(void*, ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[380]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[381]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_adjustOrientationForGlobeWhenMoving = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[382]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_detectTransformChanges = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[383]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[384]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[385]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_localToGlobeFixedMatrix = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::double4x4*, void**)>(functionPointers[386]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_longitudeLatitudeHeight = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[387]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[388]);
  ::DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_positionGlobeFixed = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[389]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[390]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[391]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[392]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[393]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[394]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[395]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[396]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[397]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_apiKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[398]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[399]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[400]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[401]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_highDpi = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[402]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_language = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[403]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_layerTypes = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[404]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_mapType = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[405]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_materialKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[406]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[407]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[408]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_maximumTextureSize = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[409]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[410]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[411]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_overlay = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[412]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_region = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[413]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_scale = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[414]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[415]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_styles = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[416]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_subTileCacheBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[417]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[418]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_apiKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[419]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[420]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[421]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_highDpi = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[422]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_language = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[423]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_layerTypes = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[424]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_mapType = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[425]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_materialKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[426]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[427]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[428]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_maximumTextureSize = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[429]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[430]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_overlay = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[431]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_region = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[432]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_scale = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[433]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[434]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_styles = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[435]);
  ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_subTileCacheBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[436]);
  ::DotNet::CesiumForUnity::CesiumIntMat2x2::Construct_FoRlw9gqeGSV1ZBPJBNk9g = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumIntVec2*, const ::DotNet::CesiumForUnity::CesiumIntVec2*, ::DotNet::CesiumForUnity::CesiumIntMat2x2*, void**)>(functionPointers[437]);
  ::DotNet::CesiumForUnity::CesiumIntMat2x2::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumIntMat2x2*, ::std::int32_t, ::DotNet::CesiumForUnity::CesiumIntVec2*, void**)>(functionPointers[438]);
  ::DotNet::CesiumForUnity::CesiumIntMat3x3::Construct_tv5P8Gb7SQuNjwU2Vh0zRw = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumIntVec3*, const ::DotNet::CesiumForUnity::CesiumIntVec3*, const ::DotNet::CesiumForUnity::CesiumIntVec3*, ::DotNet::CesiumForUnity::CesiumIntMat3x3*, void**)>(functionPointers[439]);
  ::DotNet::CesiumForUnity::CesiumIntMat3x3::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumIntMat3x3*, ::std::int32_t, ::DotNet::CesiumForUnity::CesiumIntVec3*, void**)>(functionPointers[440]);
  ::DotNet::CesiumForUnity::CesiumIntMat4x4::Construct_1oaleqFQUQx5j2RbOSvw3w = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumIntVec4*, const ::DotNet::CesiumForUnity::CesiumIntVec4*, const ::DotNet::CesiumForUnity::CesiumIntVec4*, const ::DotNet::CesiumForUnity::CesiumIntVec4*, ::DotNet::CesiumForUnity::CesiumIntMat4x4*, void**)>(functionPointers[441]);
  ::DotNet::CesiumForUnity::CesiumIntMat4x4::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumIntMat4x4*, ::std::int32_t, ::DotNet::CesiumForUnity::CesiumIntVec4*, void**)>(functionPointers[442]);
  ::DotNet::CesiumForUnity::CesiumIntVec2::Construct_CSSfw_WOk6__K5__v8pO4eLw = reinterpret_cast<void (*)(::std::int32_t, ::std::int32_t, ::DotNet::CesiumForUnity::CesiumIntVec2*, void**)>(functionPointers[443]);
  ::DotNet::CesiumForUnity::CesiumIntVec2::Construct_dZv0kAenH9__iFQ8xBVdqfQ = reinterpret_cast<void (*)(::std::int16_t, ::std::int16_t, ::DotNet::CesiumForUnity::CesiumIntVec2*, void**)>(functionPointers[444]);
  ::DotNet::CesiumForUnity::CesiumIntVec2::Construct_iC__gCkOnQfbe6NMbdvLiGg = reinterpret_cast<void (*)(::std::int8_t, ::std::int8_t, ::DotNet::CesiumForUnity::CesiumIntVec2*, void**)>(functionPointers[445]);
  ::DotNet::CesiumForUnity::CesiumIntVec2::Construct_tS0EQwQ6_Z2EVvmR2x05Hg = reinterpret_cast<void (*)(::std::int64_t, ::std::int64_t, ::DotNet::CesiumForUnity::CesiumIntVec2*, void**)>(functionPointers[446]);
  ::DotNet::CesiumForUnity::CesiumIntVec2::Property_get_Item = reinterpret_cast<::std::int64_t (*)(const ::DotNet::CesiumForUnity::CesiumIntVec2*, ::std::int32_t, void**)>(functionPointers[447]);
  ::DotNet::CesiumForUnity::CesiumIntVec3::Construct_2lzDmp63Mfw__oFMy0HdgWw = reinterpret_cast<void (*)(::std::int32_t, ::std::int32_t, ::std::int32_t, ::DotNet::CesiumForUnity::CesiumIntVec3*, void**)>(functionPointers[448]);
  ::DotNet::CesiumForUnity::CesiumIntVec3::Construct_8bShh4o97BtgzpoxMAXY5g = reinterpret_cast<void (*)(::std::int64_t, ::std::int64_t, ::std::int64_t, ::DotNet::CesiumForUnity::CesiumIntVec3*, void**)>(functionPointers[449]);
  ::DotNet::CesiumForUnity::CesiumIntVec3::Construct_cAgWTHR8SgDZQ7UniQULbg = reinterpret_cast<void (*)(::std::int16_t, ::std::int16_t, ::std::int16_t, ::DotNet::CesiumForUnity::CesiumIntVec3*, void**)>(functionPointers[450]);
  ::DotNet::CesiumForUnity::CesiumIntVec3::Construct_luE9S3oIPaPU1lLegMPAPA = reinterpret_cast<void (*)(::std::int8_t, ::std::int8_t, ::std::int8_t, ::DotNet::CesiumForUnity::CesiumIntVec3*, void**)>(functionPointers[451]);
  ::DotNet::CesiumForUnity::CesiumIntVec3::Property_get_Item = reinterpret_cast<::std::int64_t (*)(const ::DotNet::CesiumForUnity::CesiumIntVec3*, ::std::int32_t, void**)>(functionPointers[452]);
  ::DotNet::CesiumForUnity::CesiumIntVec4::Construct__tGDX2UJ5ZtAXl4__zRN6Rg = reinterpret_cast<void (*)(::std::int8_t, ::std::int8_t, ::std::int8_t, ::std::int8_t, ::DotNet::CesiumForUnity::CesiumIntVec4*, void**)>(functionPointers[453]);
  ::DotNet::CesiumForUnity::CesiumIntVec4::Construct_ima1GH0lko9R2DnR_aRPyw = reinterpret_cast<void (*)(::std::int32_t, ::std::int32_t, ::std::int32_t, ::std::int32_t, ::DotNet::CesiumForUnity::CesiumIntVec4*, void**)>(functionPointers[454]);
  ::DotNet::CesiumForUnity::CesiumIntVec4::Construct_KoW6Dv__2RVyEhBpX4dwRww = reinterpret_cast<void (*)(::std::int64_t, ::std::int64_t, ::std::int64_t, ::std::int64_t, ::DotNet::CesiumForUnity::CesiumIntVec4*, void**)>(functionPointers[455]);
  ::DotNet::CesiumForUnity::CesiumIntVec4::Construct_yhJRKUizUTWOe_SY6NdeKQ = reinterpret_cast<void (*)(::std::int16_t, ::std::int16_t, ::std::int16_t, ::std::int16_t, ::DotNet::CesiumForUnity::CesiumIntVec4*, void**)>(functionPointers[456]);
  ::DotNet::CesiumForUnity::CesiumIntVec4::Property_get_Item = reinterpret_cast<::std::int64_t (*)(const ::DotNet::CesiumForUnity::CesiumIntVec4*, ::std::int32_t, void**)>(functionPointers[457]);
  ::DotNet::CesiumForUnity::CesiumIonAsset::CallIsNull_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[458]);
  ::DotNet::CesiumForUnity::CesiumIonAsset::Property_get_componentType = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[459]);
  ::DotNet::CesiumForUnity::CesiumIonAsset::Property_get_ionAccessToken = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[460]);
  ::DotNet::CesiumForUnity::CesiumIonAsset::Property_get_ionAssetID = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[461]);
  ::DotNet::CesiumForUnity::CesiumIonAsset::Property_get_objectName = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[462]);
  ::DotNet::CesiumForUnity::CesiumIonAsset::Property_get_overlay = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[463]);
  ::DotNet::CesiumForUnity::CesiumIonAsset::Property_get_tileset = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[464]);
  ::DotNet::CesiumForUnity::CesiumIonAsset::Property_get_type = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[465]);
  ::DotNet::CesiumForUnity::CesiumIonAsset::Property_set_ionAccessToken = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[466]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[467]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallAddToTilesetLater_SrfNoP9IJM__ZwyysR9yJTQ = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[468]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[469]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[470]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[471]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[472]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[473]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[474]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[475]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_assetOptions = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[476]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[477]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[478]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[479]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_ionAccessToken = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[480]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_ionAssetID = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[481]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_ionServer = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[482]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_materialKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[483]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[484]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[485]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_maximumTextureSize = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[486]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[487]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[488]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[489]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_subTileCacheBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[490]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[491]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_assetOptions = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[492]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[493]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[494]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_ionAccessToken = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[495]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_ionAssetID = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[496]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_ionServer = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[497]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_materialKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[498]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[499]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[500]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_maximumTextureSize = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[501]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[502]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[503]);
  ::DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_subTileCacheBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[504]);
  ::DotNet::CesiumForUnity::CesiumIonServer::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[505]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[506]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[507]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_get_apiUrl = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[508]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_get_defaultIonAccessToken = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[509]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_get_defaultIonAccessTokenId = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[510]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_get_oauth2ApplicationID = reinterpret_cast<::std::int64_t (*)(void* thiz, void** reinteropException)>(functionPointers[511]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_get_serverUrl = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[512]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_get_serverUrlThatIsLoadingApiUrl = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[513]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_set_apiUrl = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[514]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_set_defaultIonAccessToken = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[515]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_set_defaultIonAccessTokenId = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[516]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_set_oauth2ApplicationID = reinterpret_cast<void (*)(void* thiz, ::std::int64_t value, void** reinteropException)>(functionPointers[517]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_set_serverUrl = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[518]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Field_set_serverUrlThatIsLoadingApiUrl = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[519]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Property_get_defaultServer = reinterpret_cast<void* (*)(void**)>(functionPointers[520]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[521]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[522]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[523]);
  ::DotNet::CesiumForUnity::CesiumIonServer::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[524]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[525]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::CallGetSession_ouKG7YNdV4bUJcBV0W3dBA = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[526]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::CallGetUserAccessToken_ouKG7YNdV4bUJcBV0W3dBA = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[527]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[528]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[529]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::CallSetUserAccessToken_i1OZfOwTwhgNuaqLRy9vZQ = reinterpret_cast<void (*)(void*, void*, void*, void**)>(functionPointers[530]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::Property_get_current = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[531]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::Property_get_currentSession = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[532]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[533]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::Property_get_instance = reinterpret_cast<void* (*)(void**)>(functionPointers[534]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[535]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::Property_set_current = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[536]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[537]);
  ::DotNet::CesiumForUnity::CesiumIonServerManager::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[538]);
  ::DotNet::CesiumForUnity::CesiumIonSession::CallBroadcastAssetsUpdate_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[539]);
  ::DotNet::CesiumForUnity::CesiumIonSession::CallBroadcastConnectionUpdate_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[540]);
  ::DotNet::CesiumForUnity::CesiumIonSession::CallBroadcastDefaultsUpdate_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[541]);
  ::DotNet::CesiumForUnity::CesiumIonSession::CallBroadcastProfileUpdate_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[542]);
  ::DotNet::CesiumForUnity::CesiumIonSession::CallBroadcastTokensUpdate_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[543]);
  ::DotNet::CesiumForUnity::CesiumIonSession::CallGetQuickAddItems_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[544]);
  ::DotNet::CesiumForUnity::CesiumIonSession::CallIsConnected_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[545]);
  ::DotNet::CesiumForUnity::CesiumIonSession::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[546]);
  ::DotNet::CesiumForUnity::CesiumIonSession::Property_get_server = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[547]);
  ::DotNet::CesiumForUnity::CesiumIonSession::Property_set_server = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[548]);
  ::DotNet::CesiumForUnity::CesiumMetadata::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[549]);
  ::DotNet::CesiumForUnity::CesiumMetadata::CallGetFeatures_5FygR9Vikuo7JxfnCBErUQ = reinterpret_cast<void* (*)(void*, void*, ::std::int32_t, void**)>(functionPointers[550]);
  ::DotNet::CesiumForUnity::CesiumMetadata::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[551]);
  ::DotNet::CesiumForUnity::CesiumMetadata::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[552]);
  ::DotNet::CesiumForUnity::CesiumMetadata::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[553]);
  ::DotNet::CesiumForUnity::CesiumMetadata::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[554]);
  ::DotNet::CesiumForUnity::CesiumMetadata::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[555]);
  ::DotNet::CesiumForUnity::CesiumMetadata::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[556]);
  ::DotNet::CesiumForUnity::CesiumMetadata::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[557]);
  ::DotNet::CesiumForUnity::CesiumMetadata::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[558]);
  ::DotNet::CesiumForUnity::CesiumMetadata::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[559]);
  ::DotNet::CesiumForUnity::CesiumMetadata::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[560]);
  ::DotNet::CesiumForUnity::CesiumMetadata::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[561]);
  ::DotNet::CesiumForUnity::CesiumMetadata::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[562]);
  ::DotNet::CesiumForUnity::CesiumMetadata::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[563]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetArray_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[564]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetBoolean_8644xplB2__fgXE67sxDhig = reinterpret_cast<::std::uint8_t (*)(void*, ::std::uint8_t, void**)>(functionPointers[565]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetByte_bGdPWSKS_QzGTQdjd0YUfg = reinterpret_cast<::std::uint8_t (*)(void*, ::std::uint8_t, void**)>(functionPointers[566]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetDouble_N2mzpgM1De7RfBi9SEVd3g = reinterpret_cast<double (*)(void*, double, void**)>(functionPointers[567]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetFloat_vH9G7A1WLTqjf5CZMDNGIg = reinterpret_cast<float (*)(void*, float, void**)>(functionPointers[568]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetInt16_WvwSboUzc5ebxbHqu1PVQQ = reinterpret_cast<::std::int16_t (*)(void*, ::std::int16_t, void**)>(functionPointers[569]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetInt32_998gVIdn2_HYywxhSBOEWQ = reinterpret_cast<::std::int32_t (*)(void*, ::std::int32_t, void**)>(functionPointers[570]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetInt64_QUJbZD3LR0PMPHpOtGaL8A = reinterpret_cast<::std::int64_t (*)(void*, ::std::int64_t, void**)>(functionPointers[571]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsBoolean_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, bool*, void**)>(functionPointers[572]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsByte_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::std::uint8_t*, void**)>(functionPointers[573]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntMat2x2_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumIntMat2x2*, void**)>(functionPointers[574]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntMat3x3_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumIntMat3x3*, void**)>(functionPointers[575]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntMat4x4_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumIntMat4x4*, void**)>(functionPointers[576]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntVec2_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumIntVec2*, void**)>(functionPointers[577]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntVec3_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumIntVec3*, void**)>(functionPointers[578]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntVec4_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumIntVec4*, void**)>(functionPointers[579]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintMat2x2_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumUintMat2x2*, void**)>(functionPointers[580]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintMat3x3_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumUintMat3x3*, void**)>(functionPointers[581]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintMat4x4_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumUintMat4x4*, void**)>(functionPointers[582]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintVec2_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumUintVec2*, void**)>(functionPointers[583]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintVec3_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumUintVec3*, void**)>(functionPointers[584]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintVec4_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::CesiumForUnity::CesiumUintVec4*, void**)>(functionPointers[585]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, double*, void**)>(functionPointers[586]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble2_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::double2*, void**)>(functionPointers[587]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble2x2_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::double2x2*, void**)>(functionPointers[588]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble3_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[589]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble3x3_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::double3x3*, void**)>(functionPointers[590]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble4_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::double4*, void**)>(functionPointers[591]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble4x4_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::double4x4*, void**)>(functionPointers[592]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, float*, void**)>(functionPointers[593]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat2_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::float2*, void**)>(functionPointers[594]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat2x2_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::float2x2*, void**)>(functionPointers[595]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat3_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::float3*, void**)>(functionPointers[596]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat3x3_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::float3x3*, void**)>(functionPointers[597]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat4_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::float4*, void**)>(functionPointers[598]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat4x4_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::DotNet::Unity::Mathematics::float4x4*, void**)>(functionPointers[599]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsInt16_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::std::int16_t*, void**)>(functionPointers[600]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsInt32_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::std::int32_t*, void**)>(functionPointers[601]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsInt64_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::std::int64_t*, void**)>(functionPointers[602]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsSByte_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::std::int8_t*, void**)>(functionPointers[603]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsString_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[604]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsUInt16_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::std::uint16_t*, void**)>(functionPointers[605]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsUInt32_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::std::uint32_t*, void**)>(functionPointers[606]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsUInt64_AtRYgGwV_m_laH7E6OJuzQ = reinterpret_cast<::std::uint8_t (*)(void*, ::std::uint64_t*, void**)>(functionPointers[607]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetSByte_u__Z7K16N77kyh7TEGfcD6w = reinterpret_cast<::std::int8_t (*)(void*, ::std::int8_t, void**)>(functionPointers[608]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetString_lQJ2w4ouvMx3GLqlEgEyGg = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[609]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetUInt16_BrHiKvcj_xRGpq___J3u__uQ = reinterpret_cast<::std::uint16_t (*)(void*, ::std::uint16_t, void**)>(functionPointers[610]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetUInt32_vwiv7sse1kaHlVcmj3cmhA = reinterpret_cast<::std::uint32_t (*)(void*, ::std::uint32_t, void**)>(functionPointers[611]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallGetUInt64_IoU0bf6YAddSM0L1le5WZw = reinterpret_cast<::std::uint64_t (*)(void*, ::std::uint64_t, void**)>(functionPointers[612]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue___hk7qZfa8rr3GOj5LB___2w = reinterpret_cast<void (*)(void*, ::std::int8_t, void**)>(functionPointers[613]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue___WBWu0KVcnlBoRHTz18iQg = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::double2*, void**)>(functionPointers[614]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue__dwRw4SrC5dQwg9WXOVCWA = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::float3x3*, void**)>(functionPointers[615]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_0MPHAdrwN6Tw6ckL78VuSw = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumIntVec3*, void**)>(functionPointers[616]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_1dZuiOwXjOp7XXu7VmYFKg = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[617]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_1WBg__LUjCHSaTnVxWpW9hg = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumIntVec2*, void**)>(functionPointers[618]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_2x5EigY7rzmfbErsKTGuwA = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[619]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_3NklrXK7mSsrFiAUMUIpHw = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::double3x3*, void**)>(functionPointers[620]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_6IVxYw6_3__T__eM__j5WVcGA = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumUintVec2*, void**)>(functionPointers[621]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_9Xqzdq684P0z1H__FquaaBA = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::float3*, void**)>(functionPointers[622]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_AOHrSvkQjQG6kWS8yHSsZg = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[623]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_AZB45d2Wd0Dhi64vRZNcpQ = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumUintVec3*, void**)>(functionPointers[624]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_cbZNG6837P_AD_Fyz7orDg = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::double4x4*, void**)>(functionPointers[625]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_CxH9s__3LeVVRneWxCIMJeQ = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumUintVec4*, void**)>(functionPointers[626]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_dwf4e0_X4__X16sg27oT_HA = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[627]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_FD9BTdwh6Rq_Uqnx3WcYzw = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[628]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_GOjK0KanRT1fe9j2Ayd54A = reinterpret_cast<void (*)(void*, ::std::int16_t, void**)>(functionPointers[629]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_hQOJfT5zVEav_dYgl__2qDA = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[630]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_J5rOnxox49GXbyekWYJkRg = reinterpret_cast<void (*)(void*, ::std::uint16_t, void**)>(functionPointers[631]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_jpn00ft20c7Tvsbl6__LFPg = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumUintMat2x2*, void**)>(functionPointers[632]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_K2SuSn7V3nS18YMZRRK2Lw = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[633]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_KdIbPno6dUQIzkDlllX7cQ = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumIntMat2x2*, void**)>(functionPointers[634]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_LfJM7X33EQGf4jiLbGxqWw = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumIntMat3x3*, void**)>(functionPointers[635]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_lWaGb__IpQLOSjzXG2ChwiQ = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::double4*, void**)>(functionPointers[636]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_OekvF3gFc1nGTHuKfXsZ3g = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[637]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_OHiI21kQ_keDg54_OLHJFA = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumUintMat4x4*, void**)>(functionPointers[638]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_p6Nq4_g8K2hv1dGlLZFq4A = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::float2x2*, void**)>(functionPointers[639]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_qWiVKY8F7ND55zOj2iwazg = reinterpret_cast<void (*)(void*, ::std::uint64_t, void**)>(functionPointers[640]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_rf6L9ndiTJQiNeSLGMcN3g = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::float2*, void**)>(functionPointers[641]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_SJOlUbxBoNfhxbRZHSyjCA = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumIntVec4*, void**)>(functionPointers[642]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_t__W_mBs2JX7Isb90n6lv8A = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[643]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_t4X__QJT6bJG22Rlb0EUSGg = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::double2x2*, void**)>(functionPointers[644]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_tgJ__I0QxIjujzxx4laL3bA = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumIntMat4x4*, void**)>(functionPointers[645]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_VPZKsFl98vDFige9cNHc9g = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::float4*, void**)>(functionPointers[646]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_WfkO9L_m4izzalpvtro06A = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumUintMat3x3*, void**)>(functionPointers[647]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_wnAsp0qKwHuRGJ3ZIPvzeA = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[648]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_YhLOr6l38fDvTI1UYnZdTg = reinterpret_cast<void (*)(void*, const ::DotNet::Unity::Mathematics::float4x4*, void**)>(functionPointers[649]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[650]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::Property_get_objectValue = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[651]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::Property_get_valueType = reinterpret_cast<void (*)(void*, ::DotNet::CesiumForUnity::CesiumMetadataValueType*, void**)>(functionPointers[652]);
  ::DotNet::CesiumForUnity::CesiumMetadataValue::Property_set_objectValue = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[653]);
  ::DotNet::CesiumForUnity::CesiumMetadataValueType::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(::DotNet::CesiumForUnity::CesiumMetadataValueType*, void**)>(functionPointers[654]);
  ::DotNet::CesiumForUnity::CesiumMetadataValueType::Construct_RFYaAjfQVfO4__8eI7fs9pw = reinterpret_cast<void (*)(::std::uint32_t, ::std::uint32_t, ::std::uint8_t, ::DotNet::CesiumForUnity::CesiumMetadataValueType*, void**)>(functionPointers[655]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[656]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[657]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[658]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[659]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[660]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[661]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[662]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[663]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[664]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Property_get_propertyTables = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[665]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[666]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[667]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[668]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[669]);
  ::DotNet::CesiumForUnity::CesiumModelMetadata::Property_set_propertyTables = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[670]);
  ::DotNet::CesiumForUnity::CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::CallGet_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[671]);
  ::DotNet::CesiumForUnity::CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::CallRelease_BN9YLS5wYv1kZRcsGBjgEg = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[672]);
  ::DotNet::CesiumForUnity::CesiumObjectPools::Property_get_MeshPool = reinterpret_cast<void* (*)(void**)>(functionPointers[673]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[674]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[675]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[676]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[677]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[678]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[679]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[680]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[681]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[682]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[683]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[684]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[685]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[686]);
  ::DotNet::CesiumForUnity::CesiumPointCloudRenderer::Property_set_tileInfo = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::Cesium3DTileInfo*, void**)>(functionPointers[687]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[688]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[689]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[690]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[691]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[692]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[693]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[694]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[695]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[696]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_excludeSelectedTiles = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[697]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[698]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[699]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_invertSelection = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[700]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_materialKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[701]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[702]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[703]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_maximumTextureSize = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[704]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[705]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[706]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_polygons = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[707]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[708]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_subTileCacheBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[709]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[710]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[711]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_excludeSelectedTiles = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[712]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[713]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_invertSelection = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[714]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_materialKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[715]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[716]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[717]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_maximumTextureSize = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[718]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[719]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_polygons = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[720]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[721]);
  ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay::Property_set_subTileCacheBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[722]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[723]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[724]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[725]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[726]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[727]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[728]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_featureIdSets = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[729]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[730]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[731]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[732]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[733]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[734]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_set_featureIdSets = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[735]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[736]);
  ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[737]);
  ::DotNet::CesiumForUnity::CesiumPropertyArray::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[738]);
  ::DotNet::CesiumForUnity::CesiumPropertyArray::Property_get_elementValueType = reinterpret_cast<void (*)(void*, ::DotNet::CesiumForUnity::CesiumMetadataValueType*, void**)>(functionPointers[739]);
  ::DotNet::CesiumForUnity::CesiumPropertyArray::Property_get_values = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[740]);
  ::DotNet::CesiumForUnity::CesiumPropertyArray::Property_set_elementValueType = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumMetadataValueType*, void**)>(functionPointers[741]);
  ::DotNet::CesiumForUnity::CesiumPropertyArray::Property_set_values = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[742]);
  ::DotNet::CesiumForUnity::CesiumPropertyTable::CallDisposeProperties_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[743]);
  ::DotNet::CesiumForUnity::CesiumPropertyTable::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[744]);
  ::DotNet::CesiumForUnity::CesiumPropertyTable::Property_get_count = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[745]);
  ::DotNet::CesiumForUnity::CesiumPropertyTable::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[746]);
  ::DotNet::CesiumForUnity::CesiumPropertyTable::Property_get_properties = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[747]);
  ::DotNet::CesiumForUnity::CesiumPropertyTable::Property_get_status = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[748]);
  ::DotNet::CesiumForUnity::CesiumPropertyTable::Property_set_count = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[749]);
  ::DotNet::CesiumForUnity::CesiumPropertyTable::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[750]);
  ::DotNet::CesiumForUnity::CesiumPropertyTable::Property_set_properties = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[751]);
  ::DotNet::CesiumForUnity::CesiumPropertyTable::Property_set_status = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[752]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[753]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_arraySize = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[754]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_defaultValue = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[755]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_isNormalized = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[756]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_max = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[757]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_min = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[758]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[759]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_noData = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[760]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_offset = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[761]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_scale = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[762]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_size = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[763]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_status = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[764]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_valueType = reinterpret_cast<void (*)(void*, ::DotNet::CesiumForUnity::CesiumMetadataValueType*, void**)>(functionPointers[765]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_arraySize = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[766]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_defaultValue = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[767]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_isNormalized = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[768]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_max = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[769]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_min = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[770]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_noData = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[771]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_offset = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[772]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_scale = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[773]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_size = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[774]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_status = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[775]);
  ::DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_valueType = reinterpret_cast<void (*)(void*, const ::DotNet::CesiumForUnity::CesiumMetadataValueType*, void**)>(functionPointers[776]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[777]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::CallBroadcastCesiumRasterOverlayLoadFailure_wzyCuVNVqUYPXthsoxKvyw = reinterpret_cast<void (*)(void*, void**)>(functionPointers[778]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[779]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[780]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[781]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[782]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[783]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[784]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[785]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[786]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[787]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[788]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_get_materialKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[789]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[790]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[791]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_get_maximumTextureSize = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[792]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[793]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[794]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_get_subTileCacheBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[795]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[796]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[797]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[798]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_set_materialKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[799]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[800]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[801]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_set_maximumTextureSize = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[802]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[803]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[804]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlay::Property_set_subTileCacheBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[805]);
  ::DotNet::CesiumForUnity::CesiumRasterOverlayLoadFailureDetails::Construct___R__AqUOiZnUHIgxRnspXXw = reinterpret_cast<void* (*)(void*, ::std::uint32_t, ::std::int64_t, void*, void**)>(functionPointers[806]);
  ::DotNet::CesiumForUnity::CesiumRuntimeSettings::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[807]);
  ::DotNet::CesiumForUnity::CesiumRuntimeSettings::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[808]);
  ::DotNet::CesiumForUnity::CesiumRuntimeSettings::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[809]);
  ::DotNet::CesiumForUnity::CesiumRuntimeSettings::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[810]);
  ::DotNet::CesiumForUnity::CesiumRuntimeSettings::Property_get_maxItems = reinterpret_cast<::std::uint64_t (*)(void**)>(functionPointers[811]);
  ::DotNet::CesiumForUnity::CesiumRuntimeSettings::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[812]);
  ::DotNet::CesiumForUnity::CesiumRuntimeSettings::Property_get_requestsPerCachePrune = reinterpret_cast<::std::int32_t (*)(void**)>(functionPointers[813]);
  ::DotNet::CesiumForUnity::CesiumRuntimeSettings::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[814]);
  ::DotNet::CesiumForUnity::CesiumRuntimeSettings::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[815]);
  ::DotNet::CesiumForUnity::CesiumSampleHeightResult::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[816]);
  ::DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_get_longitudeLatitudeHeightPositions = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[817]);
  ::DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_get_sampleSuccess = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[818]);
  ::DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_get_warnings = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[819]);
  ::DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_set_longitudeLatitudeHeightPositions = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[820]);
  ::DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_set_sampleSuccess = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[821]);
  ::DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_set_warnings = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[822]);
  ::DotNet::CesiumForUnity::CesiumSimplePlanarEllipsoidCurve::CallFromCenteredFixedCoordinates_Xlu0WX31sapbYyKKJDYoaw = reinterpret_cast<void* (*)(void*, const ::DotNet::Unity::Mathematics::double3*, const ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[823]);
  ::DotNet::CesiumForUnity::CesiumSimplePlanarEllipsoidCurve::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[824]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::CallAddToTileset_SrfNoP9IJM__ZwyysR9yJTQ = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[825]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[826]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[827]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[828]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[829]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::CallRemoveFromTileset_SrfNoP9IJM__ZwyysR9yJTQ = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[830]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::CallShouldExclude_UETWPhv0ANQLUqKbOQlZcw = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[831]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[832]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[833]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[834]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[835]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[836]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[837]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[838]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[839]);
  ::DotNet::CesiumForUnity::CesiumTileExcluder::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[840]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[841]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[842]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[843]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[844]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[845]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[846]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[847]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[848]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[849]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[850]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[851]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_materialKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[852]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_maximumLevel = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[853]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[854]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[855]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_maximumTextureSize = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[856]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_minimumLevel = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[857]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[858]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[859]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[860]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_specifyZoomLevels = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[861]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_subTileCacheBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[862]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[863]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_get_url = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[864]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[865]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[866]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_materialKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[867]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_maximumLevel = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[868]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[869]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[870]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_maximumTextureSize = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[871]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_minimumLevel = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[872]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[873]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[874]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_specifyZoomLevels = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[875]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_subTileCacheBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[876]);
  ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay::Property_set_url = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[877]);
  ::DotNet::CesiumForUnity::CesiumUintMat2x2::Construct__GL6rL0hCqqkoxAtnbIobQ = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumUintVec2*, const ::DotNet::CesiumForUnity::CesiumUintVec2*, ::DotNet::CesiumForUnity::CesiumUintMat2x2*, void**)>(functionPointers[878]);
  ::DotNet::CesiumForUnity::CesiumUintMat2x2::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumUintMat2x2*, ::std::int32_t, ::DotNet::CesiumForUnity::CesiumUintVec2*, void**)>(functionPointers[879]);
  ::DotNet::CesiumForUnity::CesiumUintMat3x3::Construct_Y4SfatHSU__2N_SCzuuF_Fg = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumUintVec3*, const ::DotNet::CesiumForUnity::CesiumUintVec3*, const ::DotNet::CesiumForUnity::CesiumUintVec3*, ::DotNet::CesiumForUnity::CesiumUintMat3x3*, void**)>(functionPointers[880]);
  ::DotNet::CesiumForUnity::CesiumUintMat3x3::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumUintMat3x3*, ::std::int32_t, ::DotNet::CesiumForUnity::CesiumUintVec3*, void**)>(functionPointers[881]);
  ::DotNet::CesiumForUnity::CesiumUintMat4x4::Construct_UoXJ1ZrrVKjTtIO7sqwAHQ = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumUintVec4*, const ::DotNet::CesiumForUnity::CesiumUintVec4*, const ::DotNet::CesiumForUnity::CesiumUintVec4*, const ::DotNet::CesiumForUnity::CesiumUintVec4*, ::DotNet::CesiumForUnity::CesiumUintMat4x4*, void**)>(functionPointers[882]);
  ::DotNet::CesiumForUnity::CesiumUintMat4x4::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::CesiumForUnity::CesiumUintMat4x4*, ::std::int32_t, ::DotNet::CesiumForUnity::CesiumUintVec4*, void**)>(functionPointers[883]);
  ::DotNet::CesiumForUnity::CesiumUintVec2::Construct_41DRfMZ91WmKUsGkzEnbPw = reinterpret_cast<void (*)(::std::uint32_t, ::std::uint32_t, ::DotNet::CesiumForUnity::CesiumUintVec2*, void**)>(functionPointers[884]);
  ::DotNet::CesiumForUnity::CesiumUintVec2::Construct_nrWljXjq__N5wiftR3c_JGg = reinterpret_cast<void (*)(::std::uint64_t, ::std::uint64_t, ::DotNet::CesiumForUnity::CesiumUintVec2*, void**)>(functionPointers[885]);
  ::DotNet::CesiumForUnity::CesiumUintVec2::Construct_ooy5yIq__mBEC6X6EtGX5Ow = reinterpret_cast<void (*)(::std::uint8_t, ::std::uint8_t, ::DotNet::CesiumForUnity::CesiumUintVec2*, void**)>(functionPointers[886]);
  ::DotNet::CesiumForUnity::CesiumUintVec2::Construct_XhEMD4DBm1OQpJbAQjBMWw = reinterpret_cast<void (*)(::std::uint16_t, ::std::uint16_t, ::DotNet::CesiumForUnity::CesiumUintVec2*, void**)>(functionPointers[887]);
  ::DotNet::CesiumForUnity::CesiumUintVec2::Property_get_Item = reinterpret_cast<::std::uint64_t (*)(const ::DotNet::CesiumForUnity::CesiumUintVec2*, ::std::int32_t, void**)>(functionPointers[888]);
  ::DotNet::CesiumForUnity::CesiumUintVec3::Construct_fwI58ky8hlqSzCrUJCqq4Q = reinterpret_cast<void (*)(::std::uint32_t, ::std::uint32_t, ::std::uint32_t, ::DotNet::CesiumForUnity::CesiumUintVec3*, void**)>(functionPointers[889]);
  ::DotNet::CesiumForUnity::CesiumUintVec3::Construct_jH1j0POYh80kGurO6bbg6w = reinterpret_cast<void (*)(::std::uint8_t, ::std::uint8_t, ::std::uint8_t, ::DotNet::CesiumForUnity::CesiumUintVec3*, void**)>(functionPointers[890]);
  ::DotNet::CesiumForUnity::CesiumUintVec3::Construct_r71YnkpCpNgMBAJTUEeKlg = reinterpret_cast<void (*)(::std::uint16_t, ::std::uint16_t, ::std::uint16_t, ::DotNet::CesiumForUnity::CesiumUintVec3*, void**)>(functionPointers[891]);
  ::DotNet::CesiumForUnity::CesiumUintVec3::Construct_ZbSqyVsWZtDI0Ryj__6S2Iw = reinterpret_cast<void (*)(::std::uint64_t, ::std::uint64_t, ::std::uint64_t, ::DotNet::CesiumForUnity::CesiumUintVec3*, void**)>(functionPointers[892]);
  ::DotNet::CesiumForUnity::CesiumUintVec3::Property_get_Item = reinterpret_cast<::std::uint64_t (*)(const ::DotNet::CesiumForUnity::CesiumUintVec3*, ::std::int32_t, void**)>(functionPointers[893]);
  ::DotNet::CesiumForUnity::CesiumUintVec4::Construct_cx5C8OyRaFgckdYoG5u6cw = reinterpret_cast<void (*)(::std::uint32_t, ::std::uint32_t, ::std::uint32_t, ::std::uint32_t, ::DotNet::CesiumForUnity::CesiumUintVec4*, void**)>(functionPointers[894]);
  ::DotNet::CesiumForUnity::CesiumUintVec4::Construct_eKggYQNxOSW0_H_SNc53xA = reinterpret_cast<void (*)(::std::uint64_t, ::std::uint64_t, ::std::uint64_t, ::std::uint64_t, ::DotNet::CesiumForUnity::CesiumUintVec4*, void**)>(functionPointers[895]);
  ::DotNet::CesiumForUnity::CesiumUintVec4::Construct_V8zlQY__7MR4_A1Ek6HBQqg = reinterpret_cast<void (*)(::std::uint8_t, ::std::uint8_t, ::std::uint8_t, ::std::uint8_t, ::DotNet::CesiumForUnity::CesiumUintVec4*, void**)>(functionPointers[896]);
  ::DotNet::CesiumForUnity::CesiumUintVec4::Construct_yp__VrxlOcxUXq2RwGv8mXw = reinterpret_cast<void (*)(::std::uint16_t, ::std::uint16_t, ::std::uint16_t, ::std::uint16_t, ::DotNet::CesiumForUnity::CesiumUintVec4*, void**)>(functionPointers[897]);
  ::DotNet::CesiumForUnity::CesiumUintVec4::Property_get_Item = reinterpret_cast<::std::uint64_t (*)(const ::DotNet::CesiumForUnity::CesiumUintVec4*, ::std::int32_t, void**)>(functionPointers[898]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[899]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[900]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[901]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[902]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[903]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[904]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[905]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[906]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[907]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[908]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[909]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_materialKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[910]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_maximumLevel = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[911]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[912]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[913]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_maximumTextureSize = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[914]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_minimumLevel = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[915]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[916]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[917]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_projection = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[918]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rectangleEast = reinterpret_cast<double (*)(void*, void**)>(functionPointers[919]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rectangleNorth = reinterpret_cast<double (*)(void*, void**)>(functionPointers[920]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rectangleSouth = reinterpret_cast<double (*)(void*, void**)>(functionPointers[921]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rectangleWest = reinterpret_cast<double (*)(void*, void**)>(functionPointers[922]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_requestHeaders = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[923]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rootTilesX = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[924]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rootTilesY = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[925]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[926]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_specifyTilingScheme = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[927]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_subTileCacheBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[928]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_templateUrl = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[929]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_tileHeight = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[930]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_tileWidth = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[931]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[932]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[933]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[934]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_materialKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[935]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_maximumLevel = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[936]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[937]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[938]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_maximumTextureSize = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[939]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_minimumLevel = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[940]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[941]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_projection = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[942]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rectangleEast = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[943]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rectangleNorth = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[944]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rectangleSouth = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[945]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rectangleWest = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[946]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_requestHeaders = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[947]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rootTilesX = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[948]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rootTilesY = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[949]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[950]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_specifyTilingScheme = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[951]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_subTileCacheBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[952]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_templateUrl = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[953]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_tileHeight = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[954]);
  ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_tileWidth = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[955]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[956]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[957]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[958]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[959]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[960]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[961]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[962]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[963]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_baseUrl = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[964]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[965]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[966]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[967]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_layers = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[968]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_materialKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[969]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_maximumLevel = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[970]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[971]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[972]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_maximumTextureSize = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[973]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_minimumLevel = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[974]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[975]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[976]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[977]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_subTileCacheBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[978]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_tileHeight = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[979]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_tileWidth = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[980]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[981]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_baseUrl = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[982]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[983]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[984]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_layers = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[985]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_materialKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[986]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_maximumLevel = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[987]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[988]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[989]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_maximumTextureSize = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[990]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_minimumLevel = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[991]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[992]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[993]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_subTileCacheBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[994]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_tileHeight = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[995]);
  ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay::Property_set_tileWidth = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[996]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[997]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[998]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[999]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1000]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1001]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1002]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1003]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[1004]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_baseUrl = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1005]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1006]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_format = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1007]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1008]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1009]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_layer = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1010]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_materialKey = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1011]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_maximumLevel = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1012]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_maximumScreenSpaceError = reinterpret_cast<float (*)(void*, void**)>(functionPointers[1013]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_maximumSimultaneousTileLoads = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1014]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_maximumTextureSize = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1015]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_minimumLevel = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1016]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1017]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[1018]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_projection = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1019]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rectangleEast = reinterpret_cast<double (*)(void*, void**)>(functionPointers[1020]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rectangleNorth = reinterpret_cast<double (*)(void*, void**)>(functionPointers[1021]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rectangleSouth = reinterpret_cast<double (*)(void*, void**)>(functionPointers[1022]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rectangleWest = reinterpret_cast<double (*)(void*, void**)>(functionPointers[1023]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rootTilesX = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1024]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rootTilesY = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1025]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_showCreditsOnScreen = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1026]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_specifyTileMatrixSetLabels = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1027]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_specifyTilingScheme = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1028]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_specifyZoomLevels = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1029]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_style = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1030]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_subTileCacheBytes = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[1031]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_tileHeight = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1032]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_tileMatrixSetID = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1033]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_tileMatrixSetLabelPrefix = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1034]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_tileMatrixSetLabels = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1035]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_tileWidth = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1036]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1037]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_baseUrl = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1038]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1039]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_format = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1040]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1041]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_layer = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1042]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_materialKey = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1043]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_maximumLevel = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1044]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_maximumScreenSpaceError = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[1045]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_maximumSimultaneousTileLoads = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1046]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_maximumTextureSize = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1047]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_minimumLevel = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1048]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1049]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_projection = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1050]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rectangleEast = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[1051]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rectangleNorth = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[1052]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rectangleSouth = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[1053]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rectangleWest = reinterpret_cast<void (*)(void*, double, void**)>(functionPointers[1054]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rootTilesX = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1055]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rootTilesY = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1056]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_showCreditsOnScreen = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1057]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_specifyTileMatrixSetLabels = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1058]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_specifyTilingScheme = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1059]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_specifyZoomLevels = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1060]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_style = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1061]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_subTileCacheBytes = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[1062]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_tileHeight = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1063]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_tileMatrixSetID = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1064]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_tileMatrixSetLabelPrefix = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1065]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_tileMatrixSetLabels = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1066]);
  ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_tileWidth = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1067]);
  ::DotNet::CesiumForUnity::HeaderEntry::Field_get_Name = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[1068]);
  ::DotNet::CesiumForUnity::HeaderEntry::Field_get_Value = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[1069]);
  ::DotNet::CesiumForUnity::HeaderEntry::Field_set_Name = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[1070]);
  ::DotNet::CesiumForUnity::HeaderEntry::Field_set_Value = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[1071]);
  ::DotNet::CesiumForUnity::Helpers::CallToString__8pn__Nas4aiRxhf1NkpeKg = reinterpret_cast<void* (*)(::std::uint32_t, void**)>(functionPointers[1072]);
  ::DotNet::CesiumForUnity::IonAssetDetails::CallFormatDate_Wg__UxSmEJUgHx3kyfccFEw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1073]);
  ::DotNet::CesiumForUnity::IonAssetDetails::CallFormatType_3GczHehc_XCRt9ReXGSrdQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1074]);
  ::DotNet::CesiumForUnity::IonAssetsTreeView::CallReload_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1075]);
  ::DotNet::CesiumForUnity::IonAssetsTreeView::Construct_bk3kO2aTAFaE0GWD9sxbig = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1076]);
  ::DotNet::CesiumForUnity::IonAssetsTreeView::Property_get_multiColumnHeader = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1077]);
  ::DotNet::CesiumForUnity::IonAssetsTreeView::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[1078]);
  ::DotNet::CesiumForUnity::IonAssetsTreeView::Property_get_searchString = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1079]);
  ::DotNet::CesiumForUnity::IonAssetsTreeView::Property_set_multiColumnHeader = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1080]);
  ::DotNet::CesiumForUnity::IonAssetsTreeView::Property_set_searchString = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1081]);
  ::DotNet::CesiumForUnity::IonMissingAssetWindow::CallClose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1082]);
  ::DotNet::CesiumForUnity::IonMissingAssetWindow::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1083]);
  ::DotNet::CesiumForUnity::IonMissingAssetWindow::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1084]);
  ::DotNet::CesiumForUnity::IonMissingAssetWindow::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1085]);
  ::DotNet::CesiumForUnity::IonMissingAssetWindow::CallShowWindow_zCuaF57FLiXZD1__wksXLdQ = reinterpret_cast<void (*)(void*, ::std::int64_t, void**)>(functionPointers[1086]);
  ::DotNet::CesiumForUnity::IonMissingAssetWindow::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1087]);
  ::DotNet::CesiumForUnity::IonMissingAssetWindow::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1088]);
  ::DotNet::CesiumForUnity::IonMissingAssetWindow::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1089]);
  ::DotNet::CesiumForUnity::IonMissingAssetWindow::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1090]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::CallClose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1091]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1092]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1093]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1094]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::CallUseDefaultToken_qpX7eE7SvOg4KIeidX7yng = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1095]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_assetDetails = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1096]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_assetTokenDetails = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1097]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_defaultTokenDetails = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1098]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1099]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_ionAsset = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1100]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1101]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1102]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_set_ionAsset = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1103]);
  ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1104]);
  ::DotNet::CesiumForUnity::NativeCoroutine::CallGetEnumerator_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1105]);
  ::DotNet::CesiumForUnity::NativeCoroutine::Construct_cIsazMJakk__Bsh3eD72HgQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1106]);
  ::DotNet::CesiumForUnity::NativeDownloadHandler::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1107]);
  ::DotNet::CesiumForUnity::NativeDownloadHandler::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1108]);
  ::DotNet::CesiumForUnity::NativeDownloadHandler::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[1109]);
  ::DotNet::CesiumForUnity::QuickAddItem::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1110]);
  ::DotNet::CesiumForUnity::QuickAddItem::Construct_MigqS33KRbgyAt6uiJjTGw = reinterpret_cast<void* (*)(::std::uint32_t, void*, void*, void*, ::std::int64_t, void*, ::std::int64_t, void**)>(functionPointers[1111]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_get_name = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[1112]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_get_overlayId = reinterpret_cast<::std::int64_t (*)(void* thiz, void** reinteropException)>(functionPointers[1113]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_get_overlayName = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[1114]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_get_tilesetId = reinterpret_cast<::std::int64_t (*)(void* thiz, void** reinteropException)>(functionPointers[1115]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_get_tilesetName = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[1116]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_get_tooltip = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[1117]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_get_type = reinterpret_cast<::std::uint32_t (*)(void* thiz, void** reinteropException)>(functionPointers[1118]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_set_name = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[1119]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_set_overlayId = reinterpret_cast<void (*)(void* thiz, ::std::int64_t value, void** reinteropException)>(functionPointers[1120]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_set_overlayName = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[1121]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_set_tilesetId = reinterpret_cast<void (*)(void* thiz, ::std::int64_t value, void** reinteropException)>(functionPointers[1122]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_set_tilesetName = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[1123]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_set_tooltip = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[1124]);
  ::DotNet::CesiumForUnity::QuickAddItem::Field_set_type = reinterpret_cast<void (*)(void* thiz, ::std::uint32_t value, void** reinteropException)>(functionPointers[1125]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::CallClose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1126]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::CallGetDefaultNewTokenName_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1127]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::CallGetExistingTokenList_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1128]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1129]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1130]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1131]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::CallRefreshExistingTokenList_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1132]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::CallShowWindow_ouKG7YNdV4bUJcBV0W3dBA = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1133]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Field_get_currentWindow = reinterpret_cast<void* (*)(void** reinteropException)>(functionPointers[1134]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Field_get_server = reinterpret_cast<void* (*)(void* thiz, void** reinteropException)>(functionPointers[1135]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Field_set_currentWindow = reinterpret_cast<void (*)(void* value, void** reinteropException)>(functionPointers[1136]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Field_set_server = reinterpret_cast<void (*)(void* thiz, void* value, void** reinteropException)>(functionPointers[1137]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_createdTokenName = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1138]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1139]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1140]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[1141]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_selectedExistingTokenIndex = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1142]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_specifiedToken = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1143]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_tokenSource = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1144]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_createdTokenName = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1145]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1146]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1147]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_selectedExistingTokenIndex = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1148]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_specifiedToken = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1149]);
  ::DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_tokenSource = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1150]);
  ::DotNet::CesiumForUnity::TestGltfModel::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1151]);
  ::DotNet::CesiumForUnity::TestGltfModel::Property_get_NativeImplementation = reinterpret_cast<void* (*)(void*)>(functionPointers[1152]);
  ::DotNet::CesiumForUnity::TestReinterop::CallThrowAnException_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void**)>(functionPointers[1153]);
  ::DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_get_allowsAccessToAsset = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1154]);
  ::DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_get_associatedWithUserAccount = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1155]);
  ::DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_get_isValid = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1156]);
  ::DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_get_loaded = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1157]);
  ::DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_get_token = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1158]);
  ::DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_set_allowsAccessToAsset = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1159]);
  ::DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_set_associatedWithUserAccount = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1160]);
  ::DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_set_isValid = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1161]);
  ::DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_set_loaded = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1162]);
  ::DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_set_token = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1163]);
  ::DotNet::Reinterop::ObjectHandleUtility::CallCopyHandle_Lk0gUmdC13dRVZ_MAT71eg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1164]);
  ::DotNet::Reinterop::ObjectHandleUtility::CallCreateHandle_vjOnn8y5DjvqKs3467vAJQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1165]);
  ::DotNet::Reinterop::ObjectHandleUtility::CallFreeHandle_Lk0gUmdC13dRVZ_MAT71eg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1166]);
  ::DotNet::Reinterop::ReinteropException::Construct_XwA9a8yCTL1RNh1m2OT3bA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1167]);
  ::DotNet::Reinterop::ReinteropException::Property_get_Message = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1168]);
  ::DotNet::System::Action::CallInvoke_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1169]);
  ::DotNet::System::Action::Callop_Equality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1170]);
  ::DotNet::System::Action::Callop_Equality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1171]);
  ::DotNet::System::Action::Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1172]);
  ::DotNet::System::Action::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1173]);
  ::DotNet::System::Action::CombineDelegates = reinterpret_cast<void* (*)(void*, void*)>(functionPointers[1174]);
  ::DotNet::System::Action::CreateDelegate = reinterpret_cast<void* (*)(void*)>(functionPointers[1175]);
  ::DotNet::System::Action::DisposeDelegate = reinterpret_cast<void (*)(void*)>(functionPointers[1176]);
  ::DotNet::System::Action::RemoveDelegate = reinterpret_cast<void* (*)(void*, void*)>(functionPointers[1177]);
  ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::CallInvoke_GZtSECpzDV__dvLP8ujKEdA = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1178]);
  ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::Callop_Equality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1179]);
  ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::Callop_Equality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1180]);
  ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1181]);
  ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1182]);
  ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::CombineDelegates = reinterpret_cast<void* (*)(void*, void*)>(functionPointers[1183]);
  ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::CreateDelegate = reinterpret_cast<void* (*)(void*)>(functionPointers[1184]);
  ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::DisposeDelegate = reinterpret_cast<void (*)(void*)>(functionPointers[1185]);
  ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::RemoveDelegate = reinterpret_cast<void* (*)(void*, void*)>(functionPointers[1186]);
  ::DotNet::System::Array::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1187]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1188]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1189]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1190]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::Cesium3DTileset>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1191]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeature>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1192]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeature>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1193]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeature>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1194]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeature>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1195]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1196]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1197]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1198]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1199]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1200]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1201]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1202]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1203]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1204]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1205]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1206]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1207]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1208]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1209]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1210]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1211]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1212]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1213]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1214]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumPropertyTable>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1215]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1216]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1217]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1218]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1219]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1220]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1221]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1222]);
  ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1223]);
  ::DotNet::System::Array1<::DotNet::System::String>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1224]);
  ::DotNet::System::Array1<::DotNet::System::String>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1225]);
  ::DotNet::System::Array1<::DotNet::System::String>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1226]);
  ::DotNet::System::Array1<::DotNet::System::String>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1227]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::double3>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1228]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::double3>::Property_get_Item = reinterpret_cast<void (*)(void*, ::std::int32_t, ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[1229]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::double3>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1230]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::double3>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, const ::DotNet::Unity::Mathematics::double3*)>(functionPointers[1231]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float2>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1232]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float2>::Property_get_Item = reinterpret_cast<void (*)(void*, ::std::int32_t, ::DotNet::Unity::Mathematics::float2*, void**)>(functionPointers[1233]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float2>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1234]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float2>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, const ::DotNet::Unity::Mathematics::float2*)>(functionPointers[1235]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float2x2>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1236]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float2x2>::Property_get_Item = reinterpret_cast<void (*)(void*, ::std::int32_t, ::DotNet::Unity::Mathematics::float2x2*, void**)>(functionPointers[1237]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float2x2>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1238]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float2x2>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, const ::DotNet::Unity::Mathematics::float2x2*)>(functionPointers[1239]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float3>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1240]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float3>::Property_get_Item = reinterpret_cast<void (*)(void*, ::std::int32_t, ::DotNet::Unity::Mathematics::float3*, void**)>(functionPointers[1241]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float3>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1242]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float3>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, const ::DotNet::Unity::Mathematics::float3*)>(functionPointers[1243]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float3x3>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1244]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float3x3>::Property_get_Item = reinterpret_cast<void (*)(void*, ::std::int32_t, ::DotNet::Unity::Mathematics::float3x3*, void**)>(functionPointers[1245]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float3x3>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1246]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float3x3>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, const ::DotNet::Unity::Mathematics::float3x3*)>(functionPointers[1247]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float4>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1248]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float4>::Property_get_Item = reinterpret_cast<void (*)(void*, ::std::int32_t, ::DotNet::Unity::Mathematics::float4*, void**)>(functionPointers[1249]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float4>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1250]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float4>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, const ::DotNet::Unity::Mathematics::float4*)>(functionPointers[1251]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float4x4>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1252]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float4x4>::Property_get_Item = reinterpret_cast<void (*)(void*, ::std::int32_t, ::DotNet::Unity::Mathematics::float4x4*, void**)>(functionPointers[1253]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float4x4>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1254]);
  ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float4x4>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, const ::DotNet::Unity::Mathematics::float4x4*)>(functionPointers[1255]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::GameObject>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1256]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::GameObject>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1257]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::GameObject>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1258]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::GameObject>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1259]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Mesh>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1260]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Mesh>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1261]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Mesh>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1262]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Mesh>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, void*)>(functionPointers[1263]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1264]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::Property_get_Item = reinterpret_cast<void (*)(void*, ::std::int32_t, ::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor*, void**)>(functionPointers[1265]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1266]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, const ::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor*)>(functionPointers[1267]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Vector3>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1268]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Vector3>::Property_get_Item = reinterpret_cast<void (*)(void*, ::std::int32_t, ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1269]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Vector3>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1270]);
  ::DotNet::System::Array1<::DotNet::UnityEngine::Vector3>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, const ::DotNet::UnityEngine::Vector3*)>(functionPointers[1271]);
  ::DotNet::System::Array1<::std::int32_t>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1272]);
  ::DotNet::System::Array1<::std::int32_t>::Property_get_Item = reinterpret_cast<::std::int32_t (*)(void*, ::std::int32_t, void**)>(functionPointers[1273]);
  ::DotNet::System::Array1<::std::int32_t>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1274]);
  ::DotNet::System::Array1<::std::int32_t>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, ::std::int32_t)>(functionPointers[1275]);
  ::DotNet::System::Array1<::std::uint16_t>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1276]);
  ::DotNet::System::Array1<::std::uint16_t>::Property_get_Item = reinterpret_cast<::std::uint16_t (*)(void*, ::std::int32_t, void**)>(functionPointers[1277]);
  ::DotNet::System::Array1<::std::uint16_t>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1278]);
  ::DotNet::System::Array1<::std::uint16_t>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, ::std::uint16_t)>(functionPointers[1279]);
  ::DotNet::System::Array1<::std::uint8_t>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1280]);
  ::DotNet::System::Array1<::std::uint8_t>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1281]);
  ::DotNet::System::Array1<::std::uint8_t>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, ::std::uint8_t)>(functionPointers[1282]);
  ::DotNet::System::Array1<bool>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1283]);
  ::DotNet::System::Array1<bool>::Property_get_Item = reinterpret_cast<::std::uint8_t (*)(void*, ::std::int32_t, void**)>(functionPointers[1284]);
  ::DotNet::System::Array1<bool>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1285]);
  ::DotNet::System::Array1<bool>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, ::std::uint8_t)>(functionPointers[1286]);
  ::DotNet::System::Array1<double>::Construct_Size = reinterpret_cast<void* (*)(std::int32_t size)>(functionPointers[1287]);
  ::DotNet::System::Array1<double>::Property_get_Item = reinterpret_cast<double (*)(void*, ::std::int32_t, void**)>(functionPointers[1288]);
  ::DotNet::System::Array1<double>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1289]);
  ::DotNet::System::Array1<double>::SetItem = reinterpret_cast<void (*)(void*, std::int32_t, double)>(functionPointers[1290]);
  ::DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::CallAdd_zclURTnfSFbfrVxWQq_LWQ = reinterpret_cast<void (*)(void*, void*, void*, void**)>(functionPointers[1291]);
  ::DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>::Construct_WGe5Irde9C7cSq7hDUfI5Q = reinterpret_cast<void* (*)(::std::int32_t, void**)>(functionPointers[1292]);
  ::DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::System::String>::CallGetEnumerator_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1293]);
  ::DotNet::System::Collections::Generic::Enumerator0::CallMoveNext_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1294]);
  ::DotNet::System::Collections::Generic::Enumerator0::Property_get_Current = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1295]);
  ::DotNet::System::Collections::Generic::KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::Property_get_Key = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1296]);
  ::DotNet::System::Collections::Generic::KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::Property_get_Value = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1297]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::Property_get_Count = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1298]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1299]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCredit>::CallAdd_DnUt__NGf__FxtU__keZH5Geg = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1300]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCredit>::CallClear_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1301]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::CallAdd_VqNpQ4Sqmxp7DzXSAQsehQ = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1302]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1303]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCreditComponent>::Property_get_Count = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1304]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1305]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::Property_get_Count = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1306]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>::Property_get_Item = reinterpret_cast<::std::uint32_t (*)(void*, ::std::int32_t, void**)>(functionPointers[1307]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::HeaderEntry>::Property_get_Count = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1308]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::HeaderEntry>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1309]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::QuickAddItem>::CallAdd_nq8TJwFX_ptyb2rCV3CGsw = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1310]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::QuickAddItem>::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1311]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>::CallAdd_LRSjiXmrvb5pgfbcZ_Nv7w = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1312]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>::CallClear_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1313]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>::CallToArray_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1314]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1315]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>::Property_get_Count = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1316]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1317]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::Unity::Mathematics::double2>::Property_get_Count = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1318]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::Unity::Mathematics::double2>::Property_get_Item = reinterpret_cast<void (*)(void*, ::std::int32_t, ::DotNet::Unity::Mathematics::double2*, void**)>(functionPointers[1319]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::UnityEngine::Camera>::Property_get_Count = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1320]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::UnityEngine::Camera>::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1321]);
  ::DotNet::System::Collections::Generic::List1<::DotNet::UnityEngine::Texture2D>::Property_get_Count = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1322]);
  ::DotNet::System::Collections::Generic::List1<::std::int32_t>::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1323]);
  ::DotNet::System::Collections::Generic::List1<::std::int32_t>::Property_get_Count = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1324]);
  ::DotNet::System::Collections::Generic::List1<::std::int32_t>::Property_get_Item = reinterpret_cast<::std::int32_t (*)(void*, ::std::int32_t, void**)>(functionPointers[1325]);
  ::DotNet::System::Delegate::Callop_Equality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1326]);
  ::DotNet::System::Delegate::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1327]);
  ::DotNet::System::Environment::Property_get_OSVersion = reinterpret_cast<void* (*)(void**)>(functionPointers[1328]);
  ::DotNet::System::Exception::Construct_XwA9a8yCTL1RNh1m2OT3bA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1329]);
  ::DotNet::System::Exception::Property_get_Message = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1330]);
  ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::CallInvoke_lYA9p9IAgcAW1UlWV_LvhA = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[1331]);
  ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::Callop_Equality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1332]);
  ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::Callop_Equality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1333]);
  ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1334]);
  ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1335]);
  ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::CombineDelegates = reinterpret_cast<void* (*)(void*, void*)>(functionPointers[1336]);
  ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::CreateDelegate = reinterpret_cast<void* (*)(void*)>(functionPointers[1337]);
  ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::DisposeDelegate = reinterpret_cast<void (*)(void*)>(functionPointers[1338]);
  ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::RemoveDelegate = reinterpret_cast<void* (*)(void*, void*)>(functionPointers[1339]);
  ::DotNet::System::MulticastDelegate::Callop_Equality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1340]);
  ::DotNet::System::MulticastDelegate::Callop_Equality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1341]);
  ::DotNet::System::MulticastDelegate::Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1342]);
  ::DotNet::System::MulticastDelegate::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1343]);
  ::DotNet::System::Object::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1344]);
  ::DotNet::System::OperatingSystem::Property_get_VersionString = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1345]);
  ::DotNet::System::Runtime::InteropServices::Marshal::CallFreeCoTaskMem_eF5IwSJe_WM3IuDxcegQFg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1346]);
  ::DotNet::System::Runtime::InteropServices::Marshal::CallStringToCoTaskMemUTF8_ga80EVd9gqZ4YlhSP8iRzg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1347]);
  ::DotNet::System::String::CallConcat_OM9SoWVFMTHXvbepMyUchw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[1348]);
  ::DotNet::System::String::CallConcat_yq7nlytzIFp8a79slfH_mw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[1349]);
  ::DotNet::System::String::CallContains_GImL1A5rlEQAx14EidO2oA = reinterpret_cast<::std::uint8_t (*)(void*, void*, ::std::uint32_t, void**)>(functionPointers[1350]);
  ::DotNet::System::String::CallEquals_46DLRq__QwpwCx8Uf20Cl7A = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1351]);
  ::DotNet::System::String::CallIsNullOrEmpty_ZOWEGUlscki07yVzH4i4ww = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1352]);
  ::DotNet::System::String::CallIsNullOrWhiteSpace_ZOWEGUlscki07yVzH4i4ww = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1353]);
  ::DotNet::System::String::CallJoin_ZMypEy2QfaUCbJCXuGMgzg = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[1354]);
  ::DotNet::System::String::Callop_Equality_46DLRq__QwpwCx8Uf20Cl7A = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1355]);
  ::DotNet::System::String::Callop_Inequality_46DLRq__QwpwCx8Uf20Cl7A = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1356]);
  ::DotNet::System::String::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1357]);
  ::DotNet::System::Text::Encoding::CallGetString_J_gIxYGOW0ecDuybXJZsCw = reinterpret_cast<void* (*)(void*, ::std::uint8_t*, ::std::int32_t, void**)>(functionPointers[1358]);
  ::DotNet::System::Text::Encoding::Property_get_UTF8 = reinterpret_cast<void* (*)(void**)>(functionPointers[1359]);
  ::DotNet::System::Threading::Tasks::Task::CallRun_uG3jiSYLEmrwe0pJoPtxoA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1360]);
  ::DotNet::System::Threading::Tasks::TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::CallSetException_VrvSHSzTF_R2DRLTwid8jg = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1361]);
  ::DotNet::System::Threading::Tasks::TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::CallSetResult_DgnA9fh8lXZZ0ttkGvLh0w = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1362]);
  ::DotNet::System::Threading::Tasks::TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1363]);
  ::DotNet::System::Threading::Tasks::TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::Property_get_Task = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1364]);
  ::DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_dODsb2EbtCXW9Y67cYH1sg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1365]);
  ::DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_ExoUtqZSMWnuKvejW2dcYw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1366]);
  ::DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_iVtd6RQjrruzXGL_Bo80bw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1367]);
  ::DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_Lv3zldnuDkcZt7Gk__iYidg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1368]);
  ::DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_QIjAavb5O6M1Tim2Rs2ohQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1369]);
  ::DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_VYRTjxyHQQFS6luUIZqMHQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1370]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1371]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>::Callop_Equality_upxAhiBTuli9tU8WNSSzEg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1372]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>::Callop_Inequality_upxAhiBTuli9tU8WNSSzEg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1373]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1374]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>::Construct_fyLz0cEPCtnsPNSt__omZwQ = reinterpret_cast<void* (*)(::std::int32_t, ::std::uint32_t, ::std::uint32_t, void**)>(functionPointers[1375]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1376]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1377]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>::Callop_Equality_vrdbfdWf_jNnpc3OykEL7A = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1378]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>::Callop_Inequality_vrdbfdWf_jNnpc3OykEL7A = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1379]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1380]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>::Construct_fyLz0cEPCtnsPNSt__omZwQ = reinterpret_cast<void* (*)(::std::int32_t, ::std::uint32_t, ::std::uint32_t, void**)>(functionPointers[1381]);
  ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1382]);
  ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1383]);
  ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>::Callop_Equality_udAsXu_l5uh9odAsOsJXHQ = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1384]);
  ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>::Callop_Inequality_udAsXu_l5uh9odAsOsJXHQ = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1385]);
  ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1386]);
  ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>::Construct_fyLz0cEPCtnsPNSt__omZwQ = reinterpret_cast<void* (*)(::std::int32_t, ::std::uint32_t, ::std::uint32_t, void**)>(functionPointers[1387]);
  ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>::Callop_Equality_V583jKrqBJAPH29Lt9agWA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1388]);
  ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>::Callop_Inequality_V583jKrqBJAPH29Lt9agWA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1389]);
  ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1390]);
  ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>::Callop_Equality_Mjak7jxj5GQBeCOOhOuHAw = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1391]);
  ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>::Callop_Inequality_Mjak7jxj5GQBeCOOhOuHAw = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1392]);
  ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1393]);
  ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>::Callop_Equality___ZFbUbDYmnqRGnwegIjKPw = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1394]);
  ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>::Callop_Inequality___ZFbUbDYmnqRGnwegIjKPw = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1395]);
  ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>::Construct_fyLz0cEPCtnsPNSt__omZwQ = reinterpret_cast<void* (*)(::std::int32_t, ::std::uint32_t, ::std::uint32_t, void**)>(functionPointers[1396]);
  ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1397]);
  ::DotNet::Unity::Mathematics::double2::Construct_8gQZlbVINFTIoHYsENgIlA = reinterpret_cast<void (*)(double, double, ::DotNet::Unity::Mathematics::double2*, void**)>(functionPointers[1398]);
  ::DotNet::Unity::Mathematics::double2::Property_get_Item = reinterpret_cast<double (*)(const ::DotNet::Unity::Mathematics::double2*, ::std::int32_t, void**)>(functionPointers[1399]);
  ::DotNet::Unity::Mathematics::double2x2::Construct_N2UNoIlt5DjPRS7f8weqIA = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::double2*, const ::DotNet::Unity::Mathematics::double2*, ::DotNet::Unity::Mathematics::double2x2*, void**)>(functionPointers[1400]);
  ::DotNet::Unity::Mathematics::double2x2::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::double2x2*, ::std::int32_t, ::DotNet::Unity::Mathematics::double2*, void**)>(functionPointers[1401]);
  ::DotNet::Unity::Mathematics::double3::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[1402]);
  ::DotNet::Unity::Mathematics::double3::Construct_vFScQRRHVnKCy1ZblYgxig = reinterpret_cast<void (*)(double, double, double, ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[1403]);
  ::DotNet::Unity::Mathematics::double3::Property_get_Item = reinterpret_cast<double (*)(const ::DotNet::Unity::Mathematics::double3*, ::std::int32_t, void**)>(functionPointers[1404]);
  ::DotNet::Unity::Mathematics::double3x3::Construct_qgf8OQh32bnPxjj_codUtg = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::double3*, const ::DotNet::Unity::Mathematics::double3*, const ::DotNet::Unity::Mathematics::double3*, ::DotNet::Unity::Mathematics::double3x3*, void**)>(functionPointers[1405]);
  ::DotNet::Unity::Mathematics::double3x3::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::double3x3*, ::std::int32_t, ::DotNet::Unity::Mathematics::double3*, void**)>(functionPointers[1406]);
  ::DotNet::Unity::Mathematics::double4::Construct_vGP51u8UcgYZVrSmxERqcw = reinterpret_cast<void (*)(double, double, double, double, ::DotNet::Unity::Mathematics::double4*, void**)>(functionPointers[1407]);
  ::DotNet::Unity::Mathematics::double4::Property_get_Item = reinterpret_cast<double (*)(const ::DotNet::Unity::Mathematics::double4*, ::std::int32_t, void**)>(functionPointers[1408]);
  ::DotNet::Unity::Mathematics::double4x4::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(::DotNet::Unity::Mathematics::double4x4*, void**)>(functionPointers[1409]);
  ::DotNet::Unity::Mathematics::double4x4::Construct_Y_Piywi9K91QLK9aeVlq1w = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::double4*, const ::DotNet::Unity::Mathematics::double4*, const ::DotNet::Unity::Mathematics::double4*, const ::DotNet::Unity::Mathematics::double4*, ::DotNet::Unity::Mathematics::double4x4*, void**)>(functionPointers[1410]);
  ::DotNet::Unity::Mathematics::double4x4::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::double4x4*, ::std::int32_t, ::DotNet::Unity::Mathematics::double4*, void**)>(functionPointers[1411]);
  ::DotNet::Unity::Mathematics::float2::Construct_aHAAcVLY3x5GFF0HQijktQ = reinterpret_cast<void (*)(float, float, ::DotNet::Unity::Mathematics::float2*, void**)>(functionPointers[1412]);
  ::DotNet::Unity::Mathematics::float2::Property_get_Item = reinterpret_cast<float (*)(const ::DotNet::Unity::Mathematics::float2*, ::std::int32_t, void**)>(functionPointers[1413]);
  ::DotNet::Unity::Mathematics::float2x2::Construct_nD6FhZgoOnVALNm4NoUCeQ = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::float2*, const ::DotNet::Unity::Mathematics::float2*, ::DotNet::Unity::Mathematics::float2x2*, void**)>(functionPointers[1414]);
  ::DotNet::Unity::Mathematics::float2x2::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::float2x2*, ::std::int32_t, ::DotNet::Unity::Mathematics::float2*, void**)>(functionPointers[1415]);
  ::DotNet::Unity::Mathematics::float3::Construct_LB__scTJntm1swre2IwXuIw = reinterpret_cast<void (*)(float, float, float, ::DotNet::Unity::Mathematics::float3*, void**)>(functionPointers[1416]);
  ::DotNet::Unity::Mathematics::float3::Property_get_Item = reinterpret_cast<float (*)(const ::DotNet::Unity::Mathematics::float3*, ::std::int32_t, void**)>(functionPointers[1417]);
  ::DotNet::Unity::Mathematics::float3x3::Construct_xZgBbnocutib2NGrHT9kpA = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::float3*, const ::DotNet::Unity::Mathematics::float3*, const ::DotNet::Unity::Mathematics::float3*, ::DotNet::Unity::Mathematics::float3x3*, void**)>(functionPointers[1418]);
  ::DotNet::Unity::Mathematics::float3x3::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::float3x3*, ::std::int32_t, ::DotNet::Unity::Mathematics::float3*, void**)>(functionPointers[1419]);
  ::DotNet::Unity::Mathematics::float4::Construct_HRdOMAw1wcknBRlYiWJ61Q = reinterpret_cast<void (*)(float, float, float, float, ::DotNet::Unity::Mathematics::float4*, void**)>(functionPointers[1420]);
  ::DotNet::Unity::Mathematics::float4::Property_get_Item = reinterpret_cast<float (*)(const ::DotNet::Unity::Mathematics::float4*, ::std::int32_t, void**)>(functionPointers[1421]);
  ::DotNet::Unity::Mathematics::float4x4::Construct_40mXKMXvvkbHdnVEuqJdsw = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::float4*, const ::DotNet::Unity::Mathematics::float4*, const ::DotNet::Unity::Mathematics::float4*, const ::DotNet::Unity::Mathematics::float4*, ::DotNet::Unity::Mathematics::float4x4*, void**)>(functionPointers[1422]);
  ::DotNet::Unity::Mathematics::float4x4::Property_get_Item = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::float4x4*, ::std::int32_t, ::DotNet::Unity::Mathematics::float4*, void**)>(functionPointers[1423]);
  ::DotNet::Unity::Mathematics::int2::Construct_CSSfw_WOk6__K5__v8pO4eLw = reinterpret_cast<void (*)(::std::int32_t, ::std::int32_t, ::DotNet::Unity::Mathematics::int2*, void**)>(functionPointers[1424]);
  ::DotNet::Unity::Mathematics::int2x2::Construct_mnOQ_opjj2StriajDwrD9g = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::int2*, const ::DotNet::Unity::Mathematics::int2*, ::DotNet::Unity::Mathematics::int2x2*, void**)>(functionPointers[1425]);
  ::DotNet::Unity::Mathematics::int3::Construct_2lzDmp63Mfw__oFMy0HdgWw = reinterpret_cast<void (*)(::std::int32_t, ::std::int32_t, ::std::int32_t, ::DotNet::Unity::Mathematics::int3*, void**)>(functionPointers[1426]);
  ::DotNet::Unity::Mathematics::int3x3::Construct_A__Tj4TB5T_s22Xd4RW46Fg = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::int3*, const ::DotNet::Unity::Mathematics::int3*, const ::DotNet::Unity::Mathematics::int3*, ::DotNet::Unity::Mathematics::int3x3*, void**)>(functionPointers[1427]);
  ::DotNet::Unity::Mathematics::int4::Construct_ima1GH0lko9R2DnR_aRPyw = reinterpret_cast<void (*)(::std::int32_t, ::std::int32_t, ::std::int32_t, ::std::int32_t, ::DotNet::Unity::Mathematics::int4*, void**)>(functionPointers[1428]);
  ::DotNet::Unity::Mathematics::int4x4::Construct___u7bLaYK7NsvS7W3VaLQcw = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::int4*, const ::DotNet::Unity::Mathematics::int4*, const ::DotNet::Unity::Mathematics::int4*, const ::DotNet::Unity::Mathematics::int4*, ::DotNet::Unity::Mathematics::int4x4*, void**)>(functionPointers[1429]);
  ::DotNet::Unity::Mathematics::uint2::Construct_41DRfMZ91WmKUsGkzEnbPw = reinterpret_cast<void (*)(::std::uint32_t, ::std::uint32_t, ::DotNet::Unity::Mathematics::uint2*, void**)>(functionPointers[1430]);
  ::DotNet::Unity::Mathematics::uint2x2::Construct_P1cAnApbSLA3Xc3DztNMzw = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::uint2*, const ::DotNet::Unity::Mathematics::uint2*, ::DotNet::Unity::Mathematics::uint2x2*, void**)>(functionPointers[1431]);
  ::DotNet::Unity::Mathematics::uint3::Construct_fwI58ky8hlqSzCrUJCqq4Q = reinterpret_cast<void (*)(::std::uint32_t, ::std::uint32_t, ::std::uint32_t, ::DotNet::Unity::Mathematics::uint3*, void**)>(functionPointers[1432]);
  ::DotNet::Unity::Mathematics::uint3x3::Construct_ZtWpbr50zCN2kT2S7fwByQ = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::uint3*, const ::DotNet::Unity::Mathematics::uint3*, const ::DotNet::Unity::Mathematics::uint3*, ::DotNet::Unity::Mathematics::uint3x3*, void**)>(functionPointers[1433]);
  ::DotNet::Unity::Mathematics::uint4::Construct_cx5C8OyRaFgckdYoG5u6cw = reinterpret_cast<void (*)(::std::uint32_t, ::std::uint32_t, ::std::uint32_t, ::std::uint32_t, ::DotNet::Unity::Mathematics::uint4*, void**)>(functionPointers[1434]);
  ::DotNet::Unity::Mathematics::uint4x4::Construct_P__muY59YdYGI7W2ynF5sPw = reinterpret_cast<void (*)(const ::DotNet::Unity::Mathematics::uint4*, const ::DotNet::Unity::Mathematics::uint4*, const ::DotNet::Unity::Mathematics::uint4*, const ::DotNet::Unity::Mathematics::uint4*, ::DotNet::Unity::Mathematics::uint4x4*, void**)>(functionPointers[1435]);
  ::DotNet::UnityEditor::AssemblyReloadCallback::CallInvoke_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1436]);
  ::DotNet::UnityEditor::AssemblyReloadCallback::Callop_Equality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1437]);
  ::DotNet::UnityEditor::AssemblyReloadCallback::Callop_Equality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1438]);
  ::DotNet::UnityEditor::AssemblyReloadCallback::Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1439]);
  ::DotNet::UnityEditor::AssemblyReloadCallback::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1440]);
  ::DotNet::UnityEditor::AssemblyReloadCallback::CombineDelegates = reinterpret_cast<void* (*)(void*, void*)>(functionPointers[1441]);
  ::DotNet::UnityEditor::AssemblyReloadCallback::CreateDelegate = reinterpret_cast<void* (*)(void*)>(functionPointers[1442]);
  ::DotNet::UnityEditor::AssemblyReloadCallback::DisposeDelegate = reinterpret_cast<void (*)(void*)>(functionPointers[1443]);
  ::DotNet::UnityEditor::AssemblyReloadCallback::RemoveDelegate = reinterpret_cast<void* (*)(void*, void*)>(functionPointers[1444]);
  ::DotNet::UnityEditor::AssemblyReloadEvents::Calladd_afterAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1445]);
  ::DotNet::UnityEditor::AssemblyReloadEvents::Calladd_beforeAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1446]);
  ::DotNet::UnityEditor::AssemblyReloadEvents::Callremove_afterAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1447]);
  ::DotNet::UnityEditor::AssemblyReloadEvents::Callremove_beforeAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1448]);
  ::DotNet::UnityEditor::CallbackFunction::CallInvoke_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1449]);
  ::DotNet::UnityEditor::CallbackFunction::Callop_Equality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1450]);
  ::DotNet::UnityEditor::CallbackFunction::Callop_Equality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1451]);
  ::DotNet::UnityEditor::CallbackFunction::Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1452]);
  ::DotNet::UnityEditor::CallbackFunction::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1453]);
  ::DotNet::UnityEditor::CallbackFunction::CombineDelegates = reinterpret_cast<void* (*)(void*, void*)>(functionPointers[1454]);
  ::DotNet::UnityEditor::CallbackFunction::CreateDelegate = reinterpret_cast<void* (*)(void*)>(functionPointers[1455]);
  ::DotNet::UnityEditor::CallbackFunction::DisposeDelegate = reinterpret_cast<void (*)(void*)>(functionPointers[1456]);
  ::DotNet::UnityEditor::CallbackFunction::RemoveDelegate = reinterpret_cast<void* (*)(void*, void*)>(functionPointers[1457]);
  ::DotNet::UnityEditor::EditorApplication::CallExecuteMenuItem__mTAWffFaNJNxtE3VLYhxw = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1458]);
  ::DotNet::UnityEditor::EditorApplication::Field_get_update = reinterpret_cast<void* (*)(void** reinteropException)>(functionPointers[1459]);
  ::DotNet::UnityEditor::EditorApplication::Field_set_update = reinterpret_cast<void (*)(void* value, void** reinteropException)>(functionPointers[1460]);
  ::DotNet::UnityEditor::EditorApplication::Property_get_isPlaying = reinterpret_cast<::std::uint8_t (*)(void**)>(functionPointers[1461]);
  ::DotNet::UnityEditor::EditorApplication::Property_set_isPlaying = reinterpret_cast<void (*)(::std::uint8_t, void**)>(functionPointers[1462]);
  ::DotNet::UnityEditor::EditorPrefs::CallDeleteKey_4Oa4KGDR__vvaosUsC29xLg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1463]);
  ::DotNet::UnityEditor::EditorPrefs::CallGetString_4Oa4KGDR__vvaosUsC29xLg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1464]);
  ::DotNet::UnityEditor::EditorPrefs::CallHasKey_4Oa4KGDR__vvaosUsC29xLg = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1465]);
  ::DotNet::UnityEditor::EditorPrefs::CallSetString_eMSjpsyKrCDpoy__674Qaew = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1466]);
  ::DotNet::UnityEditor::EditorUtility::CallSetDirty_byPIQUdz9akDU2__zoHd1tg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1467]);
  ::DotNet::UnityEditor::EditorWindow::CallClose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1468]);
  ::DotNet::UnityEditor::EditorWindow::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1469]);
  ::DotNet::UnityEditor::EditorWindow::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1470]);
  ::DotNet::UnityEditor::EditorWindow::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1471]);
  ::DotNet::UnityEditor::EditorWindow::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1472]);
  ::DotNet::UnityEditor::EditorWindow::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1473]);
  ::DotNet::UnityEditor::EditorWindow::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1474]);
  ::DotNet::UnityEditor::EditorWindow::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1475]);
  ::DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader::CallIsSortedAscending_ZiJhFqE0LPDoV__RgQlNVpQ = reinterpret_cast<::std::uint8_t (*)(void*, ::std::int32_t, void**)>(functionPointers[1476]);
  ::DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader::Property_get_sortedColumnIndex = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1477]);
  ::DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader::Property_set_sortedColumnIndex = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1478]);
  ::DotNet::UnityEditor::IMGUI::Controls::TreeView::CallReload_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1479]);
  ::DotNet::UnityEditor::IMGUI::Controls::TreeView::Property_get_multiColumnHeader = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1480]);
  ::DotNet::UnityEditor::IMGUI::Controls::TreeView::Property_get_searchString = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1481]);
  ::DotNet::UnityEditor::IMGUI::Controls::TreeView::Property_set_multiColumnHeader = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1482]);
  ::DotNet::UnityEditor::IMGUI::Controls::TreeView::Property_set_searchString = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1483]);
  ::DotNet::UnityEditor::IMGUI::Controls::TreeViewItem::Construct_fAkE2H7EjTzReHiM2XHBPA = reinterpret_cast<void* (*)(::std::int32_t, ::std::int32_t, void*, void**)>(functionPointers[1484]);
  ::DotNet::UnityEditor::IMGUI::Controls::TreeViewItem::Property_get_id = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1485]);
  ::DotNet::UnityEditor::IMGUI::Controls::TreeViewItem::Property_set_id = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1486]);
  ::DotNet::UnityEditor::IMGUI::Controls::TreeViewState::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1487]);
  ::DotNet::UnityEditor::SceneView::CallClose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1488]);
  ::DotNet::UnityEditor::SceneView::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1489]);
  ::DotNet::UnityEditor::SceneView::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1490]);
  ::DotNet::UnityEditor::SceneView::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1491]);
  ::DotNet::UnityEditor::SceneView::Property_get_camera = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1492]);
  ::DotNet::UnityEditor::SceneView::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1493]);
  ::DotNet::UnityEditor::SceneView::Property_get_lastActiveSceneView = reinterpret_cast<void* (*)(void**)>(functionPointers[1494]);
  ::DotNet::UnityEditor::SceneView::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1495]);
  ::DotNet::UnityEditor::SceneView::Property_get_pivot = reinterpret_cast<void (*)(void*, ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1496]);
  ::DotNet::UnityEditor::SceneView::Property_get_rotation = reinterpret_cast<void (*)(void*, ::DotNet::UnityEngine::Quaternion*, void**)>(functionPointers[1497]);
  ::DotNet::UnityEditor::SceneView::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1498]);
  ::DotNet::UnityEditor::SceneView::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1499]);
  ::DotNet::UnityEditor::SceneView::Property_set_pivot = reinterpret_cast<void (*)(void*, const ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1500]);
  ::DotNet::UnityEditor::SceneView::Property_set_rotation = reinterpret_cast<void (*)(void*, const ::DotNet::UnityEngine::Quaternion*, void**)>(functionPointers[1501]);
  ::DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1502]);
  ::DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1503]);
  ::DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1504]);
  ::DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1505]);
  ::DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Property_get_instance = reinterpret_cast<void* (*)(void**)>(functionPointers[1506]);
  ::DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1507]);
  ::DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1508]);
  ::DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1509]);
  ::DotNet::UnityEditor::Selection::Property_get_activeGameObject = reinterpret_cast<void* (*)(void**)>(functionPointers[1510]);
  ::DotNet::UnityEditor::Selection::Property_set_activeGameObject = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1511]);
  ::DotNet::UnityEngine::Application::CallOpenURL_i4__FgVIR5VYHO4KBzPBwNQ = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1512]);
  ::DotNet::UnityEngine::Application::Property_get_isEditor = reinterpret_cast<::std::uint8_t (*)(void**)>(functionPointers[1513]);
  ::DotNet::UnityEngine::Application::Property_get_platform = reinterpret_cast<::std::uint32_t (*)(void**)>(functionPointers[1514]);
  ::DotNet::UnityEngine::Application::Property_get_productName = reinterpret_cast<void* (*)(void**)>(functionPointers[1515]);
  ::DotNet::UnityEngine::Application::Property_get_temporaryCachePath = reinterpret_cast<void* (*)(void**)>(functionPointers[1516]);
  ::DotNet::UnityEngine::Application::Property_get_unityVersion = reinterpret_cast<void* (*)(void**)>(functionPointers[1517]);
  ::DotNet::UnityEngine::Application::Property_get_version = reinterpret_cast<void* (*)(void**)>(functionPointers[1518]);
  ::DotNet::UnityEngine::AsyncOperation::Calladd_completed_89b__Riirtgd1Q5mmRzPojA = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1519]);
  ::DotNet::UnityEngine::AsyncOperation::Callremove_completed_89b__Riirtgd1Q5mmRzPojA = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1520]);
  ::DotNet::UnityEngine::Behaviour::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1521]);
  ::DotNet::UnityEngine::Behaviour::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1522]);
  ::DotNet::UnityEngine::Behaviour::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1523]);
  ::DotNet::UnityEngine::Behaviour::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1524]);
  ::DotNet::UnityEngine::Behaviour::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1525]);
  ::DotNet::UnityEngine::Behaviour::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1526]);
  ::DotNet::UnityEngine::Behaviour::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1527]);
  ::DotNet::UnityEngine::Behaviour::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1528]);
  ::DotNet::UnityEngine::Behaviour::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1529]);
  ::DotNet::UnityEngine::Behaviour::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1530]);
  ::DotNet::UnityEngine::Behaviour::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1531]);
  ::DotNet::UnityEngine::Behaviour::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1532]);
  ::DotNet::UnityEngine::Bounds::Construct_Qy9aU2ShAPtxkIq6r1DXbA = reinterpret_cast<void (*)(const ::DotNet::UnityEngine::Vector3*, const ::DotNet::UnityEngine::Vector3*, ::DotNet::UnityEngine::Bounds*, void**)>(functionPointers[1533]);
  ::DotNet::UnityEngine::Camera::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1534]);
  ::DotNet::UnityEngine::Camera::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1535]);
  ::DotNet::UnityEngine::Camera::CallGetStereoViewMatrix_tC0__sPPwO7__M2RD5oQtqig = reinterpret_cast<void (*)(void*, ::std::uint32_t, ::DotNet::UnityEngine::Matrix4x4*, void**)>(functionPointers[1536]);
  ::DotNet::UnityEngine::Camera::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1537]);
  ::DotNet::UnityEngine::Camera::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1538]);
  ::DotNet::UnityEngine::Camera::Property_get_aspect = reinterpret_cast<float (*)(void*, void**)>(functionPointers[1539]);
  ::DotNet::UnityEngine::Camera::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1540]);
  ::DotNet::UnityEngine::Camera::Property_get_fieldOfView = reinterpret_cast<float (*)(void*, void**)>(functionPointers[1541]);
  ::DotNet::UnityEngine::Camera::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1542]);
  ::DotNet::UnityEngine::Camera::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1543]);
  ::DotNet::UnityEngine::Camera::Property_get_main = reinterpret_cast<void* (*)(void**)>(functionPointers[1544]);
  ::DotNet::UnityEngine::Camera::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1545]);
  ::DotNet::UnityEngine::Camera::Property_get_orthographic = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1546]);
  ::DotNet::UnityEngine::Camera::Property_get_orthographicSize = reinterpret_cast<float (*)(void*, void**)>(functionPointers[1547]);
  ::DotNet::UnityEngine::Camera::Property_get_pixelHeight = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1548]);
  ::DotNet::UnityEngine::Camera::Property_get_pixelWidth = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1549]);
  ::DotNet::UnityEngine::Camera::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1550]);
  ::DotNet::UnityEngine::Camera::Property_set_aspect = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[1551]);
  ::DotNet::UnityEngine::Camera::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1552]);
  ::DotNet::UnityEngine::Camera::Property_set_fieldOfView = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[1553]);
  ::DotNet::UnityEngine::Camera::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1554]);
  ::DotNet::UnityEngine::Camera::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1555]);
  ::DotNet::UnityEngine::Camera::Property_set_orthographic = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1556]);
  ::DotNet::UnityEngine::Camera::Property_set_orthographicSize = reinterpret_cast<void (*)(void*, float, void**)>(functionPointers[1557]);
  ::DotNet::UnityEngine::Component::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1558]);
  ::DotNet::UnityEngine::Component::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1559]);
  ::DotNet::UnityEngine::Component::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1560]);
  ::DotNet::UnityEngine::Component::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1561]);
  ::DotNet::UnityEngine::Component::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1562]);
  ::DotNet::UnityEngine::Component::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1563]);
  ::DotNet::UnityEngine::Component::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1564]);
  ::DotNet::UnityEngine::Component::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1565]);
  ::DotNet::UnityEngine::Component::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1566]);
  ::DotNet::UnityEngine::Component::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1567]);
  ::DotNet::UnityEngine::Debug::CallLog_FA05wu8x__otZNsgdHTnU9A = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1568]);
  ::DotNet::UnityEngine::Debug::CallLogError_FA05wu8x__otZNsgdHTnU9A = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1569]);
  ::DotNet::UnityEngine::Debug::CallLogWarning_FA05wu8x__otZNsgdHTnU9A = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1570]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_0EgxpGTzCG1YTfWqwgLniw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1571]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_9Dl3F62kv4jRdRrSCaAhWg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1572]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_BAtcoWNWVoAVplmna6OgsQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1573]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_bqVePTBqqV2QqVo4ESth7Q = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1574]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_cgILpkZPip9MNREZc7j5sA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1575]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_jKezPd1C5klHWmgOl3TpSg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1576]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_kHO1FlHzBtTx__KiumABg0g = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1577]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_NF_PuZoAY7qn_PtfB0gOuA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1578]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_NuZsWWrRz5eMwjHbcVsVwA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1579]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_PYIqvoB6xIJFucZLpuXW4g = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1580]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1581]);
  ::DotNet::UnityEngine::GameObject::CallAddComponent_z_rdtaHehbYFGG7_o6BG8A = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1582]);
  ::DotNet::UnityEngine::GameObject::CallFindGameObjectsWithTag_X3GzO_w9lbBwSL5__E4yHEA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1583]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_0EgxpGTzCG1YTfWqwgLniw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1584]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_6Whoj_6qM2__sUah3I8fbaA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1585]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_a430lQ0omIr32Y9qAs_Zdw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1586]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_BAtcoWNWVoAVplmna6OgsQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1587]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_bqVePTBqqV2QqVo4ESth7Q = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1588]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_ceANxxBRdEpPcfCIAtIDbw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1589]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_cgILpkZPip9MNREZc7j5sA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1590]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_D9Lae__zo_r27FE__dPPON_Q = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1591]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_H1UZCBm__Pf6NnqpE7xQ8NQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1592]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_h3Dg1fHhPAsIOJVZ_EBQ0Q = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1593]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_Is4miIX63ogCDpU56JfOjw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1594]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_kHO1FlHzBtTx__KiumABg0g = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1595]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_NF_PuZoAY7qn_PtfB0gOuA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1596]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_PYIqvoB6xIJFucZLpuXW4g = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1597]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1598]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_xszYH1Pc7IFeB_VsZOpLAg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1599]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_xv03rkZpw_Znk_k8us1wKw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1600]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_z_rdtaHehbYFGG7_o6BG8A = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1601]);
  ::DotNet::UnityEngine::GameObject::CallGetComponent_zSXCS__EpLjNvbypxgiLwTw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1602]);
  ::DotNet::UnityEngine::GameObject::CallGetComponentInParent_bqVePTBqqV2QqVo4ESth7Q = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1603]);
  ::DotNet::UnityEngine::GameObject::CallGetComponentInParent_cgILpkZPip9MNREZc7j5sA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1604]);
  ::DotNet::UnityEngine::GameObject::CallGetComponents_BAtcoWNWVoAVplmna6OgsQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1605]);
  ::DotNet::UnityEngine::GameObject::CallGetComponents_H1UZCBm__Pf6NnqpE7xQ8NQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1606]);
  ::DotNet::UnityEngine::GameObject::CallGetComponentsInChildren_0EgxpGTzCG1YTfWqwgLniw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1607]);
  ::DotNet::UnityEngine::GameObject::CallGetComponentsInChildren_STJODArO5i8B0kejx7otTA = reinterpret_cast<void* (*)(void*, ::std::uint8_t, void**)>(functionPointers[1608]);
  ::DotNet::UnityEngine::GameObject::CallGetComponentsInChildren_z_rdtaHehbYFGG7_o6BG8A = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1609]);
  ::DotNet::UnityEngine::GameObject::CallGetComponentsInParent_5cYXJenC2831by5N6skAPw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1610]);
  ::DotNet::UnityEngine::GameObject::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1611]);
  ::DotNet::UnityEngine::GameObject::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1612]);
  ::DotNet::UnityEngine::GameObject::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1613]);
  ::DotNet::UnityEngine::GameObject::CallSetActive_5DHWh79LLGX72UsSrgy12Q = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1614]);
  ::DotNet::UnityEngine::GameObject::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1615]);
  ::DotNet::UnityEngine::GameObject::Construct_wfPSjxsETIcebv8un8PGZw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1616]);
  ::DotNet::UnityEngine::GameObject::Property_get_activeInHierarchy = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1617]);
  ::DotNet::UnityEngine::GameObject::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1618]);
  ::DotNet::UnityEngine::GameObject::Property_get_layer = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1619]);
  ::DotNet::UnityEngine::GameObject::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1620]);
  ::DotNet::UnityEngine::GameObject::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1621]);
  ::DotNet::UnityEngine::GameObject::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1622]);
  ::DotNet::UnityEngine::GameObject::Property_set_layer = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1623]);
  ::DotNet::UnityEngine::GameObject::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1624]);
  ::DotNet::UnityEngine::GUI::CallLabel_iRU7t71QqJzkr4BTYehN9A = reinterpret_cast<void (*)(const ::DotNet::UnityEngine::Rect*, void*, void**)>(functionPointers[1625]);
  ::DotNet::UnityEngine::Material::CallComputeCRC_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1626]);
  ::DotNet::UnityEngine::Material::CallDisableKeyword_OjhTXlNYqXjpgz6Nd_41__A = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1627]);
  ::DotNet::UnityEngine::Material::CallEnableKeyword_OjhTXlNYqXjpgz6Nd_41__A = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1628]);
  ::DotNet::UnityEngine::Material::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1629]);
  ::DotNet::UnityEngine::Material::CallGetTexture_FH4N7HzmeU2VNRINVzNxBQ = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1630]);
  ::DotNet::UnityEngine::Material::CallGetTexturePropertyNameIDs_HlbsadfaizcXlyyoqQEA3Q = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1631]);
  ::DotNet::UnityEngine::Material::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1632]);
  ::DotNet::UnityEngine::Material::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1633]);
  ::DotNet::UnityEngine::Material::CallSetFloat_D__nDm70ZmOnS4ff1jXmV2g = reinterpret_cast<void (*)(void*, ::std::int32_t, float, void**)>(functionPointers[1634]);
  ::DotNet::UnityEngine::Material::CallSetTexture_RautZzWeb93ejEP2lTHyaQ = reinterpret_cast<void (*)(void*, ::std::int32_t, void*, void**)>(functionPointers[1635]);
  ::DotNet::UnityEngine::Material::CallSetTextureOffset_ZCDR2hJmAGOF0Xsc__aBBJA = reinterpret_cast<void (*)(void*, ::std::int32_t, const ::DotNet::UnityEngine::Vector2*, void**)>(functionPointers[1636]);
  ::DotNet::UnityEngine::Material::CallSetTextureScale_ZCDR2hJmAGOF0Xsc__aBBJA = reinterpret_cast<void (*)(void*, ::std::int32_t, const ::DotNet::UnityEngine::Vector2*, void**)>(functionPointers[1637]);
  ::DotNet::UnityEngine::Material::CallSetVector_O_6hMsPoe8Mxh6B7ktm1dw = reinterpret_cast<void (*)(void*, ::std::int32_t, const ::DotNet::UnityEngine::Vector4*, void**)>(functionPointers[1638]);
  ::DotNet::UnityEngine::Material::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1639]);
  ::DotNet::UnityEngine::Material::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1640]);
  ::DotNet::UnityEngine::Material::Property_get_shader = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1641]);
  ::DotNet::UnityEngine::Material::Property_get_shaderKeywords = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1642]);
  ::DotNet::UnityEngine::Material::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1643]);
  ::DotNet::UnityEngine::Material::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1644]);
  ::DotNet::UnityEngine::Material::Property_set_shader = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1645]);
  ::DotNet::UnityEngine::Material::Property_set_shaderKeywords = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1646]);
  ::DotNet::UnityEngine::Matrix4x4::CallMultiplyPoint3x4_nRoP5wpLbrdr_ZZudXtbFA = reinterpret_cast<void (*)(const ::DotNet::UnityEngine::Matrix4x4*, const ::DotNet::UnityEngine::Vector3*, ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1647]);
  ::DotNet::UnityEngine::Mesh::CallAllocateWritableMeshData_a7RdxWIDVq3m4GTzSAxtDw = reinterpret_cast<void* (*)(::std::int32_t, void**)>(functionPointers[1648]);
  ::DotNet::UnityEngine::Mesh::CallApplyAndDisposeWritableMeshData_K7gsr9XXVwYV61pKjp0Flw = reinterpret_cast<void (*)(void*, void*, ::std::uint32_t, void**)>(functionPointers[1649]);
  ::DotNet::UnityEngine::Mesh::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1650]);
  ::DotNet::UnityEngine::Mesh::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1651]);
  ::DotNet::UnityEngine::Mesh::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1652]);
  ::DotNet::UnityEngine::Mesh::CallRecalculateBounds_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1653]);
  ::DotNet::UnityEngine::Mesh::CallSetIndices_ojn8dGiQbch02RdGWlLnpA = reinterpret_cast<void (*)(void*, void*, ::std::uint32_t, ::std::int32_t, ::std::uint8_t, ::std::int32_t, void**)>(functionPointers[1654]);
  ::DotNet::UnityEngine::Mesh::CallSetNormals_Jwfug4VcNnAHDEO5Mr1VPQ = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1655]);
  ::DotNet::UnityEngine::Mesh::CallSetUVs_xhGznZ6iubWLgUmOC8daog = reinterpret_cast<void (*)(void*, ::std::int32_t, void*, void**)>(functionPointers[1656]);
  ::DotNet::UnityEngine::Mesh::CallSetVertices_8SVQMDrqHKz8KuxxeLnZAw = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1657]);
  ::DotNet::UnityEngine::Mesh::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1658]);
  ::DotNet::UnityEngine::Mesh::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1659]);
  ::DotNet::UnityEngine::Mesh::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1660]);
  ::DotNet::UnityEngine::Mesh::Property_get_vertexCount = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1661]);
  ::DotNet::UnityEngine::Mesh::Property_get_vertices = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1662]);
  ::DotNet::UnityEngine::Mesh::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1663]);
  ::DotNet::UnityEngine::Mesh::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1664]);
  ::DotNet::UnityEngine::Mesh::Property_set_vertices = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1665]);
  ::DotNet::UnityEngine::MeshCollider::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1666]);
  ::DotNet::UnityEngine::MeshCollider::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1667]);
  ::DotNet::UnityEngine::MeshCollider::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1668]);
  ::DotNet::UnityEngine::MeshCollider::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1669]);
  ::DotNet::UnityEngine::MeshCollider::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1670]);
  ::DotNet::UnityEngine::MeshCollider::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1671]);
  ::DotNet::UnityEngine::MeshCollider::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1672]);
  ::DotNet::UnityEngine::MeshCollider::Property_get_sharedMesh = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1673]);
  ::DotNet::UnityEngine::MeshCollider::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1674]);
  ::DotNet::UnityEngine::MeshCollider::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1675]);
  ::DotNet::UnityEngine::MeshCollider::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1676]);
  ::DotNet::UnityEngine::MeshCollider::Property_set_sharedMesh = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1677]);
  ::DotNet::UnityEngine::MeshData::CallGetIndexData_Ce46szGfJ6vmevqnTM9T9A = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1678]);
  ::DotNet::UnityEngine::MeshData::CallGetIndexData_YAIddHPxvLNUfgMxRDxChw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1679]);
  ::DotNet::UnityEngine::MeshData::CallGetVertexData__7GtY91GOoYBBL6__e7IK3g = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1680]);
  ::DotNet::UnityEngine::MeshData::CallGetVertexData_5pXb_vZ42FUJBb__NBZAGDQ = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1681]);
  ::DotNet::UnityEngine::MeshData::CallGetVertexData_dyQZuDnE0veN17wSKpECqg = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1682]);
  ::DotNet::UnityEngine::MeshData::CallSetIndexBufferParams_33DrxW_6gBzitFJX1cCsNw = reinterpret_cast<void (*)(void*, ::std::int32_t, ::std::uint32_t, void**)>(functionPointers[1683]);
  ::DotNet::UnityEngine::MeshData::CallSetSubMesh_UefU0znm5VK66Qs__Aa2BMQ = reinterpret_cast<void (*)(void*, ::std::int32_t, const ::DotNet::UnityEngine::Rendering::SubMeshDescriptor*, ::std::uint32_t, void**)>(functionPointers[1684]);
  ::DotNet::UnityEngine::MeshData::CallSetVertexBufferParams_rY4e33oFKB7g68Q__VYd3ZA = reinterpret_cast<void (*)(void*, ::std::int32_t, void*, void**)>(functionPointers[1685]);
  ::DotNet::UnityEngine::MeshData::Property_get_subMeshCount = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1686]);
  ::DotNet::UnityEngine::MeshData::Property_set_subMeshCount = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1687]);
  ::DotNet::UnityEngine::MeshDataArray::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1688]);
  ::DotNet::UnityEngine::MeshDataArray::Property_get_Item = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1689]);
  ::DotNet::UnityEngine::MeshDataArray::Property_get_Length = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1690]);
  ::DotNet::UnityEngine::MeshFilter::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1691]);
  ::DotNet::UnityEngine::MeshFilter::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1692]);
  ::DotNet::UnityEngine::MeshFilter::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1693]);
  ::DotNet::UnityEngine::MeshFilter::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1694]);
  ::DotNet::UnityEngine::MeshFilter::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1695]);
  ::DotNet::UnityEngine::MeshFilter::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1696]);
  ::DotNet::UnityEngine::MeshFilter::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1697]);
  ::DotNet::UnityEngine::MeshFilter::Property_get_mesh = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1698]);
  ::DotNet::UnityEngine::MeshFilter::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1699]);
  ::DotNet::UnityEngine::MeshFilter::Property_get_sharedMesh = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1700]);
  ::DotNet::UnityEngine::MeshFilter::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1701]);
  ::DotNet::UnityEngine::MeshFilter::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1702]);
  ::DotNet::UnityEngine::MeshFilter::Property_set_mesh = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1703]);
  ::DotNet::UnityEngine::MeshFilter::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1704]);
  ::DotNet::UnityEngine::MeshFilter::Property_set_sharedMesh = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1705]);
  ::DotNet::UnityEngine::MeshRenderer::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1706]);
  ::DotNet::UnityEngine::MeshRenderer::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1707]);
  ::DotNet::UnityEngine::MeshRenderer::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1708]);
  ::DotNet::UnityEngine::MeshRenderer::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1709]);
  ::DotNet::UnityEngine::MeshRenderer::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void**)>(functionPointers[1710]);
  ::DotNet::UnityEngine::MeshRenderer::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1711]);
  ::DotNet::UnityEngine::MeshRenderer::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1712]);
  ::DotNet::UnityEngine::MeshRenderer::Property_get_material = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1713]);
  ::DotNet::UnityEngine::MeshRenderer::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1714]);
  ::DotNet::UnityEngine::MeshRenderer::Property_get_sharedMaterial = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1715]);
  ::DotNet::UnityEngine::MeshRenderer::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1716]);
  ::DotNet::UnityEngine::MeshRenderer::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1717]);
  ::DotNet::UnityEngine::MeshRenderer::Property_set_material = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1718]);
  ::DotNet::UnityEngine::MeshRenderer::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1719]);
  ::DotNet::UnityEngine::MeshRenderer::Property_set_sharedMaterial = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1720]);
  ::DotNet::UnityEngine::MonoBehaviour::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1721]);
  ::DotNet::UnityEngine::MonoBehaviour::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1722]);
  ::DotNet::UnityEngine::MonoBehaviour::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1723]);
  ::DotNet::UnityEngine::MonoBehaviour::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1724]);
  ::DotNet::UnityEngine::MonoBehaviour::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[1725]);
  ::DotNet::UnityEngine::MonoBehaviour::Property_get_enabled = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1726]);
  ::DotNet::UnityEngine::MonoBehaviour::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1727]);
  ::DotNet::UnityEngine::MonoBehaviour::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1728]);
  ::DotNet::UnityEngine::MonoBehaviour::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1729]);
  ::DotNet::UnityEngine::MonoBehaviour::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1730]);
  ::DotNet::UnityEngine::MonoBehaviour::Property_set_enabled = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1731]);
  ::DotNet::UnityEngine::MonoBehaviour::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1732]);
  ::DotNet::UnityEngine::MonoBehaviour::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1733]);
  ::DotNet::UnityEngine::Networking::DownloadHandler::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1734]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::CallAbort_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1735]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1736]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::CallGet_Y2__l4HVQ8CbSg4jpXDip9A = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1737]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::CallGetResponseHeader_wfPSjxsETIcebv8un8PGZw = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[1738]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::CallGetResponseHeaders_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1739]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::CallSendWebRequest_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1740]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::CallSetRequestHeader_tEfBle3aSdR47_HxLakNjw = reinterpret_cast<void (*)(void*, void*, void*, void**)>(functionPointers[1741]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::Construct_N5nF6s7__PflIcgtgQgj6DA = reinterpret_cast<void* (*)(void*, void*, void*, void*, void**)>(functionPointers[1742]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_downloadHandler = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1743]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_error = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1744]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_isDone = reinterpret_cast<::std::uint8_t (*)(void*, void**)>(functionPointers[1745]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_method = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1746]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_responseCode = reinterpret_cast<::std::int64_t (*)(void*, void**)>(functionPointers[1747]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_result = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1748]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_url = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1749]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::Property_set_downloadHandler = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1750]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::Property_set_method = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1751]);
  ::DotNet::UnityEngine::Networking::UnityWebRequest::Property_set_url = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1752]);
  ::DotNet::UnityEngine::Networking::UnityWebRequestAsyncOperation::Calladd_completed_89b__Riirtgd1Q5mmRzPojA = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1753]);
  ::DotNet::UnityEngine::Networking::UnityWebRequestAsyncOperation::Callremove_completed_89b__Riirtgd1Q5mmRzPojA = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1754]);
  ::DotNet::UnityEngine::Networking::UnityWebRequestTexture::CallGetTexture_Y2__l4HVQ8CbSg4jpXDip9A = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1755]);
  ::DotNet::UnityEngine::Networking::UploadHandlerRaw::Construct_j9VUe_obWzqxHm0yKnVCmg = reinterpret_cast<void* (*)(void*, ::std::uint8_t, void**)>(functionPointers[1756]);
  ::DotNet::UnityEngine::Networking::UploadHandlerRaw::Construct_Wn8TTeG3Q36ufSfvO3m1sg = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1757]);
  ::DotNet::UnityEngine::Object::CallDestroy_x7aQMuJcEpatC9689ghI4A = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1758]);
  ::DotNet::UnityEngine::Object::CallDestroyImmediate_c5oFMRh3nzKMIo8On83YBg = reinterpret_cast<void (*)(void*, ::std::uint8_t, void**)>(functionPointers[1759]);
  ::DotNet::UnityEngine::Object::CallDestroyImmediate_x7aQMuJcEpatC9689ghI4A = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1760]);
  ::DotNet::UnityEngine::Object::CallFindObjectsOfType_0EgxpGTzCG1YTfWqwgLniw = reinterpret_cast<void* (*)(void**)>(functionPointers[1761]);
  ::DotNet::UnityEngine::Object::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1762]);
  ::DotNet::UnityEngine::Object::CallInstantiate_FQyuyLH6iz8rpKkiJwlxBA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1763]);
  ::DotNet::UnityEngine::Object::CallInstantiate_zoaJbce7UThbChk6y9FLqQ = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1764]);
  ::DotNet::UnityEngine::Object::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1765]);
  ::DotNet::UnityEngine::Object::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1766]);
  ::DotNet::UnityEngine::Object::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1767]);
  ::DotNet::UnityEngine::Object::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1768]);
  ::DotNet::UnityEngine::Object::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1769]);
  ::DotNet::UnityEngine::Object::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1770]);
  ::DotNet::UnityEngine::Physics::CallBakeMesh_dUTFInDZC08B3wpYvm01lw = reinterpret_cast<void (*)(::std::int32_t, ::std::uint8_t, void**)>(functionPointers[1771]);
  ::DotNet::UnityEngine::Quaternion::CallLookRotation_7YsCImhRrFIh_6hqa__5IAQ = reinterpret_cast<void (*)(const ::DotNet::UnityEngine::Vector3*, const ::DotNet::UnityEngine::Vector3*, ::DotNet::UnityEngine::Quaternion*, void**)>(functionPointers[1772]);
  ::DotNet::UnityEngine::Quaternion::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(::DotNet::UnityEngine::Quaternion*, void**)>(functionPointers[1773]);
  ::DotNet::UnityEngine::RaycastHit::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(::DotNet::UnityEngine::RaycastHit*, void**)>(functionPointers[1774]);
  ::DotNet::UnityEngine::RaycastHit::Property_get_point = reinterpret_cast<void (*)(const ::DotNet::UnityEngine::RaycastHit*, ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1775]);
  ::DotNet::UnityEngine::RaycastHit::Property_get_transform = reinterpret_cast<void* (*)(const ::DotNet::UnityEngine::RaycastHit*, void**)>(functionPointers[1776]);
  ::DotNet::UnityEngine::RaycastHit::Property_get_triangleIndex = reinterpret_cast<::std::int32_t (*)(const ::DotNet::UnityEngine::RaycastHit*, void**)>(functionPointers[1777]);
  ::DotNet::UnityEngine::RaycastHit::Property_set_point = reinterpret_cast<void (*)(const ::DotNet::UnityEngine::RaycastHit*, const ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1778]);
  ::DotNet::UnityEngine::Rect::Construct_SWzoP__nNh7g2zNwjI5mUvQ = reinterpret_cast<void (*)(float, float, float, float, ::DotNet::UnityEngine::Rect*, void**)>(functionPointers[1779]);
  ::DotNet::UnityEngine::Renderer::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1780]);
  ::DotNet::UnityEngine::Renderer::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1781]);
  ::DotNet::UnityEngine::Renderer::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1782]);
  ::DotNet::UnityEngine::Renderer::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1783]);
  ::DotNet::UnityEngine::Renderer::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1784]);
  ::DotNet::UnityEngine::Renderer::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1785]);
  ::DotNet::UnityEngine::Renderer::Property_get_material = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1786]);
  ::DotNet::UnityEngine::Renderer::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1787]);
  ::DotNet::UnityEngine::Renderer::Property_get_sharedMaterial = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1788]);
  ::DotNet::UnityEngine::Renderer::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1789]);
  ::DotNet::UnityEngine::Renderer::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1790]);
  ::DotNet::UnityEngine::Renderer::Property_set_material = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1791]);
  ::DotNet::UnityEngine::Renderer::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1792]);
  ::DotNet::UnityEngine::Renderer::Property_set_sharedMaterial = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1793]);
  ::DotNet::UnityEngine::Rendering::SubMeshDescriptor::Construct_hVqvzF5fyHzN08NI0LUuIw = reinterpret_cast<void (*)(::std::int32_t, ::std::int32_t, ::std::uint32_t, ::DotNet::UnityEngine::Rendering::SubMeshDescriptor*, void**)>(functionPointers[1794]);
  ::DotNet::UnityEngine::Resources::CallLoad_rsjQbSk78vk9BZ1CvfZ2fw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1795]);
  ::DotNet::UnityEngine::Resources::CallLoad_Sx8S__RAskKFDmQvk60XduA = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1796]);
  ::DotNet::UnityEngine::SceneManagement::Scene::CallGetRootGameObjects_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void* (*)(const ::DotNet::UnityEngine::SceneManagement::Scene*, void**)>(functionPointers[1797]);
  ::DotNet::UnityEngine::SceneManagement::SceneManager::CallGetSceneAt_7IHapUgMd7RT8__gH__cKUrw = reinterpret_cast<void (*)(::std::int32_t, ::DotNet::UnityEngine::SceneManagement::Scene*, void**)>(functionPointers[1798]);
  ::DotNet::UnityEngine::SceneManagement::SceneManager::Property_get_sceneCount = reinterpret_cast<::std::int32_t (*)(void**)>(functionPointers[1799]);
  ::DotNet::UnityEngine::Shader::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1800]);
  ::DotNet::UnityEngine::Shader::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1801]);
  ::DotNet::UnityEngine::Shader::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1802]);
  ::DotNet::UnityEngine::Shader::CallPropertyToID_wfPSjxsETIcebv8un8PGZw = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1803]);
  ::DotNet::UnityEngine::Shader::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1804]);
  ::DotNet::UnityEngine::Shader::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1805]);
  ::DotNet::UnityEngine::Shader::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1806]);
  ::DotNet::UnityEngine::Shader::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1807]);
  ::DotNet::UnityEngine::SystemInfo::CallIsFormatSupported_DuaX37kfZJZ9DeCzoZGKPA = reinterpret_cast<::std::uint8_t (*)(::std::uint32_t, ::std::uint32_t, void**)>(functionPointers[1808]);
  ::DotNet::UnityEngine::Texture::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1809]);
  ::DotNet::UnityEngine::Texture::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1810]);
  ::DotNet::UnityEngine::Texture::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1811]);
  ::DotNet::UnityEngine::Texture::Property_get_anisoLevel = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1812]);
  ::DotNet::UnityEngine::Texture::Property_get_filterMode = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1813]);
  ::DotNet::UnityEngine::Texture::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1814]);
  ::DotNet::UnityEngine::Texture::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1815]);
  ::DotNet::UnityEngine::Texture::Property_get_wrapMode = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1816]);
  ::DotNet::UnityEngine::Texture::Property_get_wrapModeU = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1817]);
  ::DotNet::UnityEngine::Texture::Property_get_wrapModeV = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1818]);
  ::DotNet::UnityEngine::Texture::Property_get_wrapModeW = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1819]);
  ::DotNet::UnityEngine::Texture::Property_set_anisoLevel = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1820]);
  ::DotNet::UnityEngine::Texture::Property_set_filterMode = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1821]);
  ::DotNet::UnityEngine::Texture::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1822]);
  ::DotNet::UnityEngine::Texture::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1823]);
  ::DotNet::UnityEngine::Texture::Property_set_wrapMode = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1824]);
  ::DotNet::UnityEngine::Texture::Property_set_wrapModeU = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1825]);
  ::DotNet::UnityEngine::Texture::Property_set_wrapModeV = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1826]);
  ::DotNet::UnityEngine::Texture::Property_set_wrapModeW = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1827]);
  ::DotNet::UnityEngine::Texture2D::CallApply_FZiaA8ur57jmvHTqox9Bng = reinterpret_cast<void (*)(void*, ::std::uint8_t, ::std::uint8_t, void**)>(functionPointers[1828]);
  ::DotNet::UnityEngine::Texture2D::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1829]);
  ::DotNet::UnityEngine::Texture2D::CallGetRawTextureData_z79ECk55IqLfMIqXBYg_8w = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1830]);
  ::DotNet::UnityEngine::Texture2D::CallLoadRawTextureData_C8JeOQhDs2O3mbZ4aC21YA = reinterpret_cast<void (*)(void*, void*, ::std::int32_t, void**)>(functionPointers[1831]);
  ::DotNet::UnityEngine::Texture2D::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1832]);
  ::DotNet::UnityEngine::Texture2D::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1833]);
  ::DotNet::UnityEngine::Texture2D::Construct_7_RAqfRCmreonOQ53TO4Og = reinterpret_cast<void* (*)(::std::int32_t, ::std::int32_t, ::std::uint32_t, ::std::uint8_t, ::std::uint8_t, void**)>(functionPointers[1834]);
  ::DotNet::UnityEngine::Texture2D::Construct_IFL2bOqlLrYHuwg5z0d8Cg = reinterpret_cast<void* (*)(::std::int32_t, ::std::int32_t, ::std::uint32_t, ::std::int32_t, ::std::uint8_t, void**)>(functionPointers[1835]);
  ::DotNet::UnityEngine::Texture2D::Property_get_anisoLevel = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1836]);
  ::DotNet::UnityEngine::Texture2D::Property_get_filterMode = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1837]);
  ::DotNet::UnityEngine::Texture2D::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1838]);
  ::DotNet::UnityEngine::Texture2D::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1839]);
  ::DotNet::UnityEngine::Texture2D::Property_get_wrapMode = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1840]);
  ::DotNet::UnityEngine::Texture2D::Property_get_wrapModeU = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1841]);
  ::DotNet::UnityEngine::Texture2D::Property_get_wrapModeV = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1842]);
  ::DotNet::UnityEngine::Texture2D::Property_get_wrapModeW = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1843]);
  ::DotNet::UnityEngine::Texture2D::Property_set_anisoLevel = reinterpret_cast<void (*)(void*, ::std::int32_t, void**)>(functionPointers[1844]);
  ::DotNet::UnityEngine::Texture2D::Property_set_filterMode = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1845]);
  ::DotNet::UnityEngine::Texture2D::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1846]);
  ::DotNet::UnityEngine::Texture2D::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1847]);
  ::DotNet::UnityEngine::Texture2D::Property_set_wrapMode = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1848]);
  ::DotNet::UnityEngine::Texture2D::Property_set_wrapModeU = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1849]);
  ::DotNet::UnityEngine::Texture2D::Property_set_wrapModeV = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1850]);
  ::DotNet::UnityEngine::Texture2D::Property_set_wrapModeW = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1851]);
  ::DotNet::UnityEngine::Time::Property_get_deltaTime = reinterpret_cast<float (*)(void**)>(functionPointers[1852]);
  ::DotNet::UnityEngine::Time::Property_get_frameCount = reinterpret_cast<::std::int32_t (*)(void**)>(functionPointers[1853]);
  ::DotNet::UnityEngine::Transform::CallDetachChildren_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(void*, void**)>(functionPointers[1854]);
  ::DotNet::UnityEngine::Transform::CallFind_huUPHg6iWoosrHfTvsoHeg = reinterpret_cast<void* (*)(void*, void*, void**)>(functionPointers[1855]);
  ::DotNet::UnityEngine::Transform::CallGetChild_7IHapUgMd7RT8__gH__cKUrw = reinterpret_cast<void* (*)(void*, ::std::int32_t, void**)>(functionPointers[1856]);
  ::DotNet::UnityEngine::Transform::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1857]);
  ::DotNet::UnityEngine::Transform::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1858]);
  ::DotNet::UnityEngine::Transform::CallGetSiblingIndex_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1859]);
  ::DotNet::UnityEngine::Transform::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1860]);
  ::DotNet::UnityEngine::Transform::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg = reinterpret_cast<::std::uint8_t (*)(void*, void*, void**)>(functionPointers[1861]);
  ::DotNet::UnityEngine::Transform::CallSetParent_hgOrrPUZTaGMovRxlX__YuA = reinterpret_cast<void (*)(void*, void*, ::std::uint8_t, void**)>(functionPointers[1862]);
  ::DotNet::UnityEngine::Transform::CallSetPositionAndRotation_4iSLIQZf65unfXZMWTVccw = reinterpret_cast<void (*)(void*, const ::DotNet::UnityEngine::Vector3*, const ::DotNet::UnityEngine::Quaternion*, void**)>(functionPointers[1863]);
  ::DotNet::UnityEngine::Transform::Property_get_childCount = reinterpret_cast<::std::int32_t (*)(void*, void**)>(functionPointers[1864]);
  ::DotNet::UnityEngine::Transform::Property_get_forward = reinterpret_cast<void (*)(void*, ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1865]);
  ::DotNet::UnityEngine::Transform::Property_get_gameObject = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1866]);
  ::DotNet::UnityEngine::Transform::Property_get_hideFlags = reinterpret_cast<::std::uint32_t (*)(void*, void**)>(functionPointers[1867]);
  ::DotNet::UnityEngine::Transform::Property_get_localPosition = reinterpret_cast<void (*)(void*, ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1868]);
  ::DotNet::UnityEngine::Transform::Property_get_localRotation = reinterpret_cast<void (*)(void*, ::DotNet::UnityEngine::Quaternion*, void**)>(functionPointers[1869]);
  ::DotNet::UnityEngine::Transform::Property_get_localScale = reinterpret_cast<void (*)(void*, ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1870]);
  ::DotNet::UnityEngine::Transform::Property_get_localToWorldMatrix = reinterpret_cast<void (*)(void*, ::DotNet::UnityEngine::Matrix4x4*, void**)>(functionPointers[1871]);
  ::DotNet::UnityEngine::Transform::Property_get_name = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1872]);
  ::DotNet::UnityEngine::Transform::Property_get_parent = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1873]);
  ::DotNet::UnityEngine::Transform::Property_get_position = reinterpret_cast<void (*)(void*, ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1874]);
  ::DotNet::UnityEngine::Transform::Property_get_root = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1875]);
  ::DotNet::UnityEngine::Transform::Property_get_rotation = reinterpret_cast<void (*)(void*, ::DotNet::UnityEngine::Quaternion*, void**)>(functionPointers[1876]);
  ::DotNet::UnityEngine::Transform::Property_get_transform = reinterpret_cast<void* (*)(void*, void**)>(functionPointers[1877]);
  ::DotNet::UnityEngine::Transform::Property_get_up = reinterpret_cast<void (*)(void*, ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1878]);
  ::DotNet::UnityEngine::Transform::Property_get_worldToLocalMatrix = reinterpret_cast<void (*)(void*, ::DotNet::UnityEngine::Matrix4x4*, void**)>(functionPointers[1879]);
  ::DotNet::UnityEngine::Transform::Property_set_forward = reinterpret_cast<void (*)(void*, const ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1880]);
  ::DotNet::UnityEngine::Transform::Property_set_hideFlags = reinterpret_cast<void (*)(void*, ::std::uint32_t, void**)>(functionPointers[1881]);
  ::DotNet::UnityEngine::Transform::Property_set_localPosition = reinterpret_cast<void (*)(void*, const ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1882]);
  ::DotNet::UnityEngine::Transform::Property_set_localRotation = reinterpret_cast<void (*)(void*, const ::DotNet::UnityEngine::Quaternion*, void**)>(functionPointers[1883]);
  ::DotNet::UnityEngine::Transform::Property_set_localScale = reinterpret_cast<void (*)(void*, const ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1884]);
  ::DotNet::UnityEngine::Transform::Property_set_name = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1885]);
  ::DotNet::UnityEngine::Transform::Property_set_parent = reinterpret_cast<void (*)(void*, void*, void**)>(functionPointers[1886]);
  ::DotNet::UnityEngine::Transform::Property_set_position = reinterpret_cast<void (*)(void*, const ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1887]);
  ::DotNet::UnityEngine::Transform::Property_set_rotation = reinterpret_cast<void (*)(void*, const ::DotNet::UnityEngine::Quaternion*, void**)>(functionPointers[1888]);
  ::DotNet::UnityEngine::Transform::Property_set_up = reinterpret_cast<void (*)(void*, const ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1889]);
  ::DotNet::UnityEngine::Vector2::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(::DotNet::UnityEngine::Vector2*, void**)>(functionPointers[1890]);
  ::DotNet::UnityEngine::Vector3::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1891]);
  ::DotNet::UnityEngine::Vector3::Construct_LB__scTJntm1swre2IwXuIw = reinterpret_cast<void (*)(float, float, float, ::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1892]);
  ::DotNet::UnityEngine::Vector3::Property_get_forward = reinterpret_cast<void (*)(::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1893]);
  ::DotNet::UnityEngine::Vector3::Property_get_up = reinterpret_cast<void (*)(::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1894]);
  ::DotNet::UnityEngine::Vector3::Property_get_zero = reinterpret_cast<void (*)(::DotNet::UnityEngine::Vector3*, void**)>(functionPointers[1895]);
  ::DotNet::UnityEngine::Vector4::Construct_1B2M2Y8AsgTpgAmY7PhCfg = reinterpret_cast<void (*)(::DotNet::UnityEngine::Vector4*, void**)>(functionPointers[1896]);
  ::DotNet::UnityEngine::Vector4::Construct_HRdOMAw1wcknBRlYiWJ61Q = reinterpret_cast<void (*)(float, float, float, float, ::DotNet::UnityEngine::Vector4*, void**)>(functionPointers[1897]);

  // Invoke user startup code.
  start();

  return 1;
}

}

