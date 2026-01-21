#include <DotNet/CesiumForUnity/CesiumCreditSystem.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/MonoBehaviour.h>
#include <DotNet/UnityEngine/Behaviour.h>
#include <DotNet/UnityEngine/Component.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/CesiumForUnity/CesiumCredit.h>
#include <DotNet/System/Collections/Generic/List1.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Texture2D.h>
#include <DotNet/System/Collections/IEnumerator.h>
#include <DotNet/System/String.h>
#include <cstdint>
#include <DotNet/UnityEngine/Coroutine.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumCreditSystemImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>



namespace DotNet::CesiumForUnity {

CesiumCreditSystem::CesiumCreditSystem(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumCreditSystem::CesiumCreditSystem(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CesiumCreditSystem::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumCreditSystem::GetHandle() {
    return this->_handle;
}


CesiumCreditSystem::operator ::DotNet::UnityEngine::MonoBehaviour() const {
    return ::DotNet::UnityEngine::MonoBehaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumCreditSystem::operator ::DotNet::UnityEngine::Behaviour() const {
    return ::DotNet::UnityEngine::Behaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumCreditSystem::operator ::DotNet::UnityEngine::Component() const {
    return ::DotNet::UnityEngine::Component(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumCreditSystem::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumCreditSystem::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_onScreenCredits)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCredit> CesiumCreditSystem::onScreenCredits() const {
    void* reinteropException = nullptr;
    auto result = Property_get_onScreenCredits((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCredit>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_popupCredits)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCredit> CesiumCreditSystem::popupCredits() const {
    void* reinteropException = nullptr;
    auto result = Property_get_popupCredits((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCredit>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_images)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::List1<::DotNet::UnityEngine::Texture2D> CesiumCreditSystem::images() const {
    void* reinteropException = nullptr;
    auto result = Property_get_images((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::List1<::DotNet::UnityEngine::Texture2D>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumCreditSystem::CallGetDefaultCreditSystem_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumCreditSystem CesiumCreditSystem::GetDefaultCreditSystem() {
    void* reinteropException = nullptr;
    auto result = CallGetDefaultCreditSystem_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumCreditSystem(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumCreditSystem::CallLoadImage_i4__FgVIR5VYHO4KBzPBwNQ)(void* thiz, void* url, void** reinteropException) = nullptr;


::DotNet::System::Collections::IEnumerator CesiumCreditSystem::LoadImage(const ::DotNet::System::String& url) const {
    void* reinteropException = nullptr;
    auto result = CallLoadImage_i4__FgVIR5VYHO4KBzPBwNQ((*this).GetHandle().GetRaw(), url.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::IEnumerator(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumCreditSystem::CallGetNumberOfLoadingImages_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumCreditSystem::GetNumberOfLoadingImages() const {
    void* reinteropException = nullptr;
    auto result = CallGetNumberOfLoadingImages_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumCreditSystem::CallBroadcastCreditsUpdate_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumCreditSystem::BroadcastCreditsUpdate() const {
    void* reinteropException = nullptr;
    CallBroadcastCreditsUpdate_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumCreditSystem::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Coroutine CesiumCreditSystem::StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const {
    void* reinteropException = nullptr;
    auto result = CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw((*this).GetHandle().GetRaw(), routine.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Coroutine(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_enabled)(void* thiz, void** reinteropException) = nullptr;


bool CesiumCreditSystem::enabled() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enabled((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumCreditSystem::Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumCreditSystem::enabled(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enabled((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_gameObject)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject CesiumCreditSystem::gameObject() const {
    void* reinteropException = nullptr;
    auto result = Property_get_gameObject((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform CesiumCreditSystem::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumCreditSystem::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures CesiumCreditSystem::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumCreditSystem::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumCreditSystem::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumCreditSystem::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumCreditSystem::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> CesiumCreditSystem::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::CesiumCreditSystem::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumCreditSystem::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumCreditSystem::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumCreditSystem::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool CesiumCreditSystem::operator==(const CesiumCreditSystem& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumCreditSystem::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumCreditSystem::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumCreditSystem::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumCreditSystem::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CesiumCreditSystem::operator!=(const CesiumCreditSystem& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumCreditSystem::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumCreditSystem::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumCreditSystem::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumCreditSystem::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*CesiumCreditSystem::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumCreditSystemImpl& CesiumCreditSystem::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumCreditSystemImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumCreditSystem_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumCreditSystem wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumCreditSystemImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumCreditSystem_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumCreditSystemImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumCreditSystem_UpdateCredits(void* handle, void* pImpl, ::std::uint8_t forceUpdate, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumCreditSystemImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumCreditSystem wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->UpdateCredits(wrapper, !!forceUpdate);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}

} // extern "C"

