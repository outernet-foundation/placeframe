#include <DotNet/UnityEngine/GameObject.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/CesiumForUnity/Cesium3DTileset.h>
#include <DotNet/CesiumForUnity/CesiumIonRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumRasterOverlay.h>
#include <DotNet/System/Array1.h>
#include <DotNet/UnityEngine/MeshFilter.h>
#include <DotNet/UnityEngine/MeshRenderer.h>
#include <DotNet/UnityEngine/MeshCollider.h>
#include <DotNet/CesiumForUnity/CesiumBingMapsRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumAzureMapsRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumGoogleMapTilesRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumTileMapServiceRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumWebMapServiceRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumWebMapTileServiceRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumUrlTemplateRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumMetadata.h>
#include <DotNet/CesiumForUnity/CesiumGeoreference.h>
#include <DotNet/CesiumForUnity/CesiumCreditSystem.h>
#include <DotNet/CesiumForUnity/CesiumGlobeAnchor.h>
#include <DotNet/CesiumForUnity/CesiumTileExcluder.h>
#include <DotNet/CesiumForUnity/CesiumPointCloudRenderer.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/CesiumForUnity/CesiumModelMetadata.h>
#include <DotNet/CesiumForUnity/CesiumCartographicPolygon.h>
#include <DotNet/CesiumForUnity/CesiumPolygonRasterOverlay.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>



