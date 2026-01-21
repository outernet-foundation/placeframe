#include <DotNet/CesiumForUnity/CesiumMetadata.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/MonoBehaviour.h>
#include <DotNet/UnityEngine/Behaviour.h>
#include <DotNet/UnityEngine/Component.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumFeature.h>
#include <DotNet/System/Array1.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/UnityEngine/Coroutine.h>
#include <DotNet/System/Collections/IEnumerator.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/System/String.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumMetadataImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>



namespace DotNet::CesiumForUnity {

CesiumMetadata::CesiumMetadata(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumMetadata::CesiumMetadata(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CesiumMetadata::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumMetadata::GetHandle() {
    return this->_handle;
}


CesiumMetadata::operator ::DotNet::UnityEngine::MonoBehaviour() const {
    return ::DotNet::UnityEngine::MonoBehaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumMetadata::operator ::DotNet::UnityEngine::Behaviour() const {
    return ::DotNet::UnityEngine::Behaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumMetadata::operator ::DotNet::UnityEngine::Component() const {
    return ::DotNet::UnityEngine::Component(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumMetadata::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumMetadata::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumMetadata::CallGetFeatures_5FygR9Vikuo7JxfnCBErUQ)(void* thiz, void* transform, ::std::int32_t triangleIndex, void** reinteropException) = nullptr;


::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeature> CesiumMetadata::GetFeatures(const ::DotNet::UnityEngine::Transform& transform, ::std::int32_t triangleIndex) const {
    void* reinteropException = nullptr;
    auto result = CallGetFeatures_5FygR9Vikuo7JxfnCBErUQ((*this).GetHandle().GetRaw(), transform.GetHandle().GetRaw(), triangleIndex, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeature>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumMetadata::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Coroutine CesiumMetadata::StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const {
    void* reinteropException = nullptr;
    auto result = CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw((*this).GetHandle().GetRaw(), routine.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Coroutine(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadata::Property_get_enabled)(void* thiz, void** reinteropException) = nullptr;


bool CesiumMetadata::enabled() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enabled((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumMetadata::Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumMetadata::enabled(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enabled((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumMetadata::Property_get_gameObject)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject CesiumMetadata::gameObject() const {
    void* reinteropException = nullptr;
    auto result = Property_get_gameObject((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumMetadata::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform CesiumMetadata::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumMetadata::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures CesiumMetadata::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumMetadata::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumMetadata::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumMetadata::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumMetadata::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumMetadata::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> CesiumMetadata::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::CesiumMetadata::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumMetadata::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadata::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumMetadata::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool CesiumMetadata::operator==(const CesiumMetadata& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumMetadata::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumMetadata::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadata::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumMetadata::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CesiumMetadata::operator!=(const CesiumMetadata& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumMetadata::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumMetadata::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumMetadata::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumMetadata::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*CesiumMetadata::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumMetadataImpl& CesiumMetadata::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumMetadataImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumMetadata_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumMetadata wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumMetadataImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadata_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumMetadataImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumMetadata_GetFeatures(void* handle, void* pImpl, void* transform, ::std::int32_t triangleIndex, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumMetadataImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumMetadata wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFeatures(wrapper, ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(transform)), triangleIndex);
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}

} // extern "C"

