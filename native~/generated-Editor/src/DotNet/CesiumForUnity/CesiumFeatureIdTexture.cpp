#include <DotNet/CesiumForUnity/CesiumFeatureIdTexture.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumFeatureIdSet.h>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumFeatureIdTextureStatus.h>
#include <DotNet/System/String.h>
#include "CesiumFeatureIdTextureImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/UnityEngine/Vector2.h>
#include <DotNet/UnityEngine/RaycastHit.h>



namespace DotNet::CesiumForUnity {

CesiumFeatureIdTexture::CesiumFeatureIdTexture(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumFeatureIdTexture::CesiumFeatureIdTexture(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumFeatureIdTexture::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumFeatureIdTexture::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumFeatureIdTexture::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumFeatureIdTexture::GetHandle() {
    return this->_handle;
}


void* (*CesiumFeatureIdTexture::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


CesiumFeatureIdTexture::CesiumFeatureIdTexture()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


CesiumFeatureIdTexture::operator ::DotNet::CesiumForUnity::CesiumFeatureIdSet() const {
    return ::DotNet::CesiumForUnity::CesiumFeatureIdSet(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumFeatureIdTexture::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_get_status)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumFeatureIdTextureStatus CesiumFeatureIdTexture::status() const {
    void* reinteropException = nullptr;
    auto result = Property_get_status((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumFeatureIdTextureStatus(result);
}


void (*DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_set_status)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumFeatureIdTexture::status(::DotNet::CesiumForUnity::CesiumFeatureIdTextureStatus value) const {
    void* reinteropException = nullptr;
    Property_set_status((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_get_featureCount)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumFeatureIdTexture::featureCount() const {
    void* reinteropException = nullptr;
    auto result = Property_get_featureCount((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_set_featureCount)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumFeatureIdTexture::featureCount(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_featureCount((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_get_label)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumFeatureIdTexture::label() const {
    void* reinteropException = nullptr;
    auto result = Property_get_label((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_set_label)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumFeatureIdTexture::label(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_label((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_get_nullFeatureId)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumFeatureIdTexture::nullFeatureId() const {
    void* reinteropException = nullptr;
    auto result = Property_get_nullFeatureId((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_set_nullFeatureId)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumFeatureIdTexture::nullFeatureId(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_nullFeatureId((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_get_propertyTableIndex)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumFeatureIdTexture::propertyTableIndex() const {
    void* reinteropException = nullptr;
    auto result = Property_get_propertyTableIndex((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumFeatureIdTexture::Property_set_propertyTableIndex)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumFeatureIdTexture::propertyTableIndex(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_propertyTableIndex((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumFeatureIdTexture::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumFeatureIdTexture::Dispose() const {
    void* reinteropException = nullptr;
    CallDispose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*CesiumFeatureIdTexture::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumFeatureIdTextureImpl& CesiumFeatureIdTexture::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumFeatureIdTextureImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumFeatureIdTexture_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumFeatureIdTexture wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumFeatureIdTextureImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumFeatureIdTexture_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureIdTextureImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int64_t DotNet_CesiumForUnity_CesiumFeatureIdTexture_GetFeatureIdForUV(void* handle, void* pImpl, const ::DotNet::UnityEngine::Vector2* uv, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureIdTextureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeatureIdTexture wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFeatureIdForUV(wrapper, *uv);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int64_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int64_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int64_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int64_t DotNet_CesiumForUnity_CesiumFeatureIdTexture_GetFeatureIdForVertex(void* handle, void* pImpl, ::std::int64_t vertexIndex, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureIdTextureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeatureIdTexture wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFeatureIdForVertex(wrapper, vertexIndex);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int64_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int64_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int64_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int64_t DotNet_CesiumForUnity_CesiumFeatureIdTexture_GetFeatureIdFromRaycastHit(void* handle, void* pImpl, const ::DotNet::UnityEngine::RaycastHit* hitInfo, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureIdTextureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeatureIdTexture wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFeatureIdFromRaycastHit(wrapper, *hitInfo);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int64_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int64_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int64_t();
  }                   
}

} // extern "C"