namespace DotNet::UnityEngine {

GameObject::GameObject(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


GameObject::GameObject(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& GameObject::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& GameObject::GetHandle() {
    return this->_handle;
}


void* (*GameObject::Construct_wfPSjxsETIcebv8un8PGZw)(void* name, void** reinteropException) = nullptr;


GameObject::GameObject(const ::DotNet::System::String& name)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_wfPSjxsETIcebv8un8PGZw(name.GetHandle().GetRaw(), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


void* (*GameObject::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


GameObject::GameObject()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


GameObject::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


GameObject::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint8_t (*DotNet::UnityEngine::GameObject::Property_get_activeInHierarchy)(void* thiz, void** reinteropException) = nullptr;


bool GameObject::activeInHierarchy() const {
    void* reinteropException = nullptr;
    auto result = Property_get_activeInHierarchy((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::UnityEngine::GameObject::Property_get_layer)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t GameObject::layer() const {
    void* reinteropException = nullptr;
    auto result = Property_get_layer((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::GameObject::Property_set_layer)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void GameObject::layer(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_layer((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::GameObject::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform GameObject::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_0EgxpGTzCG1YTfWqwgLniw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::Cesium3DTileset GameObject::GetComponent<::DotNet::CesiumForUnity::Cesium3DTileset>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_0EgxpGTzCG1YTfWqwgLniw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::Cesium3DTileset(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_BAtcoWNWVoAVplmna6OgsQ)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumIonRasterOverlay GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_BAtcoWNWVoAVplmna6OgsQ((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_0EgxpGTzCG1YTfWqwgLniw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::Cesium3DTileset GameObject::AddComponent<::DotNet::CesiumForUnity::Cesium3DTileset>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_0EgxpGTzCG1YTfWqwgLniw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::Cesium3DTileset(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_BAtcoWNWVoAVplmna6OgsQ)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumIonRasterOverlay GameObject::AddComponent<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_BAtcoWNWVoAVplmna6OgsQ((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponents_H1UZCBm__Pf6NnqpE7xQ8NQ)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay> GameObject::GetComponents<::DotNet::CesiumForUnity::CesiumRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponents_H1UZCBm__Pf6NnqpE7xQ8NQ((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponents_BAtcoWNWVoAVplmna6OgsQ)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay> GameObject::GetComponents<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponents_BAtcoWNWVoAVplmna6OgsQ((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::GameObject::CallSetActive_5DHWh79LLGX72UsSrgy12Q)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void GameObject::SetActive(bool value) const {
    void* reinteropException = nullptr;
    CallSetActive_5DHWh79LLGX72UsSrgy12Q((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_NF_PuZoAY7qn_PtfB0gOuA)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::UnityEngine::MeshFilter GameObject::AddComponent<::DotNet::UnityEngine::MeshFilter>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_NF_PuZoAY7qn_PtfB0gOuA((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::MeshFilter(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_PYIqvoB6xIJFucZLpuXW4g)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::UnityEngine::MeshRenderer GameObject::AddComponent<::DotNet::UnityEngine::MeshRenderer>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_PYIqvoB6xIJFucZLpuXW4g((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::MeshRenderer(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_9Dl3F62kv4jRdRrSCaAhWg)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::UnityEngine::MeshCollider GameObject::AddComponent<::DotNet::UnityEngine::MeshCollider>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_9Dl3F62kv4jRdRrSCaAhWg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::MeshCollider(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_PYIqvoB6xIJFucZLpuXW4g)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::UnityEngine::MeshRenderer GameObject::GetComponent<::DotNet::UnityEngine::MeshRenderer>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_PYIqvoB6xIJFucZLpuXW4g((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::MeshRenderer(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_NF_PuZoAY7qn_PtfB0gOuA)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::UnityEngine::MeshFilter GameObject::GetComponent<::DotNet::UnityEngine::MeshFilter>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_NF_PuZoAY7qn_PtfB0gOuA((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::MeshFilter(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_H1UZCBm__Pf6NnqpE7xQ8NQ)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumRasterOverlay GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_H1UZCBm__Pf6NnqpE7xQ8NQ((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_xszYH1Pc7IFeB_VsZOpLAg)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_xszYH1Pc7IFeB_VsZOpLAg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumBingMapsRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_h3Dg1fHhPAsIOJVZ_EBQ0Q)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_h3Dg1fHhPAsIOJVZ_EBQ0Q((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumAzureMapsRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_D9Lae__zo_r27FE__dPPON_Q)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_D9Lae__zo_r27FE__dPPON_Q((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_zSXCS__EpLjNvbypxgiLwTw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_zSXCS__EpLjNvbypxgiLwTw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumTileMapServiceRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_ceANxxBRdEpPcfCIAtIDbw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_ceANxxBRdEpPcfCIAtIDbw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumWebMapServiceRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_xv03rkZpw_Znk_k8us1wKw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_xv03rkZpw_Znk_k8us1wKw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_6Whoj_6qM2__sUah3I8fbaA)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_6Whoj_6qM2__sUah3I8fbaA((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_cgILpkZPip9MNREZc7j5sA)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumMetadata GameObject::AddComponent<::DotNet::CesiumForUnity::CesiumMetadata>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_cgILpkZPip9MNREZc7j5sA((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumMetadata(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_cgILpkZPip9MNREZc7j5sA)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumMetadata GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumMetadata>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_cgILpkZPip9MNREZc7j5sA((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumMetadata(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponentInParent_cgILpkZPip9MNREZc7j5sA)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumMetadata GameObject::GetComponentInParent<::DotNet::CesiumForUnity::CesiumMetadata>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponentInParent_cgILpkZPip9MNREZc7j5sA((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumMetadata(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_bqVePTBqqV2QqVo4ESth7Q)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumGeoreference GameObject::AddComponent<::DotNet::CesiumForUnity::CesiumGeoreference>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_bqVePTBqqV2QqVo4ESth7Q((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumGeoreference(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_bqVePTBqqV2QqVo4ESth7Q)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumGeoreference GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumGeoreference>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_bqVePTBqqV2QqVo4ESth7Q((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumGeoreference(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponentInParent_bqVePTBqqV2QqVo4ESth7Q)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumGeoreference GameObject::GetComponentInParent<::DotNet::CesiumForUnity::CesiumGeoreference>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponentInParent_bqVePTBqqV2QqVo4ESth7Q((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumGeoreference(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallFindGameObjectsWithTag_X3GzO_w9lbBwSL5__E4yHEA)(void* tag, void** reinteropException) = nullptr;


::DotNet::System::Array1<::DotNet::UnityEngine::GameObject> GameObject::FindGameObjectsWithTag(const ::DotNet::System::String& tag) {
    void* reinteropException = nullptr;
    auto result = CallFindGameObjectsWithTag_X3GzO_w9lbBwSL5__E4yHEA(tag.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::UnityEngine::GameObject>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_jKezPd1C5klHWmgOl3TpSg)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumCreditSystem GameObject::AddComponent<::DotNet::CesiumForUnity::CesiumCreditSystem>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_jKezPd1C5klHWmgOl3TpSg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumCreditSystem(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_z_rdtaHehbYFGG7_o6BG8A)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumGlobeAnchor GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumGlobeAnchor>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_z_rdtaHehbYFGG7_o6BG8A((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumGlobeAnchor(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponentsInChildren_z_rdtaHehbYFGG7_o6BG8A)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor> GameObject::GetComponentsInChildren<::DotNet::CesiumForUnity::CesiumGlobeAnchor>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponentsInChildren_z_rdtaHehbYFGG7_o6BG8A((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponentsInChildren_STJODArO5i8B0kejx7otTA)(void* thiz, ::std::uint8_t includeInactive, void** reinteropException) = nullptr;


template <> ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor> GameObject::GetComponentsInChildren<::DotNet::CesiumForUnity::CesiumGlobeAnchor>(bool includeInactive) const {
    void* reinteropException = nullptr;
    auto result = CallGetComponentsInChildren_STJODArO5i8B0kejx7otTA((*this).GetHandle().GetRaw(), includeInactive ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponentsInChildren_0EgxpGTzCG1YTfWqwgLniw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::System::Array1<::DotNet::CesiumForUnity::Cesium3DTileset> GameObject::GetComponentsInChildren<::DotNet::CesiumForUnity::Cesium3DTileset>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponentsInChildren_0EgxpGTzCG1YTfWqwgLniw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::CesiumForUnity::Cesium3DTileset>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_z_rdtaHehbYFGG7_o6BG8A)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumGlobeAnchor GameObject::AddComponent<::DotNet::CesiumForUnity::CesiumGlobeAnchor>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_z_rdtaHehbYFGG7_o6BG8A((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumGlobeAnchor(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponentsInParent_5cYXJenC2831by5N6skAPw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumTileExcluder> GameObject::GetComponentsInParent<::DotNet::CesiumForUnity::CesiumTileExcluder>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponentsInParent_5cYXJenC2831by5N6skAPw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumTileExcluder>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_NuZsWWrRz5eMwjHbcVsVwA)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPointCloudRenderer GameObject::AddComponent<::DotNet::CesiumForUnity::CesiumPointCloudRenderer>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_NuZsWWrRz5eMwjHbcVsVwA((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPointCloudRenderer(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures GameObject::AddComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallAddComponent_kHO1FlHzBtTx__KiumABg0g)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumModelMetadata GameObject::AddComponent<::DotNet::CesiumForUnity::CesiumModelMetadata>() const {
    void* reinteropException = nullptr;
    auto result = CallAddComponent_kHO1FlHzBtTx__KiumABg0g((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumModelMetadata(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_kHO1FlHzBtTx__KiumABg0g)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumModelMetadata GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumModelMetadata>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_kHO1FlHzBtTx__KiumABg0g((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumModelMetadata(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_a430lQ0omIr32Y9qAs_Zdw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumCartographicPolygon GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumCartographicPolygon>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_a430lQ0omIr32Y9qAs_Zdw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumCartographicPolygon(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::CallGetComponent_Is4miIX63ogCDpU56JfOjw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay GameObject::GetComponent<::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_Is4miIX63ogCDpU56JfOjw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPolygonRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::GameObject::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String GameObject::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::GameObject::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void GameObject::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::GameObject::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> GameObject::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::UnityEngine::GameObject::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void GameObject::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEngine::GameObject::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool GameObject::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool GameObject::operator==(const GameObject& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool GameObject::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool GameObject::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEngine::GameObject::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool GameObject::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool GameObject::operator!=(const GameObject& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool GameObject::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool GameObject::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::UnityEngine::GameObject::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t GameObject::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


